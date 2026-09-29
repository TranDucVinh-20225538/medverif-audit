#!/usr/bin/env python3
"""Lane A generation spend cap ($2 default)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "notes/lane_a_spend.json"


def cap() -> float:
    return float(os.environ.get("MEDVERIF_LANE_A_CAP_USD", "2"))


def spent() -> float:
    if not LEDGER.is_file():
        return 0.0
    return float(json.loads(LEDGER.read_text()).get("spent_usd") or 0)


def record(delta: float, *, phase: str) -> dict:
    total = spent() + float(delta)
    payload = {"spent_usd": round(total, 6), "last_phase": phase, "cap_usd": cap()}
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(payload, indent=2) + "\n")
    if total > cap():
        raise RuntimeError(f"Lane A spend ${total:.4f} > cap ${cap():.2f}")
    return payload


def assert_ok() -> dict:
    total = spent()
    if total >= cap():
        raise RuntimeError(f"Lane A spend ${total:.4f} >= cap ${cap():.2f}")
    return {"spent_usd": total, "cap_usd": cap(), "remaining_usd": cap() - total}


if __name__ == "__main__":
    import sys

    print(json.dumps(assert_ok(), indent=2))
