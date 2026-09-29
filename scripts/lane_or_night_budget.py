#!/usr/bin/env python3
"""Tonight OpenRouter spend guard: baseline + cap for Lane C (total night ≤ $10)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "notes/lane_or_night_baseline.json"
LEDGER = ROOT / "notes/lane_or_night_spend.json"

GLOB_DIRS = (
    ROOT / "results/raw",
    ROOT / "results/raw/t17",
    ROOT / "results/raw/t14",
    ROOT / "results/raw/t2_full",
    ROOT / "results/raw/t6b/full",
    ROOT / "results/raw/t7",
    ROOT / "results/raw_m1",
)


def api_spend_in_file(path: Path) -> float:
    if not path.is_file():
        return 0.0
    total = 0.0
    with path.open() as handle:
        for line in handle:
            if line.strip():
                total += float(json.loads(line).get("api_cost_usd") or 0)
    return total


def total_api_spend() -> float:
    seen: set[str] = set()
    total = 0.0
    for d in GLOB_DIRS:
        if not d.is_dir():
            continue
        for path in d.rglob("*.jsonl"):
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            total += api_spend_in_file(path)
    api = ROOT / "results/api_cost.json"
    if api.is_file():
        try:
            data = json.loads(api.read_text())
            total = max(total, float(data.get("total_cost_usd") or 0))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return total


def night_cap() -> float:
    return float(os.environ.get("MEDVERIF_OR_NIGHT_CAP_USD", "10"))


def lane_c_cap() -> float:
    return float(os.environ.get("MEDVERIF_LANE_C_CAP_USD", "3"))


def ensure_baseline() -> float:
    if not BASELINE.is_file():
        b = total_api_spend()
        BASELINE.write_text(json.dumps({"baseline_usd": b, "note": "night OR guard"}, indent=2) + "\n")
        return b
    return float(json.loads(BASELINE.read_text())["baseline_usd"])


def incremental() -> float:
    return max(0.0, total_api_spend() - ensure_baseline())


def assert_lane_c_ok() -> dict:
    inc = incremental()
    night = night_cap()
    cap = lane_c_cap()
    remaining_night = night - inc
    if remaining_night <= 0:
        raise RuntimeError(f"night OR spend ${inc:.4f} >= cap ${night:.2f}")
    if cap > remaining_night:
        raise RuntimeError(
            f"Lane C cap ${cap:.2f} exceeds night remaining ${remaining_night:.2f} (inc ${inc:.4f})"
        )
    out = {
        "baseline_usd": ensure_baseline(),
        "incremental_usd": round(inc, 6),
        "night_cap_usd": night,
        "lane_c_cap_usd": cap,
        "night_remaining_usd": round(night - inc, 6),
    }
    LEDGER.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "reset-baseline":
        BASELINE.unlink(missing_ok=True)
        ensure_baseline()
    print(json.dumps(assert_lane_c_ok(), indent=2))
