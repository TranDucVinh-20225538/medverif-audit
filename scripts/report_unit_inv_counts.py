#!/usr/bin/env python3
"""Report INV-unit counts: all / natural, legacy / rule (old / new)."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from review_filters import effective_unit_natural_y, unit_natural_labels  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def original_span(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    if claim.get("span_before"):
        return str(claim["span_before"])
    return str(row.get("claim_span") or "")


def expand_unit_labels() -> dict[str, str]:
    path = ROOT / "qc" / "expand_unit_natural.csv"
    if not path.is_file():
        return {}
    return {
        r["base_id"]: (r.get("PI_ok") or "").strip()
        for r in csv.DictReader(path.open(newline="", encoding="utf-8"))
        if (r.get("PI_ok") or "").strip() in {"Y", "N"}
    }


def main() -> None:
    expand = "--expand" in sys.argv
    if expand:
        paths = [
            ROOT / "data" / "expand" / "instances_main.jsonl",
            ROOT / "data" / "expand" / "v3" / "instances_threshold.jsonl",
            ROOT / "data" / "expand" / "v3" / "instances_range.jsonl",
        ]
        csv_labels = expand_unit_labels()
    else:
        paths = [
            ROOT / "data" / "v3" / "instances_main.jsonl",
            ROOT / "data" / "v3" / "instances_threshold.jsonl",
            ROOT / "data" / "v3" / "instances_range.jsonl",
        ]
        csv_labels = unit_natural_labels()
    rows = []
    for p in paths:
        rows.extend(read_jsonl(p))
    unit = [
        r
        for r in rows
        if r.get("valid")
        and r.get("type") == "DOSE"
        and r.get("condition") == "INV-claim"
        and r.get("magnitude") == "unit_conversion"
    ]
    bases = {r["base_id"] for r in unit}
    by_source = Counter(r.get("unit_inv_source") or "unknown" for r in unit)
    natural_bases: set[str] = set()
    for r in unit:
        bid = r["base_id"]
        orig = original_span(r)
        rule_y = bool(rule_natural_unit_conversion_label(orig))
        if effective_unit_natural_y(bid, rule_y):
            natural_bases.add(bid)
    old_bases = {r["base_id"] for r in unit if (r.get("unit_inv_source") or "legacy") == "legacy"}
    new_bases = {r["base_id"] for r in unit if r.get("unit_inv_source") == "rule"}
    only_new = new_bases - old_bases
    report = {
        "valid_unit_inv_instances": len(unit),
        "valid_unit_inv_bases_all": len(bases),
        "by_source": dict(by_source),
        "natural_bases_effective_Y": len(natural_bases),
        "natural_from_PI_only": len({b for b in natural_bases if b in csv_labels and csv_labels[b] == "Y"}),
        "old_legacy_bases": len(old_bases),
        "new_rule_only_bases": len(only_new),
        "csv_unit_naturalness_rows": len(csv_labels),
    }
    print(json.dumps(report, indent=2))
    out_name = "unit_inv_counts_expand.json" if expand else "unit_inv_counts.json"
    (ROOT / "notes" / out_name).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
