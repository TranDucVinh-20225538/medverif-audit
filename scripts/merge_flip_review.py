#!/usr/bin/env python3
"""Merge flip PI_ok labels into qc/e1_pol_review.csv."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E1 = ROOT / "qc" / "e1_pol_review.csv"
LABELS = ROOT / "qc" / "flip_PI_ok_labels.csv"


def main() -> int:
    labels_path = Path(sys.argv[1]) if len(sys.argv) > 1 else LABELS
    labels = {r["base_id"]: r for r in csv.DictReader(labels_path.open(newline="", encoding="utf-8"))}
    rows = list(csv.DictReader(E1.open(newline="", encoding="utf-8")))
    labeled = [bid for bid, r in labels.items() if (r.get("PI_ok") or "").strip()]
    if len(labeled) != len(rows):
        print(f"row count mismatch: e1={len(rows)} labels={len(labeled)}", file=sys.stderr)
        return 1
    unmatched = set(labels) - {r["base_id"] for r in rows}
    if unmatched:
        print("unmatched base_ids:", unmatched, file=sys.stderr)
        return 1
    bad = [r for r in labels.values() if r["PI_ok"] not in ("Y", "N")]
    if bad:
        print("bad PI_ok", bad[:3], file=sys.stderr)
        return 1
    for row in rows:
        lab = labels[row["base_id"]]
        row["PI_ok"] = lab["PI_ok"]
        if lab.get("flip_mechanism") and row.get("flip_mechanism") != lab["flip_mechanism"]:
            print(f"flip_mechanism mismatch {row['base_id']}", file=sys.stderr)
            return 1
    with E1.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    from collections import Counter

    c = Counter(r["PI_ok"] for r in rows)
    print(json.dumps({"merged": len(rows), "Y": c["Y"], "N": c["N"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
