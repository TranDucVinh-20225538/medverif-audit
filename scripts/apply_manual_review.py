#!/usr/bin/env python3
"""Merge PI_ok labels and validate manual review CSVs."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "qc" / "inv_manual_review.csv"
LABELS = ROOT / "qc" / "inv_manual_review_PI_ok_labels.csv"
UNIT = ROOT / "qc" / "unit_naturalness.csv"


def key(row: dict) -> tuple[str, str, str]:
    return (row["base_id"], row["type"], row.get("mechanism") or "")


def main() -> int:
    labels_path = Path(sys.argv[1]) if len(sys.argv) > 1 else LABELS
    if not labels_path.exists():
        print(f"missing labels: {labels_path}", file=sys.stderr)
        return 1
    labels = list(csv.DictReader(labels_path.open(newline="", encoding="utf-8")))
    labeled = [r for r in labels if (r.get("PI_ok") or "").strip()]
    inv = list(csv.DictReader(INV.open(newline="", encoding="utf-8")))
    inv_keys = {key(r) for r in inv}
    label_keys = {key(r) for r in labeled}
    unmatched = label_keys - inv_keys
    unlabeled_in_inv = [
        r for r in inv if (r.get("PI_ok") or "").strip() == "" and key(r) in label_keys
    ]
    if unmatched:
        print("UNMATCHED label keys:", sorted(unmatched), file=sys.stderr)
        return 1
    if len(labeled) != 95:
        print(f"expected 95 labeled rows, got {len(labeled)}", file=sys.stderr)
        return 1
    bad = [r for r in labeled if r["PI_ok"] not in ("Y", "N")]
    if bad:
        print("invalid PI_ok values:", bad[:5], file=sys.stderr)
        return 1
    by_label = {key(r): r["PI_ok"].strip() for r in labeled}
    for row in inv:
        k = key(row)
        if k in by_label:
            row["PI_ok"] = by_label[k]
    with INV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=inv[0].keys())
        writer.writeheader()
        writer.writerows(inv)
    unit = list(csv.DictReader(UNIT.open(newline="", encoding="utf-8")))
    bad_nat = [r for r in unit if (r.get("natural") or "").strip() not in ("Y", "N")]
    if bad_nat:
        print("unit_naturalness missing/invalid natural:", bad_nat[:3], file=sys.stderr)
        return 1
    counts_pi = Counter()
    for r in labeled:
        counts_pi[(r["type"], r.get("mechanism") or "", r["PI_ok"])] += 1
    counts_nat = Counter(r["natural"] for r in unit)
    y_pi = {k: v for k, v in counts_pi.items() if k[2] == "Y"}
    pi_counts = {f"{t}|{m}|{ok}": n for (t, m, ok), n in counts_pi.items()}
    pi_y = {
        f"{t}/{m}": sum(
            n for (tt, mm, ok), n in counts_pi.items() if ok == "Y" and tt == t and mm == m
        )
        for t in ("POLARITY", "DOSE")
        for m in ("template", "llm")
    }
    print(
        json.dumps(
            {
                "labeled_rows": len(labeled),
                "unmatched_keys": 0,
                "PI_ok_counts": pi_counts,
                "PI_ok_Y_by_type_mechanism": pi_y,
                "unit_naturalness": dict(counts_nat),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
