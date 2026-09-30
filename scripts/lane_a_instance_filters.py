#!/usr/bin/env python3
"""Shared row filters for Lane A/B packs (non-dose + analysis gates)."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from non_dose_targets import invalidate_non_dose_row  # noqa: E402
from review_filters import analysis_keep_row  # noqa: E402


def lane_b_e1_evid_row(row: dict) -> bool:
    """Main E1-evid rows for local checker scoring (matches analysis cohort)."""
    if row.get("subset") != "main" or row.get("condition") != "E1-evid":
        return False
    r = copy.deepcopy(row)
    invalidate_non_dose_row(r)
    if not r.get("valid", True):
        return False
    return analysis_keep_row(r)
