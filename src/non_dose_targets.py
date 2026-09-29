"""Bases whose target span is not a medication dose (lab threshold, conversion note, etc.)."""

from __future__ import annotations

NON_DOSE_TARGET_BASES = frozenset({"D0171", "D0173"})


def invalidate_non_dose_row(row: dict) -> dict:
    bid = row.get("base_id") or row.get("id")
    if bid in NON_DOSE_TARGET_BASES:
        row["valid"] = False
        row["invalid_reason"] = "non_dose_target"
    return row
