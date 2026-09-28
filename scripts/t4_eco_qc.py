#!/usr/bin/env python3
"""QC sample for T4 ecological answers (100 random, PI_ok empty)."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "data" / "t4" / "eco_classified.jsonl"
OUT = ROOT / "qc" / "eco_sample.csv"
SEED = 42
N = 100


def main() -> None:
    rows = [json.loads(line) for line in INP.open() if line.strip()]
    rng = random.Random(SEED)
    rng.shuffle(rows)
    sample = rows[: min(N, len(rows))]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "task_id",
                "base_id",
                "answerer_id",
                "openrouter_model",
                "eco_category",
                "answer",
                "evidence",
                "target_span_evidence",
                "PI_ok",
            ]
        )
        for row in sample:
            w.writerow(
                [
                    row.get("task_id"),
                    row.get("base_id"),
                    row.get("answerer_id"),
                    row.get("openrouter_model"),
                    row.get("eco_category"),
                    row.get("answer"),
                    row.get("evidence"),
                    row.get("target_span_evidence"),
                    "",
                ]
            )
    print(f"wrote {OUT} n={len(sample)}")


if __name__ == "__main__":
    main()
