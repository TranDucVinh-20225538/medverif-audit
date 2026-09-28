#!/usr/bin/env python3
"""Precision of format-mismatch detector from qc/t8_mismatch_check.csv (PI_ok Y/N)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "qc/t8_mismatch_check.csv"
OUT = ROOT / "notes/t8_mismatch_qc_precision.json"
APPROVE = ROOT / "notes/t8_mismatch_qc_approved"
THRESHOLD = 0.80


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--qc", type=Path, default=QC)
    p.add_argument("--threshold", type=float, default=THRESHOLD)
    p.add_argument("--approve-if-precision", action="store_true")
    args = p.parse_args()
    rows = list(csv.DictReader(args.qc.open(encoding="utf-8")))
    labeled = []
    for row in rows:
        ok = (row.get("PI_ok") or "").strip().upper()
        if ok in ("Y", "N"):
            labeled.append((ok == "Y", row))
    if not labeled:
        report = {
            "n_qc_rows": len(rows),
            "n_labeled": 0,
            "precision": None,
            "threshold": args.threshold,
            "ready": False,
            "message": "Label PI_ok as Y/N on qc/t8_mismatch_check.csv (40 rows).",
        }
        OUT.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        raise SystemExit(2)

    tp = sum(1 for y, _ in labeled if y)
    n = len(labeled)
    prec = tp / n
    report = {
        "n_qc_rows": len(rows),
        "n_labeled": n,
        "n_true_mismatch": tp,
        "n_false_alarm": n - tp,
        "precision": prec,
        "threshold": args.threshold,
        "passes_threshold": prec >= args.threshold,
        "ready": True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    if args.approve_if_precision and report["passes_threshold"]:
        APPROVE.write_text(
            f"approved precision={prec:.3f} n={n} threshold={args.threshold}\n"
        )
        report["approved_file"] = str(APPROVE)
    elif APPROVE.is_file() and not report["passes_threshold"]:
        APPROVE.unlink(missing_ok=True)
    print(json.dumps(report, indent=2))
    if not report["passes_threshold"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
