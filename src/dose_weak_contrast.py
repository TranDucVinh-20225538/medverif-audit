"""Rule-based weak E1 contrast flags (robustness subset; do not drop from main analysis)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple

from text_utils import DOSE_RE, parse_decimal

THRESHOLD_RE = re.compile(
    r"(?:or\s+higher|or\s+more|or\s+greater|or\s+above|"
    r"at\s+least|up\s+to|no\s+more\s+than|"
    r"≥|>=|above|below|under|over|"
    r"at\s+doses?\s+of|doses?\s+of\s+\d|"
    r"maximum|minimum|not\s+exceed)",
    re.I,
)

PK_DESCRIPTIVE_RE = re.compile(
    r"(?:peak\s+(?:plasma|concentration|level|plasma\s+level)|"
    r"half[- ]?life|bioavailability|"
    r"acts\s+for|duration\s+of\s+(?:action|unconsciousness)|"
    r"reaches?\s+(?:its\s+)?(?:highest|peak|maximum)|"
    r"plasma\s+levels?\s+(?:are\s+)?reached|"
    r"elimination\s+half|context[- ]sensitive\s+half|"
    r"pharmacokinetic|dose[- ]response\s+curve)",
    re.I,
)

RANGE_RE = re.compile(
    r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*[-–—]\s*"
    r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"(mg|mcg|µg|μg|g|mL|ml|L|units?|micrograms?|milligrams?|grams?)",
    re.I,
)


def _dose_number_unit(text: str) -> Optional[Tuple[Decimal, str]]:
    m = DOSE_RE.search(text.strip())
    if not m:
        return None
    try:
        return parse_decimal(m.group(1)), m.group(2)
    except ValueError:
        return None


def _all_dose_mg_equiv(text: str) -> List[Decimal]:
    out: List[Decimal] = []
    for m in DOSE_RE.finditer(text or ""):
        try:
            n = parse_decimal(m.group(1))
            out.append(n)
        except ValueError:
            continue
    return out


def _in_numeric_range(value: Decimal, lo: Decimal, hi: Decimal) -> bool:
    return lo <= value <= hi


def edited_value_within_evidence_range(inst: dict) -> bool:
    """True if scaled dose in claim still falls in a dose range stated in evidence."""
    claim = inst.get("claim") or ""
    evidence = inst.get("evidence") or ""
    edited = _dose_number_unit(inst.get("claim_span") or "")
    if edited is None:
        return False
    val, unit = edited
    unit_pat = re.escape(unit)
    for m in RANGE_RE.finditer(evidence):
        u = m.group(3)
        if u.lower() != unit.lower() and not (u.lower().startswith("mg") and unit.lower() == "mg"):
            continue
        try:
            lo = parse_decimal(m.group(1))
            hi = parse_decimal(m.group(2))
        except ValueError:
            continue
        if _in_numeric_range(val, lo, hi):
            return True
    unit_key = unit.lower().split("/")[0]
    nums: List[Decimal] = []
    for m in DOSE_RE.finditer(evidence):
        u = m.group(2).lower()
        if not (u == unit.lower() or u.startswith(unit_key)):
            continue
        try:
            nums.append(parse_decimal(m.group(1)))
        except ValueError:
            continue
    if len(nums) >= 2 and min(nums) <= val <= max(nums):
        return True
    return False


def threshold_context(claim: str, span: str = "") -> bool:
    text = claim or ""
    if not text:
        return False
    if THRESHOLD_RE.search(text):
        return True
    if span and THRESHOLD_RE.search(text[max(0, text.find(span) - 40) : text.find(span) + len(span) + 40]):
        return True
    return False


def pk_descriptive_sentence(claim: str) -> bool:
    return bool(PK_DESCRIPTIVE_RE.search(claim or ""))


def weak_e1_contrast_reasons(inst: dict) -> List[str]:
    if inst.get("type") != "DOSE":
        return []
    if inst.get("condition") not in ("E1-claim", "E1-evid", "E2"):
        return []
    if inst.get("magnitude") not in ("x2", "x10"):
        return []
    claim = inst.get("claim") or ""
    span = inst.get("claim_span") or ""
    reasons: List[str] = []
    if threshold_context(claim, span):
        reasons.append("threshold_context")
    if pk_descriptive_sentence(claim):
        reasons.append("pk_descriptive")
    if edited_value_within_evidence_range(inst):
        reasons.append("within_evidence_range")
    return reasons


def flag_weak_e1_contrast(inst: dict) -> dict:
    reasons = weak_e1_contrast_reasons(inst)
    inst = dict(inst)
    if reasons:
        inst["weak_e1_contrast"] = True
        inst["weak_e1_contrast_reasons"] = reasons
    else:
        inst.pop("weak_e1_contrast", None)
        inst.pop("weak_e1_contrast_reasons", None)
    return inst
