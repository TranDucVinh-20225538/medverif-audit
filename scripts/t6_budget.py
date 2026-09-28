#!/usr/bin/env python3
"""T6-B spend cap (default $10)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw" / "t6b"


def t6_spend_usd() -> float:
    total = 0.0
    if not RAW.is_dir():
        return 0.0
    for path in RAW.rglob("*.jsonl"):
        with path.open() as handle:
            for line in handle:
                if line.strip():
                    total += float(json.loads(line).get("api_cost_usd") or 0)
    return total


def cap() -> float:
    return float(os.environ.get("MEDVERIF_T6B_BUDGET_USD", "10"))


def assert_under_cap(extra: float = 0.0) -> dict:
    spent = t6_spend_usd()
    limit = cap()
    if spent + extra > limit:
        raise RuntimeError(f"T6-B budget exceeded: spent ${spent:.4f} cap ${limit:.2f}")
    return {"spent_usd": spent, "cap_usd": limit, "remaining_usd": limit - spent}


if __name__ == "__main__":
    print(json.dumps(assert_under_cap(), indent=2))
