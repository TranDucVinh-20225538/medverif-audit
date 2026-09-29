#!/usr/bin/env python3
"""Summarize main_ext drop funnel from stage1 + post-stage1 filters."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import author_whitelist_unit_conversion  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402

STAGE1 = ROOT / "data/main_ext/stage1"
CAND = ROOT / "data/main_ext/candidates_selected.jsonl"
OUT_JSON = ROOT / "notes/main_ext_funnel.json"
OUT_MD = ROOT / "notes/main_ext_funnel.md"


def count_drops() -> Counter:
    c: Counter = Counter()
    p = STAGE1 / "drops.jsonl"
    if p.is_file():
        for row in read_jsonl(p):
            c[row.get("reason") or "unknown"] += 1
    return c


def stage1_funnel() -> dict:
    n_cand = sum(1 for _ in read_jsonl(CAND)) if CAND.is_file() else 0
    drops = count_drops()
    gen_fail = sum(v for k, v in drops.items() if k.startswith("generator") or k in (
        "span_missing_in_claim",
        "span_not_unique_in_claim",
        "generator_empty",
        "generator_truncated",
    ))
    phi4_claim = drops.get("validator_no", 0) + drops.get("validator_unparseable", 0)
    perturb = sum(v for k, v in drops.items() if k.startswith("perturb_"))
    inv = sum(v for k, v in drops.items() if k.startswith("inv_"))
    bases = list(read_jsonl(STAGE1 / "base_pairs.jsonl")) if (STAGE1 / "base_pairs.jsonl").is_file() else []
    unique_bases = {b["id"] for b in bases}
    finished_drop = sum(drops.values())
    return {
        "textbook_candidates_sent_to_stage1": n_cand,
        "stage1_drop_claim_generation_rules": dict(
            (k, drops[k])
            for k in drops
            if k
            in (
                "span_missing_in_claim",
                "span_not_unique_in_claim",
                "generator_empty",
                "generator_truncated",
            )
        ),
        "stage1_drop_phi4_claim_validation": phi4_claim,
        "stage1_drop_perturb_rules": perturb,
        "stage1_drop_phi4_inv_validation": inv,
        "stage1_drops_all": dict(drops),
        "stage1_bases_unique": len(unique_bases),
        "stage1_candidates_accounted_approx": finished_drop + len(unique_bases),
    }


def post_stage1_funnel(bases: list[dict], instances: list[dict]) -> dict:
    wl: set[str] = set()
    base_by = {b["id"]: b for b in bases}
    inv_rows = [r for r in instances if r.get("condition") == "INV-claim" and r.get("magnitude") == "unit_conversion"]
    for row in inv_rows:
        bid = row["base_id"]
        b = base_by.get(bid)
        if not b:
            continue
        if author_whitelist_unit_conversion(b["target_span_claim"], b.get("claim") or ""):
            wl.add(bid)
    return {
        "post_perturb_instances": len(instances),
        "bases_with_whitelist_inv_unit": len(wl),
        "bases_without_whitelist_inv": len(bases) - len(wl),
        "whitelist_inv_rate_on_stage1_bases": (len(wl) / len(bases)) if bases else None,
    }


def main() -> None:
    bases = list(read_jsonl(STAGE1 / "base_pairs.jsonl")) if (STAGE1 / "base_pairs.jsonl").is_file() else []
    if not bases:
        payload = {"error": "no stage1 base_pairs", "stage1": stage1_funnel()}
        OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
        print(json.dumps(payload, indent=2))
        return

    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tmp:
        for b in bases:
            tmp.write(json.dumps(b, ensure_ascii=False) + "\n")
        base_path = Path(tmp.name)
    inst_path = ROOT / "data/main_ext/_funnel_instances.jsonl"
    fail_path = ROOT / "notes/_funnel_perturb_failures.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/perturb.py"),
            "--base",
            str(base_path),
            "--out",
            str(inst_path),
            "--failures",
            str(fail_path),
            "--unit-inv-policy",
            "author_whitelist",
        ],
        check=True,
        cwd=str(ROOT),
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    instances = list(read_jsonl(inst_path))

    disjoint_ok = True
    disjoint_note = ""
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/main_ext_disjointness.py"), "--bases", str(base_path)],
            check=True,
            cwd=str(ROOT),
        )
    except subprocess.CalledProcessError:
        disjoint_ok = False
        disjoint_note = "see data/main_ext/disjointness_check.json"

    kept_path = ROOT / "data/main_ext/bases_main_ext.jsonl"
    kept_n = sum(1 for _ in read_jsonl(kept_path)) if kept_path.is_file() else 0

    payload = {
        "summary": {
            "candidates_stage1": stage1_funnel()["textbook_candidates_sent_to_stage1"],
            "stage1_bases": len(bases),
            "whitelist_inv_bases": post_stage1_funnel(bases, instances)["bases_with_whitelist_inv_unit"],
            "bases_written_main_ext": kept_n,
        },
        "funnel": {
            **stage1_funnel(),
            **post_stage1_funnel(bases, instances),
            "disjointness_pass_on_all_stage1_bases": disjoint_ok,
            "disjointness_note": disjoint_note,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    s = payload["summary"]
    f = payload["funnel"]
    md = [
        "# main_ext funnel",
        "",
        f"- Textbook candidates → stage1: **{s['candidates_stage1']}**",
        f"- Stage1 unique bases (Qwen claim + Phi-4 YES + perturb + Phi-4 INV): **{s['stage1_bases']}**",
        "  - Claim/rule drops: "
        + ", ".join(f"{k}={v}" for k, v in f.get("stage1_drop_claim_generation_rules", {}).items())
        or "0",
        f"  - Phi-4 claim validation drops: **{f.get('stage1_drop_phi4_claim_validation', 0)}**",
        f"  - Perturb rule drops: **{f.get('stage1_drop_perturb_rules', 0)}**",
        f"  - Phi-4 INV drops: **{f.get('stage1_drop_phi4_inv_validation', 0)}**",
        f"- Post-perturb **author_whitelist INV** bases: **{s['whitelist_inv_bases']}** "
        f"({f.get('whitelist_inv_rate_on_stage1_bases', 0):.1%} of stage1 bases)",
        f"- **bases_kept** in `data/main_ext/bases_main_ext.jsonl`: **{s['bases_written_main_ext']}**",
        f"- Disjointness (stage1 bases vs main+T15): **{'pass' if f.get('disjointness_pass_on_all_stage1_bases') else 'FAIL'}**",
        "",
        "Full counts: `notes/main_ext_funnel.json`",
    ]
    OUT_MD.write_text("\n".join(md) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
