#!/usr/bin/env python3
"""Summarize PI failure modes from qc/dose2_PI_ok_labels.csv (N rows)."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "qc/dose2_PI_ok_labels.csv"


def categorize(note: str) -> list[str]:
    n = (note or "").lower()
    tags: list[str] = []
    if re.search(r"1,\d{4}|sai định dạng số|thousands", n):
        tags.append("thousands_separator_bug")
    if "không phải liều" in n or "loại:" in n or "hematoma" in n or "blood loss" in n:
        tags.append("non_dose_volume")
    if "thiếu tên thuốc" in n or "the gel" in n or "the specific drug" in n or "the study" in n:
        tags.append("missing_drug_or_generic_subject")
    if "ngưỡng" in n or "above" in n or "at doses" in n or "threshold" in n:
        tags.append("threshold_context")
    if "bỏ bối cảnh" in n or "context" in n:
        tags.append("c0_context_stripped")
    if "mâu thuẫn không rõ" in n or "chưa chắc mâu thuẫn" in n or "weak e1" in n:
        tags.append("weak_e1_contrast")
    if not tags:
        tags.append("other")
    return tags


def main() -> None:
    if not LABELS.is_file():
        raise SystemExit(f"missing {LABELS}")
    rows = list(csv.DictReader(LABELS.open(encoding="utf-8-sig")))
    n_y = sum(1 for r in rows if (r.get("PI_ok") or "").strip().upper() == "Y")
    n_n = sum(1 for r in rows if (r.get("PI_ok") or "").strip().upper() == "N")
    by_tag: dict[str, list[dict]] = defaultdict(list)
    tag_counts: Counter[str] = Counter()
    for row in rows:
        if (row.get("PI_ok") or "").strip().upper() != "N":
            continue
        note = row.get("note") or ""
        tags = categorize(note)
        for t in tags:
            tag_counts[t] += 1
            by_tag[t].append({"base_id": row["base_id"], "note": note})
    payload = {
        "labeled_rows": len(rows),
        "pi_ok_y": n_y,
        "pi_ok_n": n_n,
        "y_rate": round(n_y / len(rows), 4) if rows else None,
        "gate_threshold": 0.85,
        "gate_pass": (n_y / len(rows) >= 0.85) if rows else False,
        "failure_tag_counts": dict(tag_counts),
        "examples_by_tag": {k: v[:8] for k, v in sorted(by_tag.items())},
    }
    notes = ROOT / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    (notes / "expand_dose2_failure_types.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# Expanded DOSE spot-check failure types (dose2 PI notes)",
        "",
        f"- Labeled rows: **{len(rows)}** ({n_y} Y / {n_n} N → **{100 * n_y / len(rows):.1f}%** Y; gate **85%**).",
        "",
        "## Tag counts (N rows; multi-tag allowed)",
        "",
    ]
    for tag, count in tag_counts.most_common():
        lines.append(f"- **{tag}**: {count}")
    lines.extend(["", "## Examples", ""])
    for tag in sorted(by_tag):
        lines.append(f"### {tag}")
        for ex in by_tag[tag][:5]:
            lines.append(f"- **{ex['base_id']}**: {ex['note']}")
        lines.append("")
    (notes / "expand_dose2_failure_types.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"pi_ok_y": n_y, "pi_ok_n": n_n, "tags": dict(tag_counts)}, indent=2))


if __name__ == "__main__":
    main()
