#!/usr/bin/env python3
"""T14 OpenRouter incremental cap (default $2 on resume baseline)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw" / "t14"
BASELINE = ROOT / "notes/t14_or_resume_baseline_usd.json"
LEDGER = ROOT / "notes/t14_or_resume_spend.json"


def t14_spend_usd() -> float:
    total = 0.0
    if not RAW.is_dir():
        return 0.0
    for path in RAW.glob("*.jsonl"):
        with path.open() as handle:
            for line in handle:
                if line.strip():
                    total += float(json.loads(line).get("api_cost_usd") or 0)
    return total


def cap() -> float:
    return float(os.environ.get("MEDVERIF_T14_BUDGET_USD", "2"))


def write_baseline() -> dict:
    baseline = t14_spend_usd()
    payload = {"baseline_usd": baseline, "dir": str(RAW.relative_to(ROOT))}
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def load_baseline() -> float:
    if not BASELINE.is_file():
        return write_baseline()["baseline_usd"]
    return float(json.loads(BASELINE.read_text())["baseline_usd"])


def incremental_spend_usd() -> float:
    return max(0.0, t14_spend_usd() - load_baseline())


def assert_under_cap(extra: float = 0.0) -> dict:
    spent = incremental_spend_usd()
    limit = cap()
    if spent + extra > limit:
        raise RuntimeError(
            f"T14 resume budget exceeded: incremental ${spent:.4f} + ${extra:.4f} > cap ${limit:.2f}"
        )
    out = {
        "incremental_spent_usd": round(spent, 6),
        "cap_usd": limit,
        "remaining_usd": round(limit - spent, 6),
        "baseline_usd": load_baseline(),
        "total_t14_usd": round(t14_spend_usd(), 6),
    }
    LEDGER.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps(assert_under_cap(), indent=2))
