#!/usr/bin/env python3
"""POLARITY flip PI_ok=Y (26): E1-claim/E2 pass @0.5 for all scored verifiers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _c0_pass_bases, _parsed  # noqa: E402
from review_filters import flip_pi_ok_bases  # noqa: E402
from t7_e1_unit_report import merged_scores, read_jsonl  # noqa: E402

CPU = ROOT / "data/v3/instances_cpu_early.jsonl"
OUT = ROOT / "results/tables/polarity_all_verifiers.md"
OUT_JSON = ROOT / "notes/polarity_all_verifiers.json"

SCORE_SLUGS = [
    "v1_medscore",
    "v4_ragas_nli",
    "v2a_minicheck",
    "v3_alignscore",
    "v1b_medscore",
    "v5_ragas_nli",
    "v1c_medscore",
    "v6_ragas_gpt4o_mini",
    "v6_ragas_haiku45",
    "v6_ragas_llama31_8b",
    "v6_ragas_mistral_small32",
    "v2b_bespoke",
    "t6_minicheck_deberta",
    "t6_minicheck_roberta",
    "t6_alignscore_base",
    "t6_summac_conv",
    "t6_summac_zs",
    "t6_hhem",
    "t6_granite_guardian",
]


def pol_instances(flip_y: set[str]) -> list[dict]:
    rows = []
    for line in CPU.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if not row.get("valid", True) or row.get("type") != "POLARITY":
            continue
        if row["base_id"] not in flip_y:
            continue
        if row.get("condition") not in ("E1-claim", "E2"):
            continue
        rows.append(row)
    return rows


def rate_e1(rows: list[dict], sc: dict[str, str], flip_y: set[str], c0_pass: set[str]) -> tuple[int, int]:
    parsed = []
    for row in rows:
        if row["condition"] != "E1-claim" or row["base_id"] not in flip_y:
            continue
        if row["base_id"] not in c0_pass:
            continue
        v = sc.get(row["instance_id"])
        if not v or v == "PARSE_FAIL":
            continue
        parsed.append(v == "PASS")
    if not parsed:
        return 0, 0
    return sum(parsed), len(parsed)


def main() -> None:
    flip_y = flip_pi_ok_bases()
    inst = pol_instances(flip_y)
    lines = [
        "# POLARITY — human flip_ok Y (all verifiers)",
        "",
        f"- Bases: **{len(flip_y)}** (`qc/e1_pol_review.csv` PI_ok=Y)",
        f"- E1-claim + E2 instances in pack: **{len(inst)}**",
        "- E1-claim PASS counts conditional on verifier C0 PASS (same base set)",
        "",
        "| Verifier | E1-claim PASS | n | E2 PASS | n |",
        "|---|---:|---:|---:|---:|",
    ]
    payload: dict = {"flip_ok_bases": len(flip_y), "verifiers": {}}

    for slug in SCORE_SLUGS:
        sc = merged_scores(slug)
        joined = []
        for row in inst:
            v = sc.get(row["instance_id"])
            if not v:
                continue
            j = dict(row)
            j["verifier"] = slug
            j["verdict"] = v
            joined.append(j)
        c0_pass = _c0_pass_bases(joined)
        e1_p, e1_n = rate_e1(inst, sc, flip_y, c0_pass)
        e2_rows = [
            r
            for r in inst
            if r["condition"] == "E2"
            and r["base_id"] in c0_pass
            and _parsed({"verdict": sc.get(r["instance_id"])})
            and sc.get(r["instance_id"]) not in (None, "PARSE_FAIL")
        ]
        e2_p = sum(sc[r["instance_id"]] == "PASS" for r in e2_rows)
        e2_n = len(e2_rows)
        lines.append(f"| {slug} | {e1_p} | {e1_n} | {e2_p} | {e2_n} |")
        payload["verifiers"][slug] = {
            "e1_claim_pass": e1_p,
            "e1_claim_n": e1_n,
            "e2_pass": e2_p,
            "e2_n": e2_n,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
