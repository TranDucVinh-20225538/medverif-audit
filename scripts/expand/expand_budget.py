#!/usr/bin/env python3
"""Stop expansion OpenRouter spend when cap in notes/expand_budget.json is reached."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "notes" / "expand_budget.json"
LEDGER = ROOT / "data" / "expand" / "stage1" / "api_spend.jsonl"


class ExpandBudgetStop(RuntimeError):
    pass


def cap_usd() -> float:
    if NOTES.is_file():
        data = json.loads(NOTES.read_text())
        return float(data.get("cap_usd", 30))
    return float(os.environ.get("MEDVERIF_EXPAND_BUDGET_USD", "30"))


def spent_usd() -> float:
    if not LEDGER.is_file():
        return 0.0
    total = 0.0
    with LEDGER.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                total += float(json.loads(line).get("cost_usd") or 0)
    return total


def record_cost(cost: float | None, *, cand_id: str, phase: str) -> None:
    if cost is None:
        return
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {"cand_id": cand_id, "phase": phase, "cost_usd": float(cost)}
    with LEDGER.open("a") as handle:
        handle.write(json.dumps(row) + "\n")


def assert_ok() -> dict:
    cap = cap_usd()
    spent = spent_usd()
    if spent >= cap:
        raise ExpandBudgetStop(f"expand spend ${spent:.4f} >= cap ${cap:.2f}")
    return {"cap_usd": cap, "spent_usd": spent, "remaining_usd": cap - spent}


if __name__ == "__main__":
    print(json.dumps(assert_ok(), indent=2))
