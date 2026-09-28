#!/usr/bin/env python3
"""Rerun 50 random main instances twice; report V1 verdict agreement."""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("MEDVERIF_USE_OPENROUTER", "1")

from verifiers import v1_medscore
from verifiers.io_utils import read_jsonl


def main() -> None:
    rows = [r for r in read_jsonl(ROOT / "data" / "v3" / "instances_cpu_main.jsonl") if r.get("valid", True)]
    random.seed(42)
    sample = random.sample(rows, min(50, len(rows)))
    llm, tok, params, _ = v1_medscore.load()
    a = v1_medscore.score_batch(llm, tok, params, sample)
    b = v1_medscore.score_batch(llm, tok, params, sample)
    va = {r["instance_id"]: r["verdict"] for r in a}
    vb = {r["instance_id"]: r["verdict"] for r in b}
    agree = sum(va[i] == vb[i] for i in va) / max(len(va), 1)
    out = {"n": len(sample), "agreement_rate": agree, "verifier": "v1_medscore"}
    path = ROOT / "notes" / "v1_agreement_50x2.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
