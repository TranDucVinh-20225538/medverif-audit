#!/usr/bin/env python3
"""Dedupe T17 raw scores by (instance_id, verifier), keep latest; filter to qc/t17_labels.csv."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/raw/t17"
LABELS = ROOT / "qc/t17_labels.csv"
OUT_REPORT = ROOT / "notes/t17_dedupe_report.json"


def load_valid_ids() -> set[str]:
    valid: set[str] = set()
    with LABELS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (row.get("human_ok") or "").strip().upper() == "Y":
                iid = (row.get("instance_id") or row.get("\ufeffinstance_id") or "").strip()
                if iid:
                    valid.add(iid)
    return valid


def dedupe_file(path: Path) -> dict:
    by_key: dict[tuple[str, str], dict] = {}
    conflicts = 0
    for line in path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        iid = row.get("instance_id") or ""
        vid = row.get("verifier_id") or row.get("verifier") or path.stem
        key = (iid, vid)
        if key in by_key and by_key[key].get("verdict") != row.get("verdict"):
            conflicts += 1
        by_key[key] = row
    tmp = path.with_suffix(path.suffix + ".dedupe.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for row in by_key.values():
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)
    return {"file": str(path.relative_to(ROOT)), "lines_in": len(by_key), "conflicts": conflicts}


def main() -> None:
    valid = load_valid_ids()
    report: dict = {"valid_label_rows_Y": len(valid), "per_file": [], "per_verifier_after_filter": {}}
    for path in sorted(RAW.glob("*.jsonl")):
        if ".bak." in path.name or path.name.endswith(".tmp"):
            continue
        info = dedupe_file(path)
        filtered = []
        for line in path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("instance_id") in valid:
                filtered.append(row)
        vid = path.stem
        report["per_file"].append({**info, "after_pi_filter": len(filtered)})
        report["per_verifier_after_filter"][vid] = len(filtered)
    OUT_REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
