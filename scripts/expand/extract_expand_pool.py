#!/usr/bin/env python3
"""Extract DOSE/POLARITY candidate pools from StatPearls + unused Textbooks sentences."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from extract_candidates import build_pool, select  # noqa: E402
from text_utils import normalize_ws  # noqa: E402


def used_sentence_keys(v2_dir: Path) -> set[tuple[str, str]]:
    used: set[tuple[str, str]] = set()
    for path in v2_dir.glob("bases_*.jsonl"):
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                book = str(row.get("book") or "")
                sent = normalize_ws(row.get("target_sentence") or "").casefold()
                if sent:
                    used.add((book, sent))
    return used


def build_pool_exclude(corpus_dirs: list[Path], used: set[tuple[str, str]]) -> tuple[list, dict]:
    stats = Counter()
    drops = Counter()
    seen: set[tuple[str, str]] = set()
    pool: list = []
    for corpus_dir in corpus_dirs:
        part, summary = build_pool(corpus_dir)
        stats["chunks"] += summary.get("chunks", 0)
        stats["sentences"] += summary.get("sentences", 0)
        for row in part:
            book = str(row.get("book") or "")
            sent = normalize_ws(row.get("target_sentence") or "").casefold()
            if (book, sent) in used:
                drops["used_v2_sentence"] += 1
                continue
            dedupe = (row["type"], sent)
            if dedupe in seen:
                drops["duplicate_sentence"] += 1
                continue
            seen.add(dedupe)
            pool.append(row)
            stats[f"pool_{row['type']}"] += 1
    summary = {
        "chunks": stats["chunks"],
        "sentences": stats["sentences"],
        "pool_DOSE": stats["pool_DOSE"],
        "pool_POLARITY": stats["pool_POLARITY"],
        "extract_drops": dict(drops),
    }
    return pool, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, action="append", required=True)
    parser.add_argument("--v2-dir", type=Path, default=ROOT / "data" / "v2")
    parser.add_argument("--out-pool", type=Path, required=True)
    parser.add_argument("--out-selected", type=Path, required=True)
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--attempt", type=int, default=400)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    used = used_sentence_keys(args.v2_dir)
    pool, summary = build_pool_exclude(args.corpus_dir, used)
    selected, select_drops = select(pool, 40, 3, args.attempt, args.seed)
    args.out_pool.parent.mkdir(parents=True, exist_ok=True)
    with args.out_pool.open("w") as handle:
        for row in pool:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with args.out_selected.open("w") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary["used_v2_keys"] = len(used)
    summary["selection"] = select_drops
    summary["selected"] = len(selected)
    summary["seed"] = args.seed
    args.stats.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
