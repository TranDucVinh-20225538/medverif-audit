"""M1-strong gate: edited target spans must match under M1 and M1-lib."""

from __future__ import annotations

from dataclasses import dataclass

from m1_lib import edited_span_surfaces, lib_canonical_mg_for_surface, m1_canonical_mg_for_surface
from text_utils import parse_decimal


@dataclass(frozen=True)
class SpanGateResult:
    surface: str
    m1_ok: bool
    lib_ok: bool
    both_ok: bool
    m1_mg: str | None
    lib_mg: str | None


def _norm_surface(s: str) -> str:
    return s.strip().replace("«", "").replace("»", "").strip()


def target_span_gate(surface: str) -> SpanGateResult:
    s = _norm_surface(surface)
    m1_mg = m1_canonical_mg_for_surface(s)
    lib_mg = lib_canonical_mg_for_surface(s)
    m1_ok = m1_mg is not None
    lib_ok = lib_mg is not None
    both_ok = bool(m1_ok and lib_ok and m1_mg == lib_mg)
    return SpanGateResult(s, m1_ok, lib_ok, both_ok, m1_mg, lib_mg)


def instance_gate(row: dict) -> tuple[bool, list[SpanGateResult]]:
    targets = [_norm_surface(x) for x in edited_span_surfaces(row) if x and x.strip()]
    if not targets:
        return False, []
    seen: set[str] = set()
    results: list[SpanGateResult] = []
    for s in targets:
        if s in seen:
            continue
        seen.add(s)
        results.append(target_span_gate(s))
    ok = all(r.both_ok for r in results)
    return ok, results


def pack_coverage(rows: list[dict]) -> dict:
    """Per-pack edited-span counts: M1-only, M1-lib-only, both."""
    m1_only = lib_only = both = 0
    targets_n = 0
    inst_pass = 0
    for row in rows:
        ok, spans = instance_gate(row)
        if ok:
            inst_pass += 1
        for r in spans:
            targets_n += 1
            if r.both_ok:
                both += 1
            elif r.m1_ok:
                m1_only += 1
            elif r.lib_ok:
                lib_only += 1
    return {
        "instances": len(rows),
        "instances_gate_pass": inst_pass,
        "edited_target_spans": targets_n,
        "spans_m1_only": m1_only,
        "spans_m1_lib_only": lib_only,
        "spans_both": both,
    }
