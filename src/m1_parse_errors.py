"""Counted M1 / M1-lib parse failures (no silent swallow)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "logs/m1_parse_errors.jsonl"
MAX_ERROR_RATE = 0.05

_current_pack = "unknown"
_span_total: dict[str, int] = defaultdict(int)
_error_total: dict[str, int] = defaultdict(int)


def set_pack(name: str) -> None:
    global _current_pack
    _current_pack = name or "unknown"


def note_span(pack: str | None = None) -> None:
    _span_total[pack or _current_pack] += 1


def log_parse_error(component: str, surface: str, exc: BaseException, *, pack: str | None = None) -> None:
    pk = pack or _current_pack
    _error_total[pk] += 1
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "pack": pk,
                    "component": component,
                    "exc_type": type(exc).__name__,
                    "surface": (surface or "")[:300],
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def finalize_and_abort(*, label: str = "m1-strong", abort_packs: frozenset[str] | None = None) -> None:
    """Print per-pack error totals; exit 2 if any pack exceeds MAX_ERROR_RATE."""
    packs = sorted(set(_span_total) | set(_error_total))
    print(f"[{label}] parse error summary (>{MAX_ERROR_RATE:.0%} aborts):", flush=True)
    failed = False
    for pk in packs:
        spans = _span_total.get(pk, 0)
        errs = _error_total.get(pk, 0)
        rate = (errs / spans) if spans else 0.0
        print(f"  pack={pk} spans={spans} errors={errs} rate={rate:.4f}", flush=True)
        if abort_packs is not None and pk not in abort_packs:
            continue
        if spans and rate > MAX_ERROR_RATE:
            failed = True
    if failed:
        print(f"[{label}] ABORT: parse error rate > {MAX_ERROR_RATE:.0%} in at least one pack", flush=True)
        sys.exit(2)
