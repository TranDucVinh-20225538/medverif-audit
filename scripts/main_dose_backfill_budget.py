#!/usr/bin/env python3
"""Incremental cap for main-dose OpenRouter backfill (t2_full + t6b/full cohort files)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "notes/main_dose_backfill_baseline_usd.json"
LEDGER = ROOT / "notes/main_dose_backfill_spend.json"

SCORE_FILES = (
    ROOT / "results/raw/t2_full/v1b_medscore.jsonl",
    ROOT / "results/raw/t2_full/v5_ragas_nli.jsonl",
    ROOT / "results/raw/t6b/full/v1c_medscore.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_gpt4o_mini.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_haiku45.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_mistral_small32.jsonl",
)


def file_spend_usd(path: Path) -> float:
    if not path.is_file():
        return 0.0
    total = 0.0
    with path.open() as handle:
        for line in handle:
            if line.strip():
                total += float(json.loads(line).get("api_cost_usd") or 0)
    return total


def total_spend_usd() -> float:
    return sum(file_spend_usd(p) for p in SCORE_FILES)


def cap_usd() -> float:
    return float(os.environ.get("MEDVERIF_MAIN_DOSE_BACKFILL_CAP_USD", "4"))


def write_baseline() -> dict:
    baseline = total_spend_usd()
    payload = {"baseline_usd": baseline, "files": [p.relative_to(ROOT).as_posix() for p in SCORE_FILES]}
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def load_baseline() -> float:
    if not BASELINE.is_file():
        return write_baseline()["baseline_usd"]
    return float(json.loads(BASELINE.read_text())["baseline_usd"])


def backfill_spend_usd() -> float:
    return max(0.0, total_spend_usd() - load_baseline())


def assert_under_cap(extra: float = 0.0) -> dict:
    spent = backfill_spend_usd()
    limit = cap_usd()
    if spent + extra > limit:
        raise RuntimeError(
            f"Main-dose backfill budget exceeded: spent ${spent:.4f} + ${extra:.4f} > cap ${limit:.2f}"
        )
    out = {
        "backfill_spent_usd": round(spent, 6),
        "cap_usd": limit,
        "remaining_usd": round(limit - spent, 6),
        "baseline_usd": load_baseline(),
        "total_cohort_usd": round(total_spend_usd(), 6),
    }
    LEDGER.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps(assert_under_cap(), indent=2))
