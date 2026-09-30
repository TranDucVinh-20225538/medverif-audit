"""M1 dose-span coverage and failure taxonomy for instance packs."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from decimal import InvalidOperation
from pathlib import Path

from text_utils import DOSE_RE, parse_decimal
from quantity_norm import _MASS_TO_MG, _VOL_TO_ML, _split_unit, canonicalize_dose_span

RANGE_RE = re.compile(
    r"\b\d+\s*[-–—]\s*\d+\s*(?:mg|g|mcg|µg|μg|ug|mL|ml|L)\b",
    re.I,
)


def _supported_unit(unit: str) -> bool:
    base, _ = _split_unit(unit)
    return base in _MASS_TO_MG or base in _VOL_TO_ML


def classify_span(text: str, span: str, field: str) -> tuple[str, str]:
    """Return (category, verbatim_snippet)."""
    snippet = span.strip()[:120]
    ctx_start = max(0, text.find(span) - 40)
    ctx = text[ctx_start : ctx_start + 160].replace("\n", " ")
    if RANGE_RE.search(span) or RANGE_RE.search(text[max(0, text.find(span) - 5) : text.find(span) + len(span) + 5]):
        return "range", ctx
    m = DOSE_RE.search(span)
    if not m:
        return "parse_error", ctx
    try:
        n = parse_decimal(m.group(1))
        unit = m.group(2)
    except (ValueError, InvalidOperation):
        return "parse_error", ctx
    if "/kg" in unit.lower() or "/day" in unit.lower() or "/d" in unit.lower():
        return "per_kg_per_day", ctx
    if not _supported_unit(unit):
        return "unsupported_unit", ctx
    try:
        canonicalize_dose_span(m.group(1), m.group(2))
    except (ValueError, InvalidOperation):
        return "parse_error", ctx
    if n < 0:
        return "parse_error", ctx
    return "ok", ctx


def audit_pack_instances(rows: list[dict]) -> dict:
    total = 0
    parsed_ok = 0
    cats: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for row in rows:
        for field in ("claim", "evidence"):
            text = row.get(field) or ""
            for m in DOSE_RE.finditer(text):
                total += 1
                span = m.group(0)
                cat, ctx = classify_span(text, span, field)
                if cat == "ok":
                    parsed_ok += 1
                else:
                    cats[cat] += 1
                    examples.setdefault(cat, ctx)
    return {
        "dose_spans": total,
        "m1_parsable": parsed_ok,
        "coverage_pct": (100.0 * parsed_ok / total) if total else None,
        "failure_counts": dict(cats),
        "failure_examples": examples,
    }
