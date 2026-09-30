"""T14 quantity-representation invariance (claim-side, span-local, rule-based)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Callable, List, Optional, Tuple

from text_utils import highlight, levenshtein, outside_identical, replace_span

CONDITION = "T14-repr-claim"
MAG_UNIT = "unit_spell"
MAG_THOUS = "thousands_sep"
MAG_SPACING = "spacing"
MAG_SYMBOL = "symbol_micro"
MAG_SYMBOL_UNICODE = "symbol_micro_unicode"

MICRO_SIGN = "\u00b5"  # µ
GREEK_MU = "\u03bc"  # μ

_NUM_BEFORE = re.compile(r"(\d+(?:\.\d+)?)\s*$")

_THOUS_COMMA = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+)(?![\d.])")
_THOUS_PLAIN = re.compile(r"(?<![\d.])(\d{4,})(?![\d.])")

_SPACE_BEFORE_UNIT = re.compile(
    r"(\d+(?:\.\d+)?)\s+(mg|g|mcg|µg|μg|mL|ml|milligrams|grams|micrograms|milliliters)\b",
    re.I,
)
_COMPACT_DOSE = re.compile(r"(\d+(?:\.\d+)?)(mg|g|mcg|µg|μg|mL|ml)\b", re.I)
_MICRO_TOKEN = re.compile(r"\b(mcg|µg|μg)\b")
_UNICODE_MICRO = re.compile(r"(\d+(?:\.\d+)?)\s*([µμ])g\b")

_SPELL_SINGULAR = {
    "milligrams": "milligram",
    "grams": "gram",
    "micrograms": "microgram",
    "milliliters": "milliliter",
    "milligrams per kilogram": "milligram per kilogram",
    "micrograms per kilogram": "microgram per kilogram",
}


def _numeral_before(span: str, unit_start: int) -> Optional[str]:
    prefix = span[:unit_start]
    m = _NUM_BEFORE.search(prefix)
    return m.group(1) if m else None


def _is_exactly_one(numeral: Optional[str]) -> bool:
    if numeral is None:
        return False
    try:
        return Decimal(numeral) == 1
    except Exception:
        return False


def _spelled_form(plural_word: str, numeral: Optional[str]) -> str:
    if _is_exactly_one(numeral):
        return _SPELL_SINGULAR.get(plural_word.lower(), plural_word)
    return plural_word


def _claim_diff(base: dict, new_span: str, family: str) -> dict:
    claim0 = base["claim"]
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    edited = replace_span(claim0, c0, c1, new_span)
    return {
        "family": family,
        "where": "claim",
        "span_before": claim0[c0:c1],
        "span_after": new_span,
        "edit_distance": levenshtein(claim0, edited),
        "confined_to_span": outside_identical(claim0, edited, c0, c1, new_span),
        "highlight_before": highlight(claim0, c0, c1),
        "highlight_after": highlight(edited, c0, c0 + len(new_span)),
        "text": edited,
    }


def _instance(base: dict, magnitude: str, claim: str, diff: dict, claim_span: str) -> dict:
    evid0 = base["evidence"]
    e0, e1 = base["evidence_span_start"], base["evidence_span_end"]
    return {
        "instance_id": f"{base['id']}__{CONDITION}__{magnitude}",
        "base_id": base["id"],
        "type": base["type"],
        "condition": CONDITION,
        "magnitude": magnitude,
        "claim": claim,
        "evidence": evid0,
        "expected_verdict": "PASS",
        "claim_span": claim_span,
        "evidence_span": evid0[e0:e1],
        "claim_c0": base["claim"],
        "evidence_c0": evid0,
        "diff": {"claim": diff},
        "t14_family": diff.get("family", magnitude),
        "dose_kind": base.get("dose_kind"),
        "subset": base.get("subset", "main"),
        "valid": True,
    }


def _sub_once(span: str, pat: re.Pattern, repl_builder: Callable[[re.Match], str]) -> Optional[str]:
    m = pat.search(span)
    if not m:
        return None
    repl = repl_builder(m)
    if not repl or repl.lower() == m.group(0).lower():
        return None
    return span[: m.start()] + repl + span[m.end() :]


def _try_unit_spell(span: str) -> Optional[str]:
    rules: List[Tuple[re.Pattern, Callable[[re.Match, str], Optional[str]]]] = [
        (
            re.compile(r"\bmg/kg\b", re.I),
            lambda m, s: "mg/kg"
            if m.group(0).lower().startswith("milli")
            else _spelled_form(
                "milligrams per kilogram", _numeral_before(s, m.start())
            ),
        ),
        (
            re.compile(r"\bmilligrams per kilogram\b", re.I),
            lambda m, s: "mg/kg",
        ),
        (
            re.compile(r"\bmcg/kg\b", re.I),
            lambda m, s: _spelled_form(
                "micrograms per kilogram", _numeral_before(s, m.start())
            ),
        ),
        (
            re.compile(r"\bmicrograms per kilogram\b", re.I),
            lambda m, s: "mcg/kg",
        ),
        (
            re.compile(r"\b(?:mcg|µg|μg)\b"),
            lambda m, s: _spelled_form("micrograms", _numeral_before(s, m.start())),
        ),
        (
            re.compile(r"\bmicrograms\b", re.I),
            lambda m, s: "mcg",
        ),
        (
            re.compile(r"\bmg\b"),
            lambda m, s: _spelled_form("milligrams", _numeral_before(s, m.start())),
        ),
        (
            re.compile(r"\bmilligrams\b", re.I),
            lambda m, s: "mg",
        ),
        (
            re.compile(r"\b(?:mL|ml)\b"),
            lambda m, s: _spelled_form("milliliters", _numeral_before(s, m.start())),
        ),
        (
            re.compile(r"\bmilliliters\b", re.I),
            lambda m, s: "mL",
        ),
        (
            re.compile(r"\bg\b"),
            lambda m, s: _spelled_form("grams", _numeral_before(s, m.start())),
        ),
        (
            re.compile(r"\bgrams\b", re.I),
            lambda m, s: "g",
        ),
    ]
    for pat, fn in rules:
        out = _sub_once(span, pat, lambda m, p=pat, f=fn: f(m, span))
        if out:
            return out
    return None


def _try_thousands(span: str) -> Optional[str]:
    m = _THOUS_COMMA.search(span)
    if m:
        plain = m.group(1).replace(",", "")
        if int(plain) >= 1000:
            return span[: m.start(1)] + plain + span[m.end(1) :]
    m = _THOUS_PLAIN.search(span)
    if m:
        val = int(m.group(1))
        if val >= 1000:
            formatted = f"{val:,}"
            return span[: m.start(1)] + formatted + span[m.end(1) :]
    return None


def _try_spacing(span: str) -> Optional[str]:
    m = _SPACE_BEFORE_UNIT.search(span)
    if m:
        return span[: m.start()] + m.group(1) + m.group(2) + span[m.end() :]
    m = _COMPACT_DOSE.search(span)
    if m:
        return span[: m.start()] + m.group(1) + " " + m.group(2) + span[m.end() :]
    return None


def _try_symbol_micro(span: str) -> Optional[str]:
    m = _MICRO_TOKEN.search(span)
    if not m:
        return None
    token = m.group(1)
    if token.lower() == "mcg":
        nxt = f"{MICRO_SIGN}g"
    elif token.startswith(MICRO_SIGN):
        nxt = "mcg"
    elif token.startswith(GREEK_MU):
        nxt = "mcg"
    else:
        return None
    return span[: m.start()] + nxt + span[m.end() :]


def _try_symbol_unicode(span: str) -> Optional[str]:
    m = _UNICODE_MICRO.search(span)
    if not m:
        return None
    sign = m.group(2)
    if sign == MICRO_SIGN:
        nxt = f"{m.group(1)} {GREEK_MU}g"
    elif sign == GREEK_MU:
        nxt = f"{m.group(1)} {MICRO_SIGN}g"
    else:
        return None
    before = span[m.start() : m.end()]
    after_part = nxt.split()[-1] if " " in nxt else nxt
    if before.encode("utf-8") == after_part.encode("utf-8"):
        raise AssertionError(f"unicode micro swap must change codepoints: {before!r}")
    return span[: m.start()] + nxt + span[m.end() :]


def appendix_symbol_unicode_for_base(base: dict) -> Optional[dict]:
    """Appendix-only µ vs μ (not in main scored pack)."""
    claim0 = base["claim"]
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    span = claim0[c0:c1]
    new_span = _try_symbol_unicode(span)
    if not new_span or new_span == span:
        return None
    diff = _claim_diff(base, new_span, MAG_SYMBOL_UNICODE)
    return _instance(base, MAG_SYMBOL_UNICODE, diff["text"], diff, new_span)


def build_for_base(base: dict) -> Tuple[List[dict], List[dict]]:
    failures: List[dict] = []
    out: List[dict] = []
    if base.get("type") != "DOSE":
        failures.append({"base_id": base["id"], "reason": "not_dose"})
        return out, failures
    claim0 = base["claim"]
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    span = claim0[c0:c1]
    if span != (base.get("target_span_claim") or span):
        if normalize_span(span) != normalize_span(base.get("target_span_claim") or ""):
            failures.append({"base_id": base["id"], "reason": "claim_span_mismatch"})
            return out, failures

    builders: List[Tuple[str, Callable[[str], Optional[str]]]] = [
        (MAG_UNIT, _try_unit_spell),
        (MAG_SPACING, _try_spacing),
        (MAG_SYMBOL, _try_symbol_micro),
    ]
    for magnitude, fn in builders:
        new_span = fn(span)
        if not new_span or new_span == span:
            continue
        diff = _claim_diff(base, new_span, magnitude)
        edited = diff["text"]
        out.append(
            _instance(
                base,
                magnitude,
                edited,
                diff,
                new_span,
            )
        )
    return out, failures


def normalize_span(text: str) -> str:
    return " ".join(text.split())
