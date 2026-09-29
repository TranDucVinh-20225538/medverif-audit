#!/usr/bin/env python3
"""T15 step 1: MedRAG/StatPearls dose bases + rule pairs + ANLI mix."""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from extract_candidates import build_pool  # noqa: E402
from t15_disjoint import collect_forbidden, row_blocked, sentence_hash  # noqa: E402
from t15_pairs import pairs_for_base  # noqa: E402
from text_utils import dose_matches, normalize_ws  # noqa: E402


def _span_in_sentence(row: dict) -> tuple[int, int] | None:
    sentence = row.get("target_sentence") or ""
    span = row.get("target_span") or ""
    for m in dose_matches(sentence):
        if m.group(0) == span:
            return m.start(), m.end()
    if span:
        idx = sentence.find(span)
        if idx >= 0:
            return idx, idx + len(span)
    return None


def _backup(out_dir: Path) -> None:
    if not out_dir.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = out_dir.parent / "backups" / f"t15_{stamp}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(out_dir, dest, dirs_exist_ok=True)


def _load_anli(n: int, seed: int) -> list[dict]:
    from datasets import load_dataset

    rows: list[dict] = []
    for rnd in ("r1", "r2", "r3"):
        ds = load_dataset("anli", "plain_text", split=f"train_{rnd}")
        for ex in ds:
            label = ex["label"]
            if label == 0:
                lab = "SUPPORTED"
            elif label in (1, 2):
                lab = "UNSUPPORTED"
            else:
                continue
            uid = ex.get("uid") or ex.get("id") or len(rows)
            rows.append(
                {
                    "pair_id": f"ANLI-{rnd}-{uid}",
                    "base_id": f"ANLI-{rnd}-{uid}",
                    "variant": "ANLI",
                    "claim": ex["hypothesis"],
                    "evidence": ex["premise"],
                    "label": lab,
                    "source_passage_id": None,
                    "sentence_hash": None,
                }
            )
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows[:n]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, action="append", default=[])
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/t15")
    parser.add_argument("--target-bases", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dev-frac", type=float, default=0.1)
    args = parser.parse_args()

    default_corpora = [
        ROOT / ".cache/statpearls/chunk",
        ROOT / ".cache/huggingface/hub/datasets--MedRAG--textbooks/snapshots",
    ]
    corpus_dirs = list(args.corpus_dir)
    if not corpus_dirs:
        for base in default_corpora:
            if base.name == "snapshots":
                corpus_dirs.extend(sorted(p / "chunk" for p in base.iterdir() if (p / "chunk").is_dir()))
            elif base.is_dir():
                corpus_dirs.append(base)

    forbidden = collect_forbidden(ROOT)
    pool: list[dict] = []
    stats = Counter()
    for corpus_dir in corpus_dirs:
        if not corpus_dir.is_dir():
            continue
        part, summary = build_pool(corpus_dir)
        stats["chunks"] += summary.get("chunks", 0)
        for row in part:
            if row.get("type") != "DOSE":
                continue
            probe = {
                "source_passage_id": row.get("source_passage_id"),
                "target_sentence": row.get("target_sentence"),
            }
            reason = row_blocked(probe, forbidden)
            if reason:
                stats[f"drop_{reason}"] += 1
                continue
            pool.append(row)
            stats["pool_dose"] += 1

    seen_passage_sent: set[tuple[str, str]] = set()
    unique_pool: list[dict] = []
    for row in pool:
        key = (str(row.get("source_passage_id") or ""), normalize_ws(row["target_sentence"]).casefold())
        if key in seen_passage_sent:
            stats["drop_duplicate"] += 1
            continue
        seen_passage_sent.add(key)
        unique_pool.append(row)

    rng = random.Random(args.seed)
    rng.shuffle(unique_pool)
    selected: list[dict] = []
    pairs: list[dict] = []
    failures: list[dict] = []
    for i, row in enumerate(unique_pool):
        if len(selected) >= args.target_bases:
            break
        span_loc = _span_in_sentence(row)
        if span_loc is None:
            stats["drop_no_span"] += 1
            continue
        ls, le = span_loc
        base_id = f"T15B{i + 1:05d}"
        base = {
            **row,
            "base_id": base_id,
            "span_start_in_sentence": ls,
            "span_end_in_sentence": le,
            "sentence_hash": sentence_hash(row["target_sentence"]),
        }
        got, fail = pairs_for_base(base)
        if not got:
            failures.extend(fail)
            stats["drop_pair_fail"] += 1
            continue
        selected.append(base)
        pairs.extend(got)

    base_ids = [b["base_id"] for b in selected]
    rng.shuffle(base_ids)
    n_dev = max(1, int(len(base_ids) * args.dev_frac))
    dev_ids = set(base_ids[:n_dev])

    anli_n = len(pairs)
    anli_rows = _load_anli(anli_n, args.seed + 1)
    anli_dev = set(r["base_id"] for r in anli_rows[: max(1, int(len(anli_rows) * args.dev_frac))])

    def split_rows(rows: list[dict], dev_bases: set[str]) -> tuple[list[dict], list[dict]]:
        train, dev = [], []
        for r in rows:
            bid = r["base_id"]
            if bid in dev_bases:
                dev.append(r)
            else:
                train.append(r)
        return train, dev

    dose_train, dose_dev = split_rows(pairs, dev_ids)
    anli_train, anli_dev = split_rows(anli_rows, anli_dev)

    out_dir = args.out_dir
    _backup(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        with path.open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_jsonl(out_dir / "bases.jsonl", selected)
    write_jsonl(out_dir / "pairs_dose.jsonl", pairs)
    write_jsonl(out_dir / "train.jsonl", dose_train + anli_train)
    write_jsonl(out_dir / "dev.jsonl", dose_dev + anli_dev)
    write_jsonl(out_dir / "train_dose_only.jsonl", dose_train)
    write_jsonl(out_dir / "dev_dose_only.jsonl", dose_dev)

    manifest = {
        "seed": args.seed,
        "corpus_dirs": [str(p) for p in corpus_dirs],
        "target_bases": args.target_bases,
        "n_bases": len(selected),
        "n_pairs_dose": len(pairs),
        "n_train": len(dose_train) + len(anli_train),
        "n_dev": len(dose_dev) + len(anli_dev),
        "n_anli_train": len(anli_train),
        "n_anli_dev": len(anli_dev),
        "dev_base_ids": sorted(dev_ids),
        "extract_stats": dict(stats),
        "pair_failures_sample": failures[:20],
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
