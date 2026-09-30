#!/usr/bin/env python3
"""T18 OpenRouter incremental cap (default $2)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/raw/t18"
BASELINE = ROOT / "notes/t18_or_baseline_usd.json"


def spend_usd() -> float:
    total = 0.0
    if not RAW.is_dir():
        return 0.0
    for path in RAW.glob("*.jsonl"):
        for line in path.open():
            if line.strip():
                total += float(json.loads(line).get("api_cost_usd") or 0)
    return total


def cap() -> float:
    return float(os.environ.get("MEDVERIF_T18_BUDGET_USD", "2"))


def load_baseline() -> float:
    if not BASELINE.is_file():
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps({"baseline_usd": spend_usd()}, indent=2) + "\n")
    return float(json.loads(BASELINE.read_text())["baseline_usd"])


def assert_under_cap() -> dict:
    inc = max(0.0, spend_usd() - load_baseline())
    c = cap()
    if inc >= c:
        raise RuntimeError(f"T18 OR spend ${inc:.4f} >= cap ${c:.2f}")
    return {"incremental_usd": inc, "cap_usd": c, "remaining_usd": c - inc}


if __name__ == "__main__":
    print(json.dumps(assert_under_cap(), indent=2))
