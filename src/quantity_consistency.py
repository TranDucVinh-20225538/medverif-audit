"""M2: numeric dose consistency between claim and evidence after M1 normalization."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple

from quantity_norm import normalize_quantities
from text_utils import DOSE_RE, parse_decimal


QuantityKey = Tuple[Decimal, str]


def _extract_quantities(text: str) -> List[QuantityKey]:
    text = normalize_quantities(text or "")
    out: List[QuantityKey] = []
    for match in DOSE_RE.finditer(text):
        try:
            n = parse_decimal(match.group(1))
            unit = match.group(2)
            out.append((n, unit))
        except ValueError:
            continue
    return sorted(out, key=lambda x: (x[1], x[0]))


def quantities_consistent(claim: str, evidence: str) -> bool:
    """True if normalized (value, unit) multisets match; True when neither side has doses."""
    cq = _extract_quantities(claim)
    eq = _extract_quantities(evidence)
    if not cq and not eq:
        return True
    return cq == eq


def m2_verdict(verifier_verdict: str, claim: str, evidence: str) -> str:
    """Veto: PASS only if verifier PASS and quantities consistent."""
    if verifier_verdict != "PASS":
        return verifier_verdict
    if not quantities_consistent(claim, evidence):
        return "FAIL"
    return "PASS"
