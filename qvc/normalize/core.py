"""Vendored M1 quantity normalizer (matches medverif-audit src/quantity_norm.py)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

DOSE_NUM = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?"
_UNIT = (
    r"(?:mg/kg/min|mg/kg/day|mg/kg/h|mcg/kg/min|mcg/kg/day|mcg/kg/h|"
    r"mcg/kg|mg/kg|"
    r"mcg|µg|μg|mg|mL|ml|L|l|g|units|micrograms|milligrams|grams)"
)
DOSE_RE = re.compile(rf"(?<![\w./])({DOSE_NUM})\s*({_UNIT})(?![\w/])")

_MASS_TO_MG = {"mg": Decimal("1"), "g": Decimal("1000"), "mcg": Decimal("0.001"), "µg": Decimal("0.001"), "μg": Decimal("0.001")}


def _format_decimal(d: Decimal) -> str:
    s = format(d.normalize(), "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


def _split_unit(unit: str) -> tuple[str, str]:
    for base in sorted(_MASS_TO_MG.keys(), key=len, reverse=True):
        if unit == base:
            return base, ""
        if unit.startswith(base + "/"):
            return base, unit[len(base) :]
    return unit, ""


def canonicalize_dose_span(number: str, unit: str) -> str:
    n = Decimal(number.replace(",", ""))
    base, suffix = _split_unit(unit)
    if base in _MASS_TO_MG:
        mg = n * _MASS_TO_MG[base]
        return f"{_format_decimal(mg)} mg{suffix}"
    return f"{_format_decimal(n)} {unit}"


def normalize(text: str) -> str:
    if not text:
        return text

    def repl(match: re.Match) -> str:
        try:
            return canonicalize_dose_span(match.group(1), match.group(2))
        except (ValueError, InvalidOperation):
            return match.group(0)

    return DOSE_RE.sub(repl, text)


def normalize_pair(claim: str, evidence: str) -> tuple[str, str]:
    return normalize(claim), normalize(evidence)
