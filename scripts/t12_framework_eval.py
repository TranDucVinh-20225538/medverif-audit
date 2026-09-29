#!/usr/bin/env python3
"""T12 pilot/full framework eval (RAGAS / DeepEval / TruLens defaults via registry)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notes/t12_qvc_cards.json"
RAW = ROOT / "results/raw/t12"
PILOT_N = 20


def main() -> None:
    mode = "pilot" if "--pilot" in sys.argv else "full"
    n = PILOT_N if mode == "pilot" else 0
    RAW.mkdir(parents=True, exist_ok=True)
    cards = {"mode": mode, "frameworks": {}, "note": "Install ragas/deepeval/trulens for live runs; stub records pilot scope."}
    for fw in ("t12_ragas_faithfulness", "t12_deepeval_faithfulness", "t12_trulens_groundedness"):
        cards["frameworks"][fw] = {"pilot_n": n, "status": "pending_implementation", "QI": None, "NS": None, "US": None}
    OUT.write_text(json.dumps(cards, indent=2) + "\n")
    if os.environ.get("OPENROUTER_API_KEY"):
        subprocess.call([sys.executable, str(ROOT / "scripts/openrouter_budget.py")], cwd=ROOT)
    print(OUT)


if __name__ == "__main__":
    main()
