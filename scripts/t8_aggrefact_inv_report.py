#!/usr/bin/env python3
"""T8: rates on AggreFact unit sample — INV pass vs E1-unit fail + overall FAIL."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data/t8/instances_aggrefact_inv.jsonl"
RAW = ROOT / "results/raw/t8"
OUT = ROOT / "notes/t8_aggrefact_inv_report.json"

VERIFIERS = ["v1b_medscore", "v2a_minicheck", "v3_alignscore"] + [
    c["id"]
    for c in json.loads((ROOT / "notes/t6a_eco_checkers.json").read_text()).get("checkers", [])
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    if not INST.is_file():
        raise SystemExit(f"missing {INST} — run t8_build_aggrefact_inv_sample.py")
    rows = read_jsonl(INST)
    inv_ids = [r["instance_id"] for r in rows if r.get("condition") == "T8-aggrefact-inv"]
    e1_ids = [r["instance_id"] for r in rows if r.get("condition") == "T8-aggrefact-e1-unit"]
    report = {
        "n_instances": len(rows),
        "n_inv": len(inv_ids),
        "n_e1_unit": len(e1_ids),
        "verifiers": {},
    }
    for v in VERIFIERS:
        path = RAW / f"{v}.jsonl"
        scores = {}
        if path.is_file():
            for row in read_jsonl(path):
                if row.get("instance_id"):
                    scores[row["instance_id"]] = row.get("verdict")
        inv_scored = [scores[i] for i in inv_ids if scores.get(i)]
        e1_scored = [scores[i] for i in e1_ids if scores.get(i)]
        all_scored = inv_scored + e1_scored
        fails = sum(1 for x in all_scored if x == "FAIL")
        report["verifiers"][v] = {
            "n_scored": len(all_scored),
            "fail_rate": fails / len(all_scored) if all_scored else None,
            "inv_pass_rate": sum(1 for x in inv_scored if x == "PASS") / len(inv_scored) if inv_scored else None,
            "e1_unit_fail_rate": sum(1 for x in e1_scored if x == "FAIL") / len(e1_scored) if e1_scored else None,
            "n_inv_scored": len(inv_scored),
            "n_e1_scored": len(e1_scored),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
