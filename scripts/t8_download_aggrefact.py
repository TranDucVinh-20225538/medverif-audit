#!/usr/bin/env python3
"""Cache LLM-AggreFact to data/t8/aggrefact/{dev,test}.jsonl (HF gated — accept terms first)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/t8/aggrefact"


def main() -> None:
    from datasets import load_dataset

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for split in ("dev", "test"):
        ds = load_dataset("lytang/LLM-AggreFact", split=split)
        path = OUT_DIR / f"{split}.jsonl"
        with path.open("w") as handle:
            for row in ds:
                handle.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
        print(f"wrote {path} ({len(ds)} rows)")


if __name__ == "__main__":
    main()
