#!/usr/bin/env python3
"""T8: FAIL rates on AggreFact INV-unit sample (generalization check)."""

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
    ids = [r["instance_id"] for r in read_jsonl(INST)]
    report = {"n_instances": len(ids), "verifiers": {}}
    for v in VERIFIERS:
        path = RAW / f"{v}.jsonl"
        scores = {}
        if path.is_file():
            for row in read_jsonl(path):
                if row.get("instance_id"):
                    scores[row["instance_id"]] = row.get("verdict")
        scored = [scores[i] for i in ids if scores.get(i)]
        fails = sum(1 for x in scored if x == "FAIL")
        report["verifiers"][v] = {
            "n_scored": len(scored),
            "fail_rate": fails / len(scored) if scored else None,
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
