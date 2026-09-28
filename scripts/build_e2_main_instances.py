#!/usr/bin/env python3
"""Main cohort E2 x2 instances (faithful-but-wrong magnitude)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "data/v3/instances_main.jsonl"
OUT = ROOT / "data/e2/instances_main_x2.jsonl"
MANIFEST = ROOT / "data/e2/manifest_main_x2.json"


def main() -> None:
    rows = []
    for line in MAIN.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if not row.get("valid", True):
            continue
        if row.get("condition") != "E2" or row.get("magnitude") != "x2":
            continue
        rows.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    MANIFEST.write_text(
        json.dumps(
            {
                "n": len(rows),
                "instances": str(OUT.relative_to(ROOT)),
                "filter": "main valid E2 magnitude=x2",
                "hpc_job": "jobs/run_e2_main_hpc.sh",
                "node30_job": "jobs/run_e2_main_node30.sh",
                "raw_hpc": "results/raw/e2_main",
                "raw_node30": "results/raw/e2_main",
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"n": len(rows), "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
