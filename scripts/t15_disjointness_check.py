#!/usr/bin/env python3
"""Verify T15 training bases are disjoint from evaluation packs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t15_disjoint import collect_forbidden, row_blocked, sentence_hash  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bases", type=Path, default=ROOT / "data/t15/bases.jsonl")
    parser.add_argument("--out", type=Path, default=ROOT / "data/t15/disjointness_check.json")
    args = parser.parse_args()

    forbidden = collect_forbidden(ROOT)
    overlap = {"base_id": [], "source_passage_id": [], "sentence_hash": []}
    n = 0
    with args.bases.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            n += 1
            row = json.loads(line)
            reason = row_blocked(row, forbidden)
            if reason == "base_id":
                overlap["base_id"].append(row.get("base_id"))
            elif reason == "source_passage_id":
                overlap["source_passage_id"].append(row.get("source_passage_id"))
            elif reason == "sentence_hash":
                overlap["sentence_hash"].append(row.get("sentence_hash") or sentence_hash(row.get("target_sentence", "")))

    payload = {
        "n_bases_checked": n,
        "overlap_counts": {k: len(v) for k, v in overlap.items()},
        "overlap_total": sum(len(v) for v in overlap.values()),
        "forbidden_sizes": {k: len(v) for k, v in forbidden.items()},
        "overlap_samples": {k: v[:10] for k, v in overlap.items()},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    if payload["overlap_total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
