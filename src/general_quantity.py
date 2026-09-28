"""General quantity extraction for T8 (non-medical blind-spot audit)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import NamedTuple

from text_utils import DOSE_RE, parse_decimal

# Plain numerals (incl. comma thousands)
_NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_NUM_CAP = r"(\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_ANY_NUM_RE = re.compile(rf"(?<![\w./]){_NUM}(?![\w/])")

_UNIT_SUFFIX = (
    r"(?:km|kilometers?|m|meters?|metres?|cm|mm|mi|miles?|ft|feet|"
    r"kg|kilograms?|g|grams?|mg|lb|lbs|pounds?|oz|ounces?|"
    r"l|liters?|litres?|ml|milliliters?|"
    r"hours?|hrs?|hr|minutes?|mins?|min|seconds?|secs?|"
    r"percent|%|USD|\$|€|EUR|dollars?|euros?)"
)
QTY_UNIT_RE = re.compile(rf"(?<![\w./]){_NUM_CAP}\s*({_UNIT_SUFFIX})\b", re.I)

_SCALE_WORD = re.compile(
    rf"(?<![\w./]){_NUM_CAP}\s*(thousand|million|billion|trillion)\b", re.I
)
_CURRENCY = re.compile(
    rf"(?:\$|€)\s*{_NUM_CAP}|\b{_NUM_CAP}\s*(USD|EUR|dollars?|euros?)\b", re.I
)
_PERCENT = re.compile(rf"(?<![\w./]){_NUM_CAP}\s*(%|percent|percentage)\b", re.I)
_PLAIN_NUM = _ANY_NUM_RE

_MED_DOSE = DOSE_RE


class Qty(NamedTuple):
    surface: str
    value: Decimal | None
    kind: str  # unit | scale | currency | percent | plain
    unit: str


def _parse_num(s: str) -> Decimal | None:
    try:
        return parse_decimal(s.replace(",", ""))
    except (ValueError, InvalidOperation):
        return None


def extract_general_quantities(text: str) -> list[Qty]:
    text = text or ""
    found: list[Qty] = []
    seen: set[str] = set()

    def add(surface: str, value: Decimal | None, kind: str, unit: str = "") -> None:
        key = surface.lower()
        if key in seen:
            return
        seen.add(key)
        found.append(Qty(surface=surface.strip(), value=value, kind=kind, unit=unit))

    for m in _MED_DOSE.finditer(text):
        add(m.group(0), _parse_num(m.group(1)), "med_dose", m.group(2))
    for m in QTY_UNIT_RE.finditer(text):
        num, unit = m.group(1), m.group(2)
        add(m.group(0), _parse_num(num), "unit", unit.lower())
    for m in _SCALE_WORD.finditer(text):
        add(m.group(0), _parse_num(m.group(1)), "scale", m.group(2).lower())
    for m in _CURRENCY.finditer(text):
        num_g = m.group(1) or m.group(2)
        add(m.group(0), _parse_num(num_g) if num_g else None, "currency", "$")
    for m in _PERCENT.finditer(text):
        add(m.group(0), _parse_num(m.group(1)), "percent", "%")
    for m in _PLAIN_NUM.finditer(text):
        surf = m.group(0)
        if any(surf in q.surface for q in found):
            continue
        add(surf, _parse_num(surf), "plain", "")

    return found


def claim_has_any_number(text: str) -> bool:
    return bool(_ANY_NUM_RE.search(text or ""))


def claim_has_number_unit(text: str) -> bool:
    qs = extract_general_quantities(text)
    return any(q.kind in ("unit", "med_dose", "scale", "currency", "percent") for q in qs)


def _normalize_value(q: Qty) -> Decimal | None:
    if q.value is None:
        return None
    v = q.value
    if q.kind == "scale":
        mult = {"thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000, "trillion": 1_000_000_000_000}
        return v * mult.get(q.unit, 1)
    return v


_UNIT_CANON = {
    "kilometer": "m", "kilometers": "m", "km": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "mile": "m", "miles": "m", "mi": "m", "ft": "m", "feet": "m",
    "kg": "g", "kilogram": "g", "kilograms": "g", "gram": "g", "grams": "g", "g": "g",
    "mg": "g", "lb": "g", "lbs": "g", "pound": "g", "pounds": "g", "oz": "g", "ounce": "g", "ounces": "g",
    "hour": "s", "hours": "s", "hr": "s", "hrs": "s",
    "minute": "s", "minutes": "s", "min": "s", "mins": "s",
    "second": "s", "seconds": "s", "sec": "s", "secs": "s",
}


def _canon_unit(u: str) -> str:
    return _UNIT_CANON.get(u.lower(), u.lower())


def format_quantity_mismatch(claim: str, doc: str) -> bool:
    """Same underlying quantity, different unit/format between claim and doc."""
    cq = extract_general_quantities(claim)
    dq = extract_general_quantities(doc)
    if not cq or not dq:
        return False

    for c in cq:
        cv = _normalize_value(c)
        if cv is None:
            continue
        for d in dq:
            dv = _normalize_value(d)
            if dv is None:
                continue
            # scale / plain cross (e.g. 1.2 billion vs 1200 million)
            if c.kind in ("scale", "plain") and d.kind in ("scale", "plain"):
                if cv == dv and c.surface.lower() != d.surface.lower():
                    return True
            # percent vs fraction wording (50% vs 0.5)
            if c.kind == "percent" and d.kind == "plain":
                if d.value is not None and cv / Decimal("100") == d.value:
                    return True
            if d.kind == "percent" and c.kind == "plain":
                if c.value is not None and dv / Decimal("100") == c.value:
                    return True
            # same numeric, different unit token
            if c.kind in ("unit", "med_dose") and d.kind in ("unit", "med_dose"):
                if c.value == d.value and _canon_unit(c.unit) == _canon_unit(d.unit):
                    if c.unit.lower() != d.unit.lower() or c.surface != d.surface:
                        return True
                # km vs m same length when values differ by 1000
                if _canon_unit(c.unit) == _canon_unit(d.unit) == "m" and c.unit != d.unit:
                    if c.value is not None and d.value is not None:
                        if c.value * Decimal("1000") == d.value or d.value * Decimal("1000") == c.value:
                            return True
    return False
