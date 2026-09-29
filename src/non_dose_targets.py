"""Bases whose target span is not a medication dose (lab threshold, conversion note, etc.)."""

from __future__ import annotations

NON_DOSE_TARGET_BASES = frozenset(
    {
        "D0077",  # fluid volume returned to circulation (not a medication dose)
        "D0096",
        "D0157",
        "D0158",
        "D0160",
        "D0164",  # catheter / feeding-tube fluid volume (not a medication dose)
        "D0171",
        "D0173",
        "D0176",
    }
)


def invalidate_non_dose_row(row: dict) -> dict:
    bid = row.get("base_id") or row.get("id")
    if bid in NON_DOSE_TARGET_BASES:
        row["valid"] = False
        row["invalid_reason"] = "non_dose_target"
    return row
