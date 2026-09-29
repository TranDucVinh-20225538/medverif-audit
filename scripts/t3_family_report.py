#!/usr/bin/env python3
"""T3 INV frequency/route (PI_ok=Y): pass rates per family and verifier."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _c0_pass_bases, _parsed  # noqa: E402
from t7_e1_unit_report import merged_scores  # noqa: E402

T3_PATHS = (
    ROOT / "data/v3/instances_inv_families.jsonl",
    ROOT / "data/t3/instances_inv_families.jsonl",
)
CPU = ROOT / "data/v3/instances_cpu_early.jsonl"
LABELS = ROOT / "qc/inv_claim_PI_ok_labels.csv"
OUT = ROOT / "results/tables/t3_family_pass.md"
OUT_JSON = ROOT / "notes/t3_family_pass.json"

VERIFIERS = (
    "v2a_minicheck",
    "v3_alignscore",
    "v1_medscore",
    "v4_ragas_nli",
    "v1b_medscore",
    "v5_ragas_nli",
    "v1c_medscore",
    "v6_ragas_gpt4o_mini",
    "v6_ragas_haiku45",
    "v6_ragas_llama31_8b",
    "v6_ragas_mistral_small32",
    "v6_ragas_nli",
    "v2b_bespoke",
    "t6_minicheck_deberta",
    "t6_minicheck_roberta",
    "t6_alignscore_base",
    "t6_summac_conv",
    "t6_summac_zs",
    "t6_hhem",
    "t6_granite_guardian",
)


def pi_ok_rows() -> tuple[dict[str, str], list[dict]]:
    fam: dict[str, str] = {}
    for row in csv.DictReader(LABELS.open()):
        if (row.get("PI_ok") or "").strip().upper() != "Y":
            continue
        if (row.get("family") or "").strip() not in ("inv_frequency", "inv_route"):
            continue
        fam[row["instance_id"].strip()] = row["family"].strip()
    by_id: dict[str, dict] = {}
    for path in T3_PATHS:
        if not path.is_file():
            continue
        for line in path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["instance_id"] not in fam:
                continue
            by_id.setdefault(row["instance_id"], row)
    inst = []
    for iid, family in sorted(fam.items()):
        row = by_id.get(iid)
        if not row or not row.get("valid", True):
            continue
        row = dict(row)
        row["family"] = family
        inst.append(row)
    return fam, inst


def main() -> None:
    label_ids, inst = pi_ok_rows()
    by_fam: dict[str, list[dict]] = defaultdict(list)
    for row in inst:
        by_fam[row["family"]].append(row)

    lines = [
        "# T3 encoder families (PI_ok=Y, valid)",
        "",
        f"- Label ids (freq/route): **{len(label_ids)}**; scored instances present: **{len(inst)}**",
        "- Scores: `merged_scores()` over results/raw*, t3, t7, e2_main, t6b, t2_full",
        "",
        "| Verifier | Family | PASS | n |",
        "|---|---|---:|---:|",
    ]
    payload: dict = {"pi_ok_label_ids": len(label_ids), "instances_scored": len(inst), "by_verifier": {}}

    bases = {r["base_id"] for r in inst}
    c0_rows = []
    for line in CPU.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("valid", True) and row.get("condition") == "C0" and row["base_id"] in bases:
            c0_rows.append(row)

    for v in VERIFIERS:
        sc = merged_scores(v)
        joined = []
        for row in c0_rows + inst:
            verdict = sc.get(row["instance_id"])
            if not verdict:
                continue
            j = dict(row)
            j["verifier"] = v
            j["verdict"] = verdict
            joined.append(j)
        c0_pass = _c0_pass_bases(joined)
        vdata: dict[str, dict] = {}
        for fam in ("inv_frequency", "inv_route"):
            parsed = [
                r
                for r in joined
                if r.get("family") == fam
                and r["base_id"] in c0_pass
                and _parsed(r)
            ]
            n = len(parsed)
            p = sum(r["verdict"] == "PASS" for r in parsed)
            vdata[fam] = {"pass": p, "n": n}
            lines.append(f"| {v} | {fam} | {p} | {n} |")
        payload["by_verifier"][v] = vdata

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
