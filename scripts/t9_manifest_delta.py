#!/usr/bin/env python3
"""Explain T9 manifest shrink (legacy scored rows vs current instances_all)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from review_filters import effective_unit_natural_y, unit_natural_labels  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

LEGACY = ROOT / "results/raw/t9/alignscore_rail.legacy_536.jsonl"
CURRENT = ROOT / "data/t9/instances_all.jsonl"
OUT = ROOT / "notes/t9_manifest_changelog.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def inv_span_before(row: dict) -> str:
    return str(row.get("claim") or row.get("bot_message") or "")


def classify_inv_removal(base_id: str, span: str) -> str:
    human = unit_natural_labels().get(base_id, "")
    rule_y = bool(rule_natural_unit_conversion_label(span))
    if human == "N":
        return "human_unit_natural_N"
    if human == "Y":
        return "human_Y_but_excluded_other"
    if not rule_y:
        return "rule_natural_unit_conversion_false"
    return "unknown"


def main() -> None:
    legacy_rows = read_jsonl(LEGACY) if LEGACY.is_file() else []
    current_rows = read_jsonl(CURRENT)
    legacy_by_id: dict[str, dict] = {}
    legacy_dupes: list[str] = []
    for r in legacy_rows:
        iid = r["instance_id"]
        if iid in legacy_by_id:
            legacy_dupes.append(iid)
        legacy_by_id[iid] = r

    current_ids = {r["instance_id"] for r in current_rows}
    removed_ids = sorted(set(legacy_by_id) - current_ids)

    removal_reasons: Counter[str] = Counter()
    removed_detail: list[dict] = []
    for iid in removed_ids:
        r = legacy_by_id[iid]
        grp = r.get("t9_group")
        stratum = r.get("stratum") or r.get("eco_category_final")
        reason = "not_in_current_manifest"
        if grp == "b" and stratum == "inv_unit_natural":
            reason = classify_inv_removal(r.get("base_id") or "", inv_span_before(r))
        removal_reasons[reason] += 1
        removed_detail.append(
            {
                "instance_id": iid,
                "t9_group": grp,
                "stratum": stratum,
                "base_id": r.get("base_id"),
                "removal_reason": reason,
            }
        )

    payload = {
        "legacy_score_lines": len(legacy_rows),
        "legacy_unique_instance_ids": len(legacy_by_id),
        "legacy_duplicate_instance_ids": sorted(set(legacy_dupes)),
        "legacy_duplicate_line_count": len(legacy_dupes),
        "current_manifest_n": len(current_rows),
        "unique_ids_removed": len(removed_ids),
        "all_removed_are_group_b_inv_unit_natural": all(
            legacy_by_id[i].get("t9_group") == "b"
            and legacy_by_id[i].get("stratum") == "inv_unit_natural"
            for i in removed_ids
        )
        if removed_ids
        else True,
        "removal_reason_counts": dict(removal_reasons),
        "policy_summary": (
            "Current manifest applies effective_unit_natural_y: human qc/unit_naturalness.csv "
            "(Y/N) overrides rule_natural_unit_conversion_label on INV-claim unit_conversion spans. "
            "Legacy 536-line batch included inv_unit_natural rows that fail this gate."
        ),
        "removed_instances": removed_detail,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({k: payload[k] for k in payload if k != "removed_instances"}, indent=2))


if __name__ == "__main__":
    main()
