#!/usr/bin/env python3
"""Select DOSE candidates from MedRAG Textbooks only (disjoint from main + T15)."""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from extract_candidates import dose_candidate, iter_chunks, join_window  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402
from t15_disjoint import collect_forbidden, row_blocked  # noqa: E402
from text_utils import normalize_ws, split_sentences  # noqa: E402


def default_textbook_dir() -> Path:
    cache = ROOT / ".cache/huggingface/hub/datasets--MedRAG--textbooks/snapshots"
    if cache.is_dir():
        snaps = sorted(cache.iterdir())
        if snaps:
            chunk = snaps[-1] / "chunk"
            if chunk.is_dir():
                return chunk
    raise FileNotFoundError("MedRAG textbooks chunk dir not found under .cache/huggingface")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus-dir", type=Path, default=None)
    p.add_argument("--out", type=Path, default=ROOT / "data/main_ext/candidates_selected.jsonl")
    p.add_argument("--stats", type=Path, default=ROOT / "notes/main_ext_candidate_stats.json")
    p.add_argument("--pool-min", type=int, default=200, help="minimum disjoint DOSE rows required in pool")
    p.add_argument(
        "--pool-cap",
        type=int,
        default=100000,
        help="max textbook chunks scanned while filling pool-min (corpus ~32k chunks)",
    )
    p.add_argument("--max-candidates", type=int, default=250, help="candidates written for stage1")
    p.add_argument("--seed", type=int, default=20260929)
    p.add_argument(
        "--append",
        action="store_true",
        help="add candidates after existing file/stage1 (no pool-min stop; skip used sentences)",
    )
    p.add_argument("--prior-candidates", type=Path, default=None)
    args = p.parse_args()
    corpus = args.corpus_dir or default_textbook_dir()
    forbidden = collect_forbidden(ROOT)
    stats = Counter()
    pool: list[dict] = []
    seen_sent: set[tuple[str, str]] = set()
    start_idx = 1
    prior_path = args.prior_candidates or (args.out if args.append and args.out.is_file() else None)
    if args.append and prior_path and prior_path.is_file():
        for row in read_jsonl(prior_path):
            key = (str(row.get("source_passage_id") or ""), normalize_ws(row.get("target_sentence") or "").casefold())
            seen_sent.add(key)
            cid = row.get("cand_id") or ""
            if cid.startswith("MEX") and cid[3:].isdigit():
                start_idx = max(start_idx, int(cid[3:]) + 1)
    pool_min = 0 if args.append else args.pool_min
    for row in iter_chunks(corpus):
        stats["chunks"] += 1
        content = row.get("content") or ""
        sentences = split_sentences(content)
        stats["sentences"] += len(sentences)
        passage_id = str(row.get("id") or "")
        book = str(row.get("title") or row.get("_file", ""))
        for idx, sentence in enumerate(sentences):
            cand, reason = dose_candidate(sentence)
            if reason:
                stats[f"drop_{reason}"] += 1
                continue
            if cand is None:
                continue
            probe = {"source_passage_id": passage_id, "target_sentence": sentence}
            blocked = row_blocked(probe, forbidden)
            if blocked:
                stats[f"drop_{blocked}"] += 1
                continue
            key = (passage_id, normalize_ws(sentence).casefold())
            if key in seen_sent:
                stats["drop_duplicate"] += 1
                continue
            seen_sent.add(key)
            evidence, s0, _s1 = join_window(sentences, idx)
            ls, le = cand["span_start_in_sentence"], cand["span_end_in_sentence"]
            pool.append(
                {
                    "type": "DOSE",
                    "book": book,
                    "source_passage_id": passage_id,
                    "evidence": evidence,
                    "target_sentence": sentence,
                    "target_span": cand["target_span"],
                    "evidence_span_start": s0 + ls,
                    "evidence_span_end": s0 + le,
                    "dose_number": cand["dose_number"],
                    "dose_unit": cand["dose_unit"],
                    "polarity_cue": None,
                }
            )
            stats["pool_dose"] += 1
            if not args.append and len(pool) >= args.pool_min:
                break
        if not args.append and len(pool) >= args.pool_min:
            break
        if stats["chunks"] >= args.pool_cap:
            break
    if not args.append and len(pool) < args.pool_min:
        raise RuntimeError(
            f"main_ext pool: need >={args.pool_min} disjoint DOSE rows, got {len(pool)} "
            f"(chunks={stats['chunks']})"
        )
    summary = {
        "chunks": stats["chunks"],
        "sentences": stats["sentences"],
        "pool_DOSE": len(pool),
        "pool_min": args.pool_min,
    }
    rng = random.Random(args.seed)
    rng.shuffle(pool)
    selected: list[dict] = []
    slice_pool = pool[: args.max_candidates]
    for i, row in enumerate(slice_pool):
        item = dict(row)
        item["cand_id"] = f"MEX{start_idx + i:04d}"
        selected.append(item)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    with args.out.open(mode) as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    out_stats = {
        "corpus_dir": str(corpus),
        "source": "MedRAG_Textbooks_only",
        "extract_summary": summary,
        "extract_stats": dict(stats),
        "pool_min_required": args.pool_min,
        "chunk_scan_cap": args.pool_cap,
        "n_candidates": len(selected),
        "seed": args.seed,
        "forbidden_sizes": {k: len(v) for k, v in forbidden.items()},
    }
    args.stats.parent.mkdir(parents=True, exist_ok=True)
    args.stats.write_text(json.dumps(out_stats, indent=2) + "\n")
    print(json.dumps(out_stats, indent=2))


if __name__ == "__main__":
    main()
