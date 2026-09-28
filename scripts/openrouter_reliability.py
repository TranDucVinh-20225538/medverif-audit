#!/usr/bin/env python3
"""Smoke (5) then repeatability (50 × 2) for V1/V4 via OpenRouter."""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl


def run_verifier(module_name: str, rows: list[dict]) -> list[str]:
    import importlib

    mod = importlib.import_module(f"verifiers.{module_name}")
    llm, tok, params, _ = mod.load()
    scored = mod.score_batch(llm, tok, params, rows)
    return [r["verdict"] for r in scored]


def main() -> None:
    os.environ.setdefault("MEDVERIF_USE_OPENROUTER", "1")
    inst = ROOT / "data" / "v3" / "instances_cpu_main.jsonl"
    all_rows = [r for r in read_jsonl(inst) if r.get("valid", True)]
    random.seed(42)

    smoke = all_rows[:5]
    for name in ("v1_medscore", "v4_ragas_nli"):
        verdicts = run_verifier(name, smoke)
        print(json.dumps({"phase": "smoke", "verifier": name, "n": len(smoke), "verdicts": verdicts}))

    pool = all_rows[:50]
    v1_a = run_verifier("v1_medscore", pool)
    v1_b = run_verifier("v1_medscore", pool)
    agree_v1 = sum(a == b for a, b in zip(v1_a, v1_b)) / max(len(pool), 1)
    v4_a = run_verifier("v4_ragas_nli", pool)
    v4_b = run_verifier("v4_ragas_nli", pool)
    agree_v4 = sum(a == b for a, b in zip(v4_a, v4_b)) / max(len(pool), 1)
    print(
        json.dumps(
            {
                "phase": "repeat50x2",
                "v1_agreement_rate": agree_v1,
                "v4_agreement_rate": agree_v4,
                "n": len(pool),
            }
        )
    )


if __name__ == "__main__":
    main()
