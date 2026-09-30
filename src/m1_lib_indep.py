"""M1-lib (independent): quantulum3 extraction + pint conversion for the M1-strong gate.

Deliberately imports nothing from this repo (no quantity_norm, text_utils or m1_lib), so the gate
compares M1 against a normalizer that shares no code with it.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from functools import lru_cache

import pint

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from quantulum3 import parser as _q3

UREG = pint.UnitRegistry()
UREG.define("dose = [dose]")
UREG.define("enzyme_unit = [enzyme_unit] = units")

# quantulum3 has no entry for the Greek/micro-sign microgram; this is the only surface rewrite.
_MICRO_SIGN = re.compile(r"[µμ]g")

_Q3_TO_PINT = {
    "cubic centimetre": "centimetre ** 3",
    "cubic decimetre": "decimetre ** 3",
    "litre": "litre",
}


@dataclass(frozen=True)
class LibQuantity:
    quantity: pint.Quantity | None
    reason: str
    micro_alias: bool


def _unit_expr(dimensions: list[dict]) -> str | None:
    parts = []
    for d in dimensions:
        base = d["base"]
        if base in ("unk", "dimensionless"):
            return None
        base = _Q3_TO_PINT.get(base, base.replace(" ", "_"))
        parts.append(f"({base}) ** {d['power']}")
    return " * ".join(parts) if parts else None


@lru_cache(maxsize=16384)
def parse_surface(surface: str) -> LibQuantity:
    text = surface.strip()
    micro = bool(_MICRO_SIGN.search(text))
    text = _MICRO_SIGN.sub("mcg", text)
    if re.search(r"\bunits?\b", text):
        m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*units?\b", text)
        if m:
            return LibQuantity(float(m.group(1).replace(",", "")) * UREG.enzyme_unit, "ok", micro)
    try:
        found = [q for q in _q3.parse(text) if q.unit.name != "dimensionless"]
    except Exception as exc:  # noqa: BLE001
        return LibQuantity(None, f"quantulum3 error: {exc}", micro)
    if not found:
        return LibQuantity(None, "no quantity extracted", micro)
    if len(found) > 1:
        return LibQuantity(None, f"{len(found)} quantities extracted", micro)
    q = found[0]
    expr = _unit_expr(q.unit.dimensions)
    if expr is None:
        return LibQuantity(None, f"unknown unit '{q.unit.name}'", micro)
    try:
        return LibQuantity(q.value * UREG(expr), "ok", micro)
    except Exception as exc:  # noqa: BLE001
        return LibQuantity(None, f"pint error: {exc}", micro)


def same_quantity(a: pint.Quantity, b: pint.Quantity, rel: float = 1e-9) -> bool:
    if a.dimensionality != b.dimensionality:
        return False
    av, bv = a.to_base_units().magnitude, b.to_base_units().magnitude
    return abs(av - bv) <= rel * max(abs(av), abs(bv), 1e-30)
