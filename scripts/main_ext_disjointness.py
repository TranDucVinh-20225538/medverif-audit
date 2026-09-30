#!/usr/bin/env python3
"""Disjointness check for main_ext vs main + T15 (+ sentence hashes)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t15_disjoint import collect_forbidden, row_blocked, sentence_hash  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--bases", type=Path, default=ROOT / "data/main_ext/bases_main_ext.jsonl")
    p.add_argument("--out", type=Path, default=ROOT / "data/main_ext/disjointness_check.json")
    args = p.parse_args()
    forbidden = collect_forbidden(ROOT)
    overlap_counts = {"base_id": 0, "source_passage_id": 0, "sentence_hash": 0}
    samples: dict[str, list] = {k: [] for k in overlap_counts}
    bases = list(read_jsonl(args.bases))
    for row in bases:
        reason = row_blocked(
            {
                "base_id": row.get("id"),
                "source_passage_id": row.get("source_passage_id"),
                "target_sentence": row.get("target_sentence") or row.get("claim"),
            },
            forbidden,
        )
        if reason:
            overlap_counts[reason] += 1
            if len(samples[reason]) < 5:
                samples[reason].append(row.get("id"))
    payload = {
        "n_bases_checked": len(bases),
        "overlap_counts": overlap_counts,
        "overlap_total": sum(overlap_counts.values()),
        "forbidden_sizes": {k: len(v) for k, v in forbidden.items()},
        "overlap_samples": samples,
        "sentence_hash_fn": "sha256 normalize_ws casefold (t15_disjoint)",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    if payload["overlap_total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
