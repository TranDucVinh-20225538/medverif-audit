#!/usr/bin/env python3
"""Cohen's kappa on qc/iaa_sample.csv (reviewer_a vs reviewer_b)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "qc/iaa_sample.csv"
OUT = ROOT / "notes/iaa_kappa.json"


def kappa(a: list[str], b: list[str]) -> float | None:
    pairs = [(x, y) for x, y in zip(a, b) if x in ("PASS", "FAIL") and y in ("PASS", "FAIL")]
    if len(pairs) < 2:
        return None
    n = len(pairs)
    agree = sum(int(x == y) for x, y in pairs) / n
    pa = sum(1 for x, _ in pairs if x == "PASS") / n
    pb = sum(1 for _, y in pairs if y == "PASS") / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1:
        return 1.0
    return (agree - pe) / (1 - pe)


def main() -> None:
    ra, rb = [], []
    with CSV.open() as handle:
        for row in csv.DictReader(handle):
            ra.append((row.get("reviewer_a") or "").strip().upper())
            rb.append((row.get("reviewer_b") or "").strip().upper())
    filled = sum(1 for x, y in zip(ra, rb) if x in ("PASS", "FAIL") and y in ("PASS", "FAIL"))
    stat = {
        "n_rows": len(ra),
        "n_both_filled": filled,
        "kappa": kappa(ra, rb),
    }
    OUT.write_text(json.dumps(stat, indent=2) + "\n")
    print(json.dumps(stat, indent=2))


if __name__ == "__main__":
    main()
