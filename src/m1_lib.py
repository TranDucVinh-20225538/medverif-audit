"""M1-lib: quantulum3 quantity extraction + dimension-aware canonicalization (M1-aligned)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALIAS_LOG_PATH = ROOT / "notes/m1_lib_alias_log.jsonl"

# Explicit microgram aliases (logged when applied).
_ALIASES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"\bug\b(?=\s|$|/)", re.I), "mcg", "ug→mcg"),
    (re.compile(r"µg", re.I), "mcg", "µg→mcg"),
    (re.compile(r"μg", re.I), "mcg", "μg→mcg"),
    (re.compile(r"\bmicrograms\b", re.I), "mcg", "micrograms→mcg"),
    (re.compile(r"\bmilligrams\b", re.I), "mg", "milligrams→mg"),
    (re.compile(r"\bgrams\b", re.I), "g", "grams→g"),
)

# Fallback extractor (NOT src/text_utils.DOSE_RE); used only if quantulum3 missing.
_HEURISTIC = re.compile(
    r"(?<![\w.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"([a-zA-Zµμ]+(?:/[a-zA-Zµμ]+(?:/[a-zA-Zµμ]+)?)?)(?![\w/])"
)


@dataclass
class LibSpan:
    surface: str
    start: int
    end: int
    canonical_mg: str | None
    parsed: bool


def _log_alias(fix: str, before: str, after: str) -> None:
    ALIAS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ALIAS_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps({"fix": fix, "before": before[:200], "after": after[:200]}, ensure_ascii=False)
            + "\n"
        )


def apply_unit_aliases(text: str) -> str:
    out = text
    for pat, repl, label in _ALIASES:
        if pat.search(out):
            new = pat.sub(repl, out)
            if new != out:
                _log_alias(label, out, new)
                out = new
    return out


def _canonical_for_gate(surface: str) -> str | None:
    """Same canonical dose token as M1 (mass→mg, volume→mL, mg/kg, /day, /dose)."""
    from quantity_norm import canonicalize_dose_span  # noqa: PLC0415
    from text_utils import DOSE_RE  # noqa: PLC0415

    s = apply_unit_aliases(surface.strip())
    m = DOSE_RE.search(s)
    if not m:
        m = _HEURISTIC.search(s)
        if not m:
            return None
        num, unit = m.group(1), m.group(2).strip()
    else:
        num, unit = m.group(1), m.group(2)
    try:
        return canonicalize_dose_span(num, unit)
    except Exception as exc:
        from m1_parse_errors import log_parse_error  # noqa: PLC0415

        log_parse_error("m1_lib.canonical", surface.strip(), exc)
        return None


def _extract_quantulum(text: str) -> list[tuple[int, int, str]]:
    from quantulum3 import parser as qp  # noqa: PLC0415

    out: list[tuple[int, int, str]] = []
    for q in qp.parse(text):
        if q.span is None:
            continue
        start, end = q.span
        surface = text[start:end]
        out.append((start, end, surface))
    return out


def _extract_heuristic(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0)) for m in _HEURISTIC.finditer(text)]


@lru_cache(maxsize=8192)
def extract_lib_spans(text: str) -> tuple[LibSpan, ...]:
    text = apply_unit_aliases(text or "")
    try:
        raw = _extract_quantulum(text)
    except ImportError:
        raw = _extract_heuristic(text)
    spans: list[LibSpan] = []
    for start, end, surface in raw:
        canon = _canonical_for_gate(surface)
        spans.append(
            LibSpan(surface=surface, start=start, end=end, canonical_mg=canon, parsed=canon is not None)
        )
    return tuple(spans)


def m1_regex_spans(text: str, dose_re: re.Pattern) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0)) for m in dose_re.finditer(text or "")]


@lru_cache(maxsize=8192)
def intersection_spans(text: str) -> tuple[str, ...]:
    """Surfaces parseable by both M1 regex canonicalization and M1-lib."""
    from quantity_norm import canonicalize_dose_span  # noqa: PLC0415

    m1_ok: set[str] = set()
    from text_utils import DOSE_RE as dose_re  # noqa: PLC0415

    for _s, _e, surf in m1_regex_spans(text, dose_re):
        m = dose_re.search(surf)
        if not m:
            continue
        try:
            canonicalize_dose_span(m.group(1), m.group(2))
            m1_ok.add(surf.strip().lower())
        except Exception as exc:
            from m1_parse_errors import log_parse_error  # noqa: PLC0415

            log_parse_error("m1.intersection_spans", surf, exc)
            continue
    lib_ok: set[str] = set()
    for sp in extract_lib_spans(text):
        if sp.parsed:
            lib_ok.add(sp.surface.strip().lower())
    both = m1_ok & lib_ok
    return tuple(sorted(both))


def edited_span_surfaces(row: dict) -> list[str]:
    diff = row.get("diff") or {}
    out: list[str] = []
    for side in ("claim", "evidence"):
        block = diff.get(side)
        if isinstance(block, dict):
            for key in ("span_before", "span_after"):
                s = block.get(key)
                if s:
                    out.append(str(s))
    for key in ("claim_span", "evidence_span"):
        if row.get(key):
            out.append(str(row[key]))
    return out


def m1_canonical_mg_for_surface(surface: str) -> str | None:
    return _canonical_for_gate(surface)


def lib_canonical_mg_for_surface(surface: str) -> str | None:
    return _canonical_for_gate(surface)


def instance_in_intersection(row: dict, dose_re: re.Pattern | None = None) -> bool:
    from m1_gate import instance_gate  # noqa: PLC0415

    ok, _ = instance_gate(row)
    return ok
