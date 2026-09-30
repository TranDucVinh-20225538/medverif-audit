#!/usr/bin/env python3
"""T16: 100 dose bases × C0 / Conv / Unit-up (claim-side) for attribution."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t15_pairs import pairs_for_base  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402

OUT = ROOT / "data/t16/instances_t16.jsonl"
MANIFEST = ROOT / "notes/t16_manifest.json"


def main() -> None:
    bases_path = ROOT / "data/t15/bases.jsonl"
    if not bases_path.is_file():
        raise SystemExit(f"missing {bases_path}; run t15_build_training_data.py first")
    bases = read_jsonl(bases_path)
    rng = random.Random(42)
    rng.shuffle(bases)
    chosen = bases[:100]
    rows: list[dict] = []
    want_variants = {"C0", "Conv", "Unit-up-claim"}
    for base in chosen:
        pairs, _fail = pairs_for_base(base)
        for pair in pairs:
            if pair["variant"] not in want_variants:
                continue
            rows.append(
                {
                    "instance_id": pair["pair_id"],
                    "base_id": pair["base_id"],
                    "condition": pair["variant"],
                    "claim": pair["claim"],
                    "evidence": pair["evidence"],
                    "label": pair["label"],
                    "valid": True,
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {"path": str(OUT.relative_to(ROOT)), "n_instances": len(rows), "n_bases": len(chosen)}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
