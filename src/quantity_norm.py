"""M1: rule-based dose/unit canonicalization before verifiers (hand map, no pint)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Tuple

from text_utils import format_decimal, parse_decimal

# M1 dose regex that produced the node30 M1 texts (commit 02ae97e data; text_utils in stash "pre
# node30-results merge"). Kept verbatim so those texts stay reproducible: it rebuilds
# instances_m1_pending_node30 (T1) 942/942 and lane_b/m1_t17_unit_down (US_down) 150/150
# byte-for-byte (notes/m1_provenance.md).
_M1_NUM = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?"
_M1_UNIT_NODE30 = (
    r"(?:mg/kg/min|mg/kg/day|mg/kg/h|mcg/kg/min|mcg/kg/day|mcg/kg/h|"
    r"mcg/kg|mg/kg|"
    r"mcg|µg|μg|mg|mL|ml|L|l|g|units|micrograms|milligrams|grams)"
)
M1_DOSE_RE_NODE30 = re.compile(rf"(?<![\w./])({_M1_NUM})\s*({_M1_UNIT_NODE30})(?![\w/])")

# Amendment 5 (notes/m1_prereg_amendment5.md): every mass, volume, mass/kg and volume/kg dose with
# optional rate suffix is rewritten (mass→mg, volume→mL, mass/mass→mg/kg). Concentrations such as
# mg/dL or mcg/mL are outside the amendment-4 spec and stay untouched.
_M1_MASS = r"micrograms|milligrams|grams|mcg|µg|μg|mg|g"
_M1_VOL = r"mL|ml|L|l"
_M1_RATE = r"(?:/kg)?(?:/(?:min|day|dose|hr|h|d))?"
_M1_UNIT_SPEC = rf"(?:(?:{_M1_MASS}|{_M1_VOL}){_M1_RATE}|units)"
M1_DOSE_RE_SPEC = re.compile(rf"(?<![\w./])({_M1_NUM})\s*({_M1_UNIT_SPEC})(?![\w/])")

M1_DOSE_RE = M1_DOSE_RE_SPEC

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
    n = parse_decimal(number.replace(",", ""))
    base, suffix = _split_unit(unit)
    if base in _MASS_TO_MG:
        mg = n * _MASS_TO_MG[base]
        return f"{format_decimal(mg)} mg{suffix}"
    if base in _VOL_TO_ML:
        ml = n * _VOL_TO_ML[base]
        canon = "mL" if suffix == "" else "mL"
        return f"{format_decimal(ml)} {canon}{suffix}"
    return f"{format_decimal(n)} {unit}"


def normalize_quantities(text: str, dose_re: re.Pattern | None = None) -> str:
    """Replace each dose match with canonical form; other text unchanged."""
    if not text:
        return text
    pattern = dose_re or M1_DOSE_RE

    def repl(match: re.Match) -> str:
        try:
            return canonicalize_dose_span(match.group(1), match.group(2))
        except (ValueError, InvalidOperation):
            return match.group(0)

    return pattern.sub(repl, text)


def apply_m1_pair(claim: str, evidence: str, dose_re: re.Pattern | None = None) -> tuple[str, str]:
    return normalize_quantities(claim, dose_re), normalize_quantities(evidence, dose_re)


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
