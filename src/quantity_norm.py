"""M1: rule-based dose/unit canonicalization before verifiers (hand map, no pint)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Tuple

from text_utils import DOSE_RE, format_decimal, parse_decimal

_MASS_TO_MG = {
    "mg": Decimal("1"),
    "g": Decimal("1000"),
    "mcg": Decimal("0.001"),
    "µg": Decimal("0.001"),
    "μg": Decimal("0.001"),
    "micrograms": Decimal("0.001"),
    "milligrams": Decimal("1"),
    "grams": Decimal("1000"),
}

_VOL_TO_ML = {
    "ml": Decimal("1"),
    "mL": Decimal("1"),
    "l": Decimal("1000"),
    "L": Decimal("1000"),
}


def _split_unit(unit: str) -> tuple[str, str]:
    """Return (base_unit, rate_suffix e.g. '/kg/day')."""
    for base in sorted(_MASS_TO_MG.keys(), key=len, reverse=True):
        if unit == base:
            return base, ""
        if unit.startswith(base + "/"):
            return base, unit[len(base) :]
    for base in sorted(_VOL_TO_ML.keys(), key=len, reverse=True):
        if unit == base:
            return base, ""
        if unit.startswith(base + "/"):
            return base, unit[len(base) :]
    return unit, ""


def canonicalize_dose_span(number: str, unit: str) -> str:
    """One dose token in canonical mass (mg) or volume (mL) form."""
    n = parse_decimal(number)
    base, suffix = _split_unit(unit)
    if base in _MASS_TO_MG:
        mg = n * _MASS_TO_MG[base]
        return f"{format_decimal(mg)} mg{suffix}"
    if base in _VOL_TO_ML:
        ml = n * _VOL_TO_ML[base]
        canon = "mL" if suffix == "" else "mL"
        return f"{format_decimal(ml)} {canon}{suffix}"
    return f"{format_decimal(n)} {unit}"


def normalize_quantities(text: str) -> str:
    """Replace each dose match with canonical form; other text unchanged."""
    if not text:
        return text

    def repl(match: re.Match) -> str:
        try:
            return canonicalize_dose_span(match.group(1), match.group(2))
        except (ValueError, InvalidOperation):
            return match.group(0)

    return DOSE_RE.sub(repl, text)


def apply_m1_pair(claim: str, evidence: str) -> tuple[str, str]:
    return normalize_quantities(claim), normalize_quantities(evidence)


_FREQ_CANON = (
    (re.compile(r"\bb\.?i\.?d\.?\b", re.I), "twice daily"),
    (re.compile(r"\bt\.?i\.?d\.?\b", re.I), "three times daily"),
    (re.compile(r"\bq\.?i\.?d\.?\b", re.I), "four times daily"),
    (re.compile(r"\bq\.?d\.?\b", re.I), "once daily"),
    (re.compile(r"\bq12h\b", re.I), "every 12 hours"),
    (re.compile(r"\bq8h\b", re.I), "every 8 hours"),
    (re.compile(r"\bq6h\b", re.I), "every 6 hours"),
)

_ROUTE_CANON = (
    (re.compile(r"\bintravenously\b", re.I), "IV"),
    (re.compile(r"\bintramuscularly\b", re.I), "IM"),
    (re.compile(r"\borally\b", re.I), "PO"),
    (re.compile(r"\bsubcutaneously\b", re.I), "SC"),
    (re.compile(r"\bI\.V\.\b"), "IV"),
    (re.compile(r"\bI\.M\.\b"), "IM"),
    (re.compile(r"\bP\.O\.\b", re.I), "PO"),
    (re.compile(r"\bS\.C\.\b", re.I), "SC"),
    (re.compile(r"\bS\.Q\.\b", re.I), "SC"),
)


def _apply_alias_rules(text: str, rules: Iterable[tuple[re.Pattern, str]]) -> str:
    out = text
    for pat, repl in rules:
        out = pat.sub(repl, out)
    return out


def normalize_frequency_route(text: str) -> str:
    """M1+: canonicalize common frequency/route phrases (claim/evidence text)."""
    if not text:
        return text
    out = _apply_alias_rules(text, _FREQ_CANON)
    return _apply_alias_rules(out, _ROUTE_CANON)


def apply_m1_plus_pair(claim: str, evidence: str) -> tuple[str, str]:
    c, e = apply_m1_pair(claim, evidence)
    return normalize_frequency_route(c), normalize_frequency_route(e)
