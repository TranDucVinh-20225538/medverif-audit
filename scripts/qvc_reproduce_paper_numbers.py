#!/usr/bin/env python3
"""Regenerate paper_numbers.json from results/raw (stored scores)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import load_joined, rate_table  # noqa: E402

OUT = ROOT / "qvc/paper_numbers.json"


def main() -> None:
    inst = ROOT / "data/v3/instances_cpu_early.jsonl"
    raw = ROOT / "results/raw"
    joined = load_joined(inst, raw)
    table = rate_table(joined)
    pick = {}
    for row in table:
        if row["verifier"] in ("v2a_minicheck", "v3_alignscore", "v4_ragas_nli"):
            pick.setdefault(row["verifier"], {})[row["type"]] = row
    OUT.write_text(json.dumps({"rate_table_subset": pick, "n_joined": len(joined)}, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
