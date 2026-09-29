#!/usr/bin/env python3
"""Merge dose2 PI labels, apply expand-DOSE exclusion, log failures, comma audit."""

from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTACH = Path(
    "/data2/cmdir/home/toandq/.cursor/projects/data2-hpcshared-Vinh/attachments/"
    "c8490c3c-8029-48bf-90f8-080969f892d1/dose2_PI_ok_labels.csv"
)
DOSE2 = ROOT / "qc/dose2_PI_ok_labels.csv"
EXPAND_SAMPLE = ROOT / "qc/expand_dose_sample.csv"


def merge_labels() -> None:
    src = ATTACH if ATTACH.is_file() else DOSE2
    if not src.is_file():
        raise SystemExit("dose2_PI_ok_labels.csv not found")
    shutil.copy2(src, DOSE2)
    pi = {}
    with DOSE2.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            ok = (row.get("PI_ok") or "").strip()
            if ok in {"Y", "N"}:
                pi[row["base_id"]] = ok
    if not EXPAND_SAMPLE.is_file():
        return
    rows = list(csv.DictReader(EXPAND_SAMPLE.open(encoding="utf-8")))
    fields = list(rows[0].keys()) if rows else []
    if "PI_ok" not in fields:
        fields.append("PI_ok")
    for row in rows:
        bid = row["base_id"]
        if bid in pi:
            row["PI_ok"] = pi[bid]
    with EXPAND_SAMPLE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    merge_labels()
    py = sys.executable
    for script in (
        "log_dose2_failure_types.py",
        "apply_expand_dose_exclusion.py",
        "audit_comma_dose_perturbation.py",
        "build_main_dose_audit_sample.py",
        "build_score_pending.py",
    ):
        subprocess.run([py, str(ROOT / "scripts" / script)], check=True, cwd=str(ROOT))
    print("dose2 spot-check gate applied")


if __name__ == "__main__":
    main()
