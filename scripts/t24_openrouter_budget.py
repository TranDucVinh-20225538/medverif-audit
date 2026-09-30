#!/usr/bin/env python3
"""T24 OpenRouter incremental cap (default $2)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "notes/t24_or_baseline_usd.json"
COST = ROOT / "results/api_cost.json"


def total_usd() -> float:
    if not COST.is_file():
        return 0.0
    try:
        doc = json.loads(COST.read_text())
        return float(doc.get("total_cost_usd") or doc.get("total_usd") or 0.0)
    except json.JSONDecodeError:
        return 0.0


def cap() -> float:
    return float(os.environ.get("MEDVERIF_T24_CAP_USD", "2"))


def load_baseline() -> float:
    if not BASELINE.is_file():
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps({"baseline_usd": total_usd()}, indent=2) + "\n")
    return float(json.loads(BASELINE.read_text())["baseline_usd"])


def assert_under_cap() -> dict:
    inc = max(0.0, total_usd() - load_baseline())
    c = cap()
    if inc >= c:
        raise RuntimeError(f"T24 OR spend ${inc:.4f} >= cap ${c:.2f}")
    return {"incremental_usd": inc, "cap_usd": c, "remaining_usd": c - inc}


if __name__ == "__main__":
    print(json.dumps(assert_under_cap(), indent=2))
