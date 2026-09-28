#!/usr/bin/env python3
"""Smoke N V4 OpenRouter items; print 3 raw JSON examples for QC."""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl
from verifiers.v4_ragas_nli import load, score_batch


def main() -> None:
    n = int(os.environ.get("MEDVERIF_V4_SMOKE_N", "20"))
    rows = [r for r in read_jsonl(ROOT / "data" / "v3" / "instances_cpu_main.jsonl") if r.get("valid", True)]
    random.seed(42)
    sample = random.sample(rows, min(n, len(rows)))
    engine, tok, params, _ = load()
    scored = score_batch(engine, tok, params, sample)
    parsed = sum(1 for r in scored if r["verdict"] not in ("PARSE_FAIL",))
    rate = parsed / max(len(scored), 1)
    print(json.dumps({"n": len(scored), "parse_rate": rate, "model": os.environ.get("MEDVERIF_V4_OPENROUTER_MODEL")}))
    for ex in scored[:3]:
        print("--- raw example ---")
        print(json.dumps({"instance_id": ex["instance_id"], "verdict": ex["verdict"], "raw_output": ex["raw_output"][:2000]}, indent=2))


if __name__ == "__main__":
    main()
