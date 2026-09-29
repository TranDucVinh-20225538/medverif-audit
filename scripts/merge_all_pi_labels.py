#!/usr/bin/env python3
"""Merge PI review CSVs from qc/*_PI_ok_labels.csv into working QC tables."""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "qc"
ATTACH = Path(
    "/data2/cmdir/home/toandq/.cursor/projects/data2-hpcshared-Vinh/attachments/c8490c3c-8029-48bf-90f8-080969f892d1"
)

LABEL_SOURCES = {
    "t7_PI_ok_labels.csv": QC / "t7_e1_unit_sample.csv",
    "t8_PI_ok_labels.csv": QC / "t8_mismatch_check.csv",
    "dose_PI_ok_labels.csv": QC / "expand_dose_sample.csv",
    "unit2_PI_ok_labels.csv": None,  # merged into expand_unit_natural by base_id
}


def _read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def copy_labels() -> None:
    for name in LABEL_SOURCES:
        src = QC / name
        if not src.is_file() and (ATTACH / name).is_file():
            shutil.copy2(ATTACH / name, src)


def merge_t7() -> dict:
    labels = {r["instance_id"]: r for r in _read(QC / "t7_PI_ok_labels.csv")}
    path = QC / "t7_e1_unit_sample.csv"
    rows = _read(path)
    for row in rows:
        lab = labels.get(row["instance_id"])
        if lab:
            row["PI_ok"] = lab["PI_ok"]
            if lab.get("note"):
                row["note"] = lab["note"]
    _write(path, rows, list(rows[0].keys()) if rows else [])
    c = Counter(r.get("PI_ok") for r in rows if r.get("PI_ok"))
    return {"file": str(path.name), "rows": len(rows), "PI_ok": dict(c)}


def merge_t8() -> dict:
    labels = {r["row_id"]: r for r in _read(QC / "t8_PI_ok_labels.csv")}
    path = QC / "t8_mismatch_check.csv"
    rows = _read(path)
    for row in rows:
        lab = labels.get(row["row_id"])
        if lab:
            row["PI_ok"] = lab["PI_ok"]
            if lab.get("note"):
                row["note"] = lab["note"]
    _write(path, rows, list(rows[0].keys()) if rows else [])
    c = Counter(r.get("PI_ok") for r in rows if r.get("PI_ok"))
    return {"file": str(path.name), "rows": len(rows), "PI_ok": dict(c)}


def merge_dose() -> dict:
    labels = {r["base_id"]: r for r in _read(QC / "dose_PI_ok_labels.csv")}
    path = QC / "expand_dose_sample.csv"
    rows = _read(path)
    for row in rows:
        lab = labels.get(row["base_id"])
        if lab:
            row["PI_ok"] = lab["PI_ok"]
            if lab.get("note"):
                row["note"] = lab["note"]
    _write(path, rows, list(rows[0].keys()) if rows else [])
    c = Counter(r.get("PI_ok") for r in rows if r.get("PI_ok"))
    return {"file": str(path.name), "rows": len(rows), "PI_ok": dict(c)}


def merge_unit2() -> dict:
    labels = {r["base_id"]: r for r in _read(QC / "unit2_PI_ok_labels.csv")}
    path = QC / "expand_unit_natural.csv"
    rows = _read(path)
    for row in rows:
        lab = labels.get(row["base_id"])
        if lab:
            row["PI_ok"] = lab["PI_ok"]
            if lab.get("note"):
                row["note"] = lab["note"]
    _write(path, rows, list(rows[0].keys()) if rows else [])
    sample = [r for r in rows if r.get("sample") == "1"]
    c = Counter(r.get("PI_ok") for r in sample if r.get("PI_ok"))
    return {
        "file": str(path.name),
        "rows": len(rows),
        "sample1_labeled": dict(c),
    }


def main() -> None:
    copy_labels()
    out = {
        "t7": merge_t7(),
        "t8": merge_t8(),
        "dose": merge_dose(),
        "unit2": merge_unit2(),
    }
    (QC / "pi_merge_report.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
