"""Load human-verified QVC items from bundled JSONL (export via scripts/qvc_export_data.py)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PKG = Path(__file__).resolve().parent
BUNDLE = PKG / "bundled"


def _read(name: str) -> list[dict[str, Any]]:
    path = BUNDLE / name
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def load_inv_unit(*, natural_only: bool = False) -> list[dict]:
    rows = _read("inv_unit.jsonl")
    if natural_only:
        rows = [r for r in rows if r.get("natural_unit")]
    return rows


def load_e1_x2() -> list[dict]:
    return _read("e1_x2.jsonl")


def load_e1_x10() -> list[dict]:
    return _read("e1_x10.jsonl")


def load_e1_unit_t7() -> list[dict]:
    return _read("e1_unit_t7.jsonl")


def load_inv_frequency_route() -> list[dict]:
    return _read("inv_frequency_route.jsonl")


def load_pol_flips() -> list[dict]:
    return _read("pol_flips.jsonl")
