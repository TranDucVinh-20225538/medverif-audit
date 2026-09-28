#!/usr/bin/env python3
"""Random format-mismatch pairs for human precision check."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from general_quantity import explain_format_quantity_mismatch  # noqa: E402
from t8_aggrefact_analysis import load_split  # noqa: E402

OUT = ROOT / "qc/t8_mismatch_check.csv"
SEED = 2026
N = 40


def main() -> None:
    rows: list[dict] = []
    for split in ("dev", "test"):
        for i, row in enumerate(load_split(split)):
            claim = row.get("claim") or ""
            doc = row.get("doc") or ""
            ex = explain_format_quantity_mismatch(claim, doc)
            if not ex:
                continue
            rows.append(
                {
                    "row_id": f"{split}:{i}",
                    "dataset": row.get("dataset") or "",
                    "claim_span": ex["claim_span"],
                    "doc_span": ex["doc_span"],
                    "mismatch_label": ex["mismatch_label"],
                    "claim_excerpt": claim[:240].replace("\n", " "),
                    "doc_excerpt": doc[:240].replace("\n", " "),
                    "PI_ok": "",
                    "note": "",
                }
            )
    rng = random.Random(SEED)
    rng.shuffle(rows)
    picked = rows[:N]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(handle, fieldnames=list(picked[0].keys()) if picked else [])
        w.writeheader()
        w.writerows(picked)
    print(json.dumps({"n_candidates": len(rows), "n_written": len(picked), "path": str(OUT)}))


if __name__ == "__main__":
    main()
