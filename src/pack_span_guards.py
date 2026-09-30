"""Shared span/sentence guards (T18 base drop + retroactive main_ext/T17 filters)."""

from __future__ import annotations

import re

from text_utils import DOSE_RE, T18_METRIC_RE

RANGE_IN_SPAN = re.compile(r"\d\s*[-–—]\s*\d")
EURO_THOUSANDS = re.compile(r"\b\d{1,3}\.\d{3}\b")
IMPERIAL_PAREN = re.compile(
    r"\(\s*\d+(?:\.\d+)?\s*(?:ft|in|inch|inches|lb|lbs|horsepower|hp|nautical\s+miles?)\b",
    re.I,
)
INVERSE_UNIT = re.compile(r"(?:cm|m|s|Hz|K)\s*[−\-]\s*1\b|/\s*(?:s|sec|second|m|cm)\b", re.I)
PROPER_NAME = re.compile(
    r"\b(?:Mount|Mt\.|Cape|River|Lake|Station|Slieve|Ararat|Aegean|Danube|Amazon|Rhodopes)\b",
    re.I,
)
BOUNDARY_DOWN = re.compile(
    r"(?:≤|>=|≥|<|up to|below|at most|no more than|\bor less\b|\bor fewer\b)",
    re.I,
)

_METRIC_UNIT = re.compile(r"\b(km|m|cm|kg|g|L|mL|ml|W|kW)\b", re.I)


def _row_span(row: dict) -> tuple[str, str]:
    claim = row.get("claim_c0") or row.get("claim") or ""
    span = row.get("claim_span") or ""
    if not span and row.get("diff"):
        side = row.get("edit_side") or "claim"
        block = (row.get("diff") or {}).get(side) or {}
        span = block.get("span_before") or ""
    return claim, span


def t18_base_exclusion(base: dict) -> str | None:
    """Return exclusion reason for whole T18 base, or None if keep."""
    claim = base.get("claim") or ""
    span = base.get("target_span_claim") or claim[
        base.get("claim_span_start", 0) : base.get("claim_span_end", 0)
    ]
    ctx = claim
    if RANGE_IN_SPAN.search(span) or re.search(
        rf"{re.escape(span[: max(3, len(span) // 2)])}.*[-–—].*\d", ctx
    ):
        if re.search(r"\d+\s*[-–—]\s*\d+\s*(?:km|m|cm|kg|g|L|ml|mL|W|kW)\b", ctx, re.I):
            return "range_on_quantity"
    if EURO_THOUSANDS.search(claim):
        return "european_thousands_separator"
    if IMPERIAL_PAREN.search(claim):
        return "imperial_conversion_in_parentheses"
    if INVERSE_UNIT.search(span) or INVERSE_UNIT.search(claim):
        return "inverse_unit"
    if PROPER_NAME.search(claim):
        return "proper_name_or_geo"
    # Target span sits inside a numeric range expression in claim
    if re.search(
        r"\d+\s*[-–—]\s*\d+\s*(?:km|m|cm|kg|g|L|ml|mL|W|kW)\b",
        claim,
        re.I,
    ) and span and claim.find(span) >= 0:
        window = claim[max(0, claim.find(span) - 15) : claim.find(span) + len(span) + 15]
        if RANGE_IN_SPAN.search(window):
            return "range_on_quantity"
    # Multiple distinct metric units in same sentence (claim)
    units = {m.group(2).lower() for m in T18_METRIC_RE.finditer(claim)}
    units |= {m.group(1).lower() for m in _METRIC_UNIT.finditer(claim)}
    if len(units) > 1:
        return "same_sentence_multiple_metric_units"
    return None


def retroactive_row_guard(row: dict) -> str | None:
    """Filter main_ext / T17 rows that slipped through (no base regen)."""
    claim, span = _row_span(row)
    text = f"{claim} {row.get('evidence') or ''}"
    if EURO_THOUSANDS.search(claim):
        return "guard_european_thousands"
    if IMPERIAL_PAREN.search(claim):
        return "guard_imperial_paren"
    if INVERSE_UNIT.search(span) or INVERSE_UNIT.search(text):
        return "guard_inverse_unit"
    if re.search(
        r"\d+\s*[-–—]\s*\d+\s*(?:km|m|cm|kg|g|mg|mcg|µg|μg|L|ml|mL|W|kW|units?)\b",
        claim,
        re.I,
    ):
        return "guard_range_on_quantity"
    units = set()
    for m in DOSE_RE.finditer(claim):
        units.add(m.group(2).lower())
    for m in T18_METRIC_RE.finditer(claim):
        units.add(m.group(2).lower())
    if len(units) > 1 and span:
        return "guard_same_sentence_multi_unit"
    return None


def t17_boundary_down_edit(row: dict) -> bool:
    ctx = f"{row.get('claim') or ''} {row.get('evidence') or ''}"
    return bool(BOUNDARY_DOWN.search(ctx) and row.get("magnitude") in ("down2", "down10"))
