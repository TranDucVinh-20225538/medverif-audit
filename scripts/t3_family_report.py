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

from analyze import _c0_pass_bases, _parsed  # noqa: E402

T3 = ROOT / "data/v3/instances_inv_families.jsonl"
LABELS = ROOT / "qc/inv_claim_PI_ok_labels.csv"
SCORE_DIRS = [
    ROOT / "results/raw/t3",
    ROOT / "results/raw",
    ROOT / "results/raw_m1plus",
]
OUT = ROOT / "results/tables/t3_family_pass.md"
OUT_JSON = ROOT / "notes/t3_family_pass.json"

VERIFIERS = (
    "v2a_minicheck",
    "v3_alignscore",
    "v1_medscore",
    "v4_ragas_nli",
    "v1b_medscore",
    "v5_ragas_nli",
)


def pi_ok_rows() -> tuple[dict[str, str], list[dict]]:
    fam: dict[str, str] = {}
    for row in csv.DictReader(LABELS.open()):
        if (row.get("PI_ok") or "").strip().upper() != "Y":
            continue
        if (row.get("family") or "").strip() not in ("inv_frequency", "inv_route"):
            continue
        fam[row["instance_id"].strip()] = row["family"].strip()
    inst = []
    for line in T3.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["instance_id"] not in fam or not row.get("valid", True):
            continue
        row = dict(row)
        row["family"] = fam[row["instance_id"]]
        inst.append(row)
    return fam, inst


def load_scores(slug: str) -> dict[str, str]:
    m: dict[str, str] = {}
    for d in SCORE_DIRS:
        path = d / f"{slug}.jsonl"
        if not path.is_file():
            continue
        for line in path.open():
            if line.strip():
                rec = json.loads(line)
                m[rec["instance_id"]] = rec.get("verdict") or ""
    return m


def main() -> None:
    _, inst = pi_ok_rows()
    by_fam: dict[str, list[dict]] = defaultdict(list)
    for row in inst:
        by_fam[row["family"]].append(row)

    lines = [
        "# T3 encoder families (PI_ok=Y, valid)",
        "",
        f"- Instances: **{len(inst)}** (inv_frequency + inv_route)",
        "- Scores merged: `results/raw/t3`, `results/raw`, `results/raw_m1plus`",
        "",
        "| Verifier | Family | PASS | n |",
        "|---|---|---:|---:|",
    ]
    payload: dict = {"by_verifier": {}}

    for v in VERIFIERS:
        sc = load_scores(v)
        joined = []
        for row in inst:
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
