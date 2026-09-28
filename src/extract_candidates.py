"""Select DOSE and POLARITY candidates from MedRAG Textbooks chunks.

CPU only. Does not call a model. StatPearls is not read.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from text_utils import (
    CALC_RE,
    DOSE_CONTEXT_RE,
    DRUG_RE,
    convertible_unit,
    cue_key,
    dose_matches,
    is_range_sentence,
    join_window,
    looks_like_table,
    normalize_ws,
    polarity_matches,
    split_sentences,
    word_count,
)

ROOT = Path("/data2/hpcshared/medverif-audit")


def iter_chunks(corpus_dir: Path) -> Iterable[dict]:
    files = sorted(corpus_dir.glob("*.jsonl"))
    if not files:
        raise FileNotFoundError(f"no jsonl chunks in {corpus_dir}")
    for path in files:
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                row["_file"] = path.name
                yield row


def sentence_blocked(sentence: str) -> str | None:
    if looks_like_table(sentence):
        return "table_or_figure"
    n_words = word_count(sentence)
    if n_words < 8 or n_words > 55:
        return "sentence_length"
    if CALC_RE.search(sentence):
        return "calculation"
    return None


def dose_candidate(sentence: str) -> tuple[dict | None, str | None]:
    blocked = sentence_blocked(sentence)
    if blocked:
        return None, blocked
    if is_range_sentence(sentence):
        return None, "range_dose"
    matches = dose_matches(sentence)
    if len(matches) == 0:
        return None, None
    if len(matches) != 1:
        return None, "multi_dose"
    if not DOSE_CONTEXT_RE.search(sentence):
        return None, "no_dose_context"
    match = matches[0]
    unit = match.group(2)
    if convertible_unit(unit) is None:
        return None, "unit_not_convertible"
    if match.start() > 0 and sentence[match.start() - 1] in "-–—/":
        return None, "range_dose"
    return {
        "target_span": match.group(0),
        "span_start_in_sentence": match.start(),
        "span_end_in_sentence": match.end(),
        "dose_number": match.group(1),
        "dose_unit": unit,
        "polarity_cue": None,
    }, None


def polarity_candidate(sentence: str) -> tuple[dict | None, str | None]:
    blocked = sentence_blocked(sentence)
    if blocked:
        return None, blocked
    matches = polarity_matches(sentence)
    if len(matches) == 0:
        return None, None
    if len(matches) != 1:
        return None, "multi_polarity"
    match = matches[0]
    after = sentence[match.end(): match.end() + 4]
    if re.match(r"\s+to\b", sentence[match.end():]):
        return None, "polarity_infinitive"
    if not DRUG_RE.search(sentence):
        return None, "no_drug_context"
    cue = match.group(0)
    return {
        "target_span": cue,
        "span_start_in_sentence": match.start(),
        "span_end_in_sentence": match.end(),
        "dose_number": None,
        "dose_unit": None,
        "polarity_cue": cue_key(cue),
    }, None


def build_pool(corpus_dir: Path) -> tuple[List[dict], dict]:
    stats = Counter()
    drops = Counter()
    seen = set()
    pool: List[dict] = []
    for row in iter_chunks(corpus_dir):
        stats["chunks"] += 1
        content = row.get("content") or ""
        sentences = split_sentences(content)
        stats["sentences"] += len(sentences)
        passage_id = str(row.get("id") or "")
        book = str(row.get("title") or Path(row["_file"]).stem)
        for idx, sentence in enumerate(sentences):
            key = normalize_ws(sentence).casefold()
            for kind, builder in (("DOSE", dose_candidate), ("POLARITY", polarity_candidate)):
                cand, reason = builder(sentence)
                if cand is None and reason is None:
                    continue
                if reason:
                    drops[f"{kind}:{reason}"] += 1
                    continue
                dedupe_key = (kind, key)
                if dedupe_key in seen:
                    drops[f"{kind}:duplicate_sentence"] += 1
                    continue
                seen.add(dedupe_key)
                evidence, sent_start, sent_end = join_window(sentences, idx)
                local_start = cand["span_start_in_sentence"]
                local_end = cand["span_end_in_sentence"]
                if sentence[local_start:local_end] != cand["target_span"]:
                    drops[f"{kind}:span_mismatch"] += 1
                    continue
                abs_start = sent_start + local_start
                abs_end = sent_start + local_end
                if evidence[abs_start:abs_end] != cand["target_span"]:
                    drops[f"{kind}:window_span_mismatch"] += 1
                    continue
                pool.append({
                    "type": kind,
                    "book": book,
                    "source_passage_id": passage_id,
                    "evidence": evidence,
                    "target_sentence": sentence,
                    "target_span": cand["target_span"],
                    "evidence_span_start": abs_start,
                    "evidence_span_end": abs_end,
                    "dose_number": cand["dose_number"],
                    "dose_unit": cand["dose_unit"],
                    "polarity_cue": cand["polarity_cue"],
                })
                stats[f"pool_{kind}"] += 1
    summary = {
        "chunks": stats["chunks"],
        "sentences": stats["sentences"],
        "pool_DOSE": stats["pool_DOSE"],
        "pool_POLARITY": stats["pool_POLARITY"],
        "extract_drops": dict(drops),
    }
    return pool, summary


def select(pool: List[dict], per_book: int, per_passage: int, attempt: int, seed: int) -> tuple[List[dict], dict]:
    rng = random.Random(seed)
    by_type: Dict[str, List[dict]] = defaultdict(list)
    for row in pool:
        by_type[row["type"]].append(row)
    selected: List[dict] = []
    select_drops = Counter()
    for kind in ("DOSE", "POLARITY"):
        rows = list(by_type.get(kind, []))
        rng.shuffle(rows)
        book_n: Dict[str, int] = defaultdict(int)
        passage_n: Dict[str, int] = defaultdict(int)
        kept = 0
        for row in rows:
            if kept >= attempt:
                select_drops[f"{kind}:attempt_cap"] += 1
                continue
            if book_n[row["book"]] >= per_book:
                select_drops[f"{kind}:book_cap"] += 1
                continue
            if passage_n[row["source_passage_id"]] >= per_passage:
                select_drops[f"{kind}:passage_cap"] += 1
                continue
            kept += 1
            book_n[row["book"]] += 1
            passage_n[row["source_passage_id"]] += 1
            item = dict(row)
            prefix = "D" if kind == "DOSE" else "P"
            item["cand_id"] = f"{prefix}{kept:04d}"
            selected.append(item)
        select_drops[f"{kind}:selected"] = kept
    return selected, dict(select_drops)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--per-book", type=int, default=25)
    parser.add_argument("--per-passage", type=int, default=2)
    parser.add_argument("--attempt", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    pool, summary = build_pool(args.corpus_dir)
    selected, select_drops = select(pool, args.per_book, args.per_passage, args.attempt, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary["selection"] = select_drops
    summary["selected"] = len(selected)
    summary["seed"] = args.seed
    summary["per_book"] = args.per_book
    summary["per_passage"] = args.per_passage
    summary["attempt_per_type"] = args.attempt
    args.stats.parent.mkdir(parents=True, exist_ok=True)
    args.stats.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
