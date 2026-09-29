#!/usr/bin/env python3
"""Side-by-side QI for Llama-3.3-70B (V4 API) — used by notes/reconcile_llama70b_qi.md."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _parsed, bootstrap_rate, read_jsonl  # noqa: E402
from review_filters import analysis_keep_row, effective_unit_natural_y  # noqa: E402
import t14_t3_filter_report as filt  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

LLAMA_MAIN = ROOT / "results/raw/v4_ragas_nli.llama.jsonl"
LLAMA_T14 = ROOT / "results/raw/t14/v4_ragas_nli.jsonl"
V4_DEFAULT = ROOT / "results/raw/v4_ragas_nli.jsonl"


def load_scores(*paths: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in paths:
        if not path.is_file():
            continue
        for line in path.open():
            row = json.loads(line)
            out[row["instance_id"]] = row
    return out


def c0_pass_bases(instances: list[dict], scores: dict[str, dict]) -> set[str]:
    return {
        r["base_id"]
        for r in instances
        if r.get("condition") == "C0" and scores.get(r["instance_id"], {}).get("verdict") == "PASS"
    }


def qi_micro(
    instances: list[dict],
    scores: dict[str, dict],
    *,
    natural_only: bool,
    unit_only: bool,
) -> dict:
    c0 = c0_pass_bases(instances, scores)
    hits: list[int] = []
    for r in instances:
        if r.get("condition") != "INV-claim":
            continue
        if unit_only and r.get("magnitude") != "unit_conversion":
            continue
        if r["base_id"] not in c0:
            continue
        if natural_only:
            orig = filt.inv_span_before(r)
            if not effective_unit_natural_y(
                r["base_id"], bool(rule_natural_unit_conversion_label(orig))
            ):
                continue
        sc = scores.get(r["instance_id"])
        if not sc or sc.get("verdict") not in ("PASS", "FAIL"):
            continue
        hits.append(int(sc["verdict"] == "PASS"))
    rate = sum(hits) / len(hits) if hits else None
    return {"rate": rate, "n": len(hits), "n_c0_bases": len(c0)}


def qi_m1_bootstrap(instances: list[dict], scores: dict[str, dict]) -> dict:
    joined = []
    for r in instances:
        sc = scores.get(r["instance_id"])
        if not sc or sc.get("verdict") not in ("PASS", "FAIL", "PARSE_FAIL"):
            continue
        joined.append({**r, "verdict": sc["verdict"]})
    c0 = {r["base_id"] for r in joined if r.get("condition") == "C0" and r["verdict"] == "PASS"}
    by_base: dict[str, list[dict]] = defaultdict(list)
    for r in joined:
        if r["base_id"] not in c0 or r.get("condition") != "INV-claim":
            continue
        if not _parsed(r):
            continue
        by_base[r["base_id"]].append(r)
    st = bootstrap_rate(
        [(sum(1 for r in g if r["verdict"] == "PASS"), len(g)) for g in by_base.values()]
    )
    return st


def main() -> None:
    llama = load_scores(LLAMA_MAIN, LLAMA_T14)
    qwen_v4 = load_scores(V4_DEFAULT)

    m1_inst = [
        r
        for r in read_jsonl(ROOT / "data/v3/instances_cpu_early.jsonl")
        if r.get("valid", True) and analysis_keep_row(r) and r.get("type") == "DOSE"
    ]
    main_inst = [
        r
        for r in read_jsonl(ROOT / "data/v3/instances_main.jsonl")
        if r.get("valid") and r.get("type") == "DOSE" and r.get("subset") == "main"
    ]
    t19 = read_jsonl(ROOT / "data/t19/instances_t19.jsonl")
    t19_main = [r for r in t19 if r.get("t19_pack") == "main_dose"]

    payload = {
        "llama70_sources": [str(LLAMA_MAIN.relative_to(ROOT)), str(LLAMA_T14.relative_to(ROOT))],
        "computations": {
            "m1_table_v4_raw_INV_all_magnitudes": {
                "description": "Same as m1_before_after.py slice_table INV (all INV-claim, |C0, parsed)",
                "instances": str((ROOT / "data/v3/instances_cpu_early.jsonl").relative_to(ROOT)),
                "scores": "results/raw/v4_ragas_nli.jsonl (Qwen V4 local, NOT Llama-70B)",
                "subset": "all INV-claim magnitudes",
                "conditioning": "C0 PASS (verifier-specific)",
                "exclusions": "analysis_keep_row (PI flip / INV manual gates)",
                "result": qi_m1_bootstrap(m1_inst, qwen_v4),
            },
            "m1_cohort_llama70_INV_all_magnitudes": {
                "instances": "data/v3/instances_cpu_early.jsonl (DOSE, analysis_keep)",
                "scores": "v4_ragas_nli.llama.jsonl (meta-llama/llama-3.3-70b-instruct API)",
                "subset": "all INV-claim magnitudes",
                "conditioning": "C0 PASS (Llama scores)",
                "exclusions": "analysis_keep_row",
                "result": qi_micro(m1_inst, llama, natural_only=False, unit_only=False),
            },
            "m1_cohort_llama70_INV_unit_natural": {
                "instances": "data/v3/instances_cpu_early.jsonl",
                "scores": "v4_ragas_nli.llama.jsonl",
                "subset": "natural INV-unit only (human+rule unit_naturalness)",
                "conditioning": "C0 PASS (Llama scores)",
                "exclusions": "analysis_keep_row",
                "result": qi_micro(m1_inst, llama, natural_only=True, unit_only=True),
            },
            "main_dose_llama70_INV_unit_natural": {
                "instances": "data/v3/instances_main.jsonl (main DOSE)",
                "scores": "v4_ragas_nli.llama.jsonl",
                "subset": "natural INV-unit",
                "conditioning": "C0 PASS",
                "exclusions": "non-dose not removed in this slice (main file post-audit)",
                "result": qi_micro(main_inst, llama, natural_only=True, unit_only=True),
            },
            "t19_llama70_INV_unit_natural": {
                "instances": "data/t19/instances_t19.jsonl (main_dose pack only)",
                "scores": "llama.jsonl + t14/v4 (overlap only for T19 rows)",
                "subset": "natural INV-unit",
                "conditioning": "C0 PASS (Llama scores on T19 rows)",
                "exclusions": "non_dose_targets applied in T19 pack",
                "result": qi_micro(t19_main, llama, natural_only=True, unit_only=True),
            },
            "m1_bootstrap_llama70_INV_all_parsed": {
                "description": "Cluster bootstrap by base_id like m1_before_after",
                "instances": "instances_cpu_early DOSE",
                "scores": "v4_ragas_nli.llama.jsonl",
                "subset": "all INV-claim (parsed only)",
                "conditioning": "C0 PASS",
                "exclusions": "analysis_keep_row",
                "result": qi_m1_bootstrap(m1_inst, llama),
            },
        },
    }
    out = ROOT / "notes/reconcile_llama70b_qi.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
