#!/usr/bin/env python3
"""Normalize µ (U+00B5) → μ (U+03BC) in T7 instances and QC sample."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import normalize_micro_sign  # noqa: E402

T7_INST = ROOT / "data/t7/instances_e1_unit.jsonl"
T7_SAMPLE = ROOT / "qc/t7_e1_unit_sample.csv"
TEXT_KEYS = ("claim", "evidence", "claim_c0", "evidence_c0", "unit_pair", "span_before", "span_after")


def norm_row(row: dict) -> dict:
    out = dict(row)
    for k in TEXT_KEYS:
        if k in out and isinstance(out[k], str):
            out[k] = normalize_micro_sign(out[k])
    if out.get("claim_span"):
        out["claim_span"] = normalize_micro_sign(out["claim_span"])
    if out.get("evidence_span"):
        out["evidence_span"] = normalize_micro_sign(out["evidence_span"])
    return out


def main() -> None:
    if T7_INST.is_file():
        rows = [norm_row(json.loads(line)) for line in T7_INST.read_text().splitlines() if line.strip()]
        T7_INST.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    if T7_SAMPLE.is_file():
        with T7_SAMPLE.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        fn = rows[0].keys() if rows else []
        for row in rows:
            for k in ("span_before", "span_after", "unit_pair", "claim", "evidence", "claim_c0"):
                if row.get(k):
                    row[k] = normalize_micro_sign(row[k])
        with T7_SAMPLE.open("w", newline="", encoding="utf-8") as handle:
            w = csv.DictWriter(handle, fieldnames=fn)
            w.writeheader()
            w.writerows(rows)
    print(json.dumps({"t7_instances": T7_INST.is_file(), "t7_sample": T7_SAMPLE.is_file()}))


if __name__ == "__main__":
    main()
