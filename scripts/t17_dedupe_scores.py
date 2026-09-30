#!/usr/bin/env python3
"""Dedupe T17 raw scores by (instance_id, verifier), keep latest; filter to qc/t17_labels.csv."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import read_jsonl  # noqa: E402
from review_filters import analysis_keep_row, flip_pi_ok_bases, inv_pi_ok_keys  # noqa: E402

RAW = ROOT / "results/raw/t17"
LABELS = ROOT / "qc/t17_labels.csv"
T17_INST = ROOT / "data/v3/t17_downdose.jsonl"
OUT_REPORT = ROOT / "notes/t17_dedupe_report.json"

_FLIP = flip_pi_ok_bases()
_INV = inv_pi_ok_keys()


def load_manifest_ids() -> set[str]:
    return {
        r["instance_id"]
        for r in read_jsonl(T17_INST)
        if r.get("valid", True) and analysis_keep_row(r, flip_y=_FLIP, inv_keys=_INV)
    }


def load_label_y_ids() -> set[str]:
    valid: set[str] = set()
    if not LABELS.is_file():
        return valid
    with LABELS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (row.get("human_ok") or "").strip().upper() == "Y":
                iid = (row.get("instance_id") or "").strip()
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
    rows = list(by_key.values())
    return {
        "file": str(path.relative_to(ROOT)),
        "lines_in": len(rows),
        "conflicts": conflicts,
        "rows": rows,
    }


def main() -> None:
    manifest = load_manifest_ids()
    label_y = load_label_y_ids()
    # Author PI sample uses label_y when present; else analysis_keep manifest (expect 540).
    filter_ids = manifest if len(label_y) < 100 else label_y
    report: dict = {
        "manifest_analysis_keep_n": len(manifest),
        "label_y_n": len(label_y),
        "filter_ids_n": len(filter_ids),
        "per_file": [],
        "per_verifier_after_filter": {},
    }
    for path in sorted(RAW.glob("*.jsonl")):
        if ".bak." in path.name or path.name.endswith(".tmp"):
            continue
        info = dedupe_file(path)
        kept = [row for row in info["rows"] if row.get("instance_id") in filter_ids]
        del info["rows"]
        tmp2 = path.with_suffix(path.suffix + ".filter.tmp")
        with tmp2.open("w", encoding="utf-8") as handle:
            for row in kept:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        tmp2.replace(path)
        vid = path.stem
        report["per_file"].append({**info, "after_filter": len(kept), "removed_extra_ids": info["lines_in"] - len(kept)})
        report["per_verifier_after_filter"][vid] = len(kept)
    OUT_REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
