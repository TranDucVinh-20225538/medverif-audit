#!/usr/bin/env python3
"""Gemini-only audit on pilot reference pairs (no hard rules)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
sys.path.insert(0, str(ROOT / "src"))

from inv_paraphrase_full_openrouter import QC_V3B, parse_v3b_rewrites  # noqa: E402
from inv_paraphrase_validator import validate_pair_llm_only  # noqa: E402
from openrouter_runtime import load_tokenizer  # noqa: E402

MUST_REJECT = ("D0004", "D0005", "D0007", "P0087")
MUST_PASS = ("D0001", "D0008", "D0009", "D0011", "D0013", "P0021")  # Gemini-only; no hard rules
MODEL = os.environ.get("MEDVERIF_PARA_VAL_MODEL", "google/gemini-2.5-flash")
OUT = ROOT / "notes" / "g_inv_gemini_audit.json"


def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY required")
    v3b = parse_v3b_rewrites(QC_V3B)
    tok = load_tokenizer("meta-llama/Llama-3.2-3B-Instruct", None)
    provider = os.environ.get("MEDVERIF_PARA_VAL_PROVIDER") or None
    rows = []
    for bid in MUST_REJECT + MUST_PASS:
        if bid not in v3b:
            raise SystemExit(f"missing v3b rewrite for {bid}")
        _typ, original, rewrite = v3b[bid]
        ok, meta = validate_pair_llm_only(original, rewrite, model=MODEL, tok=tok, provider=provider)
        rows.append(
            {
                "base_id": bid,
                "expect": "reject" if bid in MUST_REJECT else "pass",
                "pipeline_pass_llm_only": ok,
                "fluent": meta.get("fluent"),
                "same_meaning": meta.get("same_meaning"),
                "reason": meta.get("reason"),
                "model": MODEL,
            }
        )
    OUT.write_text(json.dumps({"pairs": rows, "model": MODEL}, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"out": str(OUT), "n": len(rows)}))
    for r in rows:
        print(
            f"{r['base_id']}: expect={r['expect']} llm_pass={r['pipeline_pass_llm_only']} "
            f"fluent={r['fluent']} same={r['same_meaning']}"
        )


if __name__ == "__main__":
    main()
