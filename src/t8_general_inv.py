"""General quantity INV / E1-unit edits for T8 AggreFact samples."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional

from general_quantity import QTY_UNIT_RE, _parse_num
from text_utils import e1_unit_only_swap, format_decimal

_SCALE = re.compile(
    r"(?<![\w./])(\d+(?:\.\d+)?)\s*(thousand|million|billion)\b", re.I
)
_HM = re.compile(r"(?<![\w./])(\d+(?:\.\d+)?)\s*(hours?|hrs?|hr|minutes?|mins?|min)\b", re.I)
_KM = re.compile(r"(?<![\w./])(\d+(?:\.\d+)?)\s*(km|kilometers?|meters?|metres?|m\b)\b", re.I)
_KG = re.compile(r"(?<![\w./])(\d+(?:\.\d+)?)\s*(kg|kilograms?|grams?|g\b)\b", re.I)
_PCT = re.compile(r"(?<![\w./])(\d+(?:\.\d+)?)\s*(%|percent|percentage)\b", re.I)


def _scale_swap(text: str) -> Optional[tuple[str, str, str]]:
    m = _SCALE.search(text)
    if not m:
        return None
    num = _parse_num(m.group(1))
    if num is None:
        return None
    word = m.group(2).lower()
    if word == "million":
        new_num = num * Decimal("1000")
        new_word = "billion"
        pair = "million↔billion"
    elif word == "billion":
        new_num = num * Decimal("1000")
        new_word = "million"
        pair = "billion↔million"
    else:
        return None
    old = m.group(0)
    new = f"{format_decimal(new_num)} {new_word}"
    return text.replace(old, new, 1), pair, "scale"


def _time_swap(text: str) -> Optional[tuple[str, str, str]]:
    m = _HM.search(text)
    if not m:
        return None
    num = _parse_num(m.group(1))
    if num is None:
        return None
    unit = m.group(2).lower()
    old = m.group(0)
    if unit.startswith("h"):
        if num != num.to_integral_value():
            return None
        new = f"{format_decimal(num * Decimal('60'))} minutes"
        pair = "hours↔minutes"
    elif unit.startswith("min"):
        if num % Decimal("60") != 0:
            return None
        new = f"{format_decimal(num / Decimal('60'))} hours"
        pair = "minutes↔hours"
    else:
        return None
    return text.replace(old, new, 1), pair, "time"


def _len_swap(text: str) -> Optional[tuple[str, str, str]]:
    m = _KM.search(text)
    if not m:
        return None
    num = _parse_num(m.group(1))
    if num is None:
        return None
    u = m.group(2).lower()
    old = m.group(0)
    if u in {"km", "kilometer", "kilometers"}:
        new = f"{format_decimal(num * Decimal('1000'))} m"
        pair = "km↔m"
    elif u in {"m", "meter", "meters", "metre", "metres"} and num >= Decimal("1000"):
        new = f"{format_decimal(num / Decimal('1000'))} km"
        pair = "m↔km"
    else:
        return None
    return text.replace(old, new, 1), pair, "length"


def _mass_swap(text: str) -> Optional[tuple[str, str, str]]:
    m = _KG.search(text)
    if not m:
        return None
    num = _parse_num(m.group(1))
    if num is None:
        return None
    u = m.group(2).lower()
    old = m.group(0)
    if u in {"kg", "kilogram", "kilograms"}:
        new = f"{format_decimal(num * Decimal('1000'))} g"
        pair = "kg↔g"
    elif u in {"g", "gram", "grams"} and num >= Decimal("1000"):
        new = f"{format_decimal(num / Decimal('1000'))} kg"
        pair = "g↔kg"
    else:
        return None
    return text.replace(old, new, 1), pair, "mass"


def _percent_swap(text: str) -> Optional[tuple[str, str, str]]:
    m = _PCT.search(text)
    if not m:
        return None
    num = _parse_num(m.group(1))
    if num is None:
        return None
    old = m.group(0)
    u = m.group(2).lower()
    if u == "%":
        new = f"{format_decimal(num)} percent"
        pair = "%↔percent"
    else:
        new = f"{format_decimal(num)}%"
        pair = "percent↔%"
    return text.replace(old, new, 1), pair, "percent"


def general_inv_edit(claim: str) -> Optional[tuple[str, str, str, str]]:
    """Return (new_claim, pair, edit_kind, matched_surface) or None."""
    claim = claim or ""
    for fn in (_len_swap, _mass_swap, _time_swap, _scale_swap, _percent_swap):
        out = fn(claim)
        if out and out[0] != claim:
            new, pair, kind = out
            return new, pair, kind, ""
    for m in QTY_UNIT_RE.finditer(claim):
        surf = m.group(0).strip()
        swap = e1_unit_only_swap(surf)
        if swap:
            new_span, pair = swap
            new_claim = claim.replace(surf, new_span, 1)
            if new_claim != claim:
                return new_claim, pair, "med_unit", surf
    return None
