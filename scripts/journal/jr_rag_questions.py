#!/usr/bin/env python3
"""(B1) Real-RAG expansion: sample ~200 dose sentences from the textbook corpus (disjoint from the
main bases, all earlier packs and the T15 fine-tune training bases) and write one natural clinical
question per sentence with a pinned, temperature-0 LLM.

Output: results/journal/rag/questions.jsonl (resumable by qid).
  --dry-run : no API; builds the pool, prints counts + cost estimate, writes nothing persistent
             (template questions to /tmp) -- works on the box with --corpus-dir <tiny dir>.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import (QUESTION_WRITER, RAG_DIR, ROOT, append_jsonl, assert_budget, chat_pinned, est_cost,  # noqa: E402
                       is_done, log, mark_done, read_jsonl, spec_check, tokens)

STAGE = "B1_questions"
OUT = RAG_DIR / "questions.jsonl"
SEED = 20261001
PROMPT = (
    "You are helping build a medical question-answering benchmark.\n"
    "Read the textbook sentence below and write ONE natural question that a clinician could ask a "
    "medical assistant, whose answer is the dose stated in the sentence.\n"
    "Rules: name the drug (or intervention) and the clinical context; do NOT include the dose number or "
    "unit; one sentence; output only the question.\n\n"
    "Context: {context}\n\nSentence: {sentence}\n\nQuestion:"
)


def default_corpus_dirs():
    out = []
    snap = ROOT / ".cache/huggingface/hub/datasets--MedRAG--textbooks/snapshots"
    if snap.is_dir():
        out += sorted(p / "chunk" for p in snap.iterdir() if (p / "chunk").is_dir())
    return out


def t15_forbidden():
    pids, hashes = set(), set()
    from t15_disjoint import sentence_hash  # noqa: E402

    for p in (ROOT / "data/t15/bases.jsonl", ROOT / "data/t24/instances_t24b.jsonl"):
        for r in read_jsonl(p):
            if r.get("source_passage_id"):
                pids.add(str(r["source_passage_id"]))
            if r.get("target_sentence"):
                hashes.add(sentence_hash(r["target_sentence"]))
    return pids, hashes


def build_candidates(corpus_dirs, n_cand, seed):
    from extract_candidates import build_pool  # noqa: E402
    from t15_disjoint import collect_forbidden, row_blocked, sentence_hash  # noqa: E402
    from text_utils import normalize_ws  # noqa: E402

    forbidden = collect_forbidden(ROOT)
    t15_pids, t15_hashes = t15_forbidden()
    stats = Counter()
    by_book = defaultdict(list)
    seen = set()
    for d in corpus_dirs:
        if not Path(d).is_dir():
            stats["missing_dir"] += 1
            continue
        pool, summ = build_pool(Path(d))
        stats["chunks"] += summ.get("chunks", 0)
        for r in pool:
            if r.get("type") != "DOSE":
                continue
            stats["dose_sentences"] += 1
            reason = row_blocked({"source_passage_id": r.get("source_passage_id"),
                                  "target_sentence": r.get("target_sentence")}, forbidden)
            if reason:
                stats["drop_main_or_pack_" + reason] += 1
                continue
            if str(r.get("source_passage_id")) in t15_pids or sentence_hash(r["target_sentence"]) in t15_hashes:
                stats["drop_t15_train_or_t24"] += 1
                continue
            key = normalize_ws(r["target_sentence"]).casefold()
            if key in seen:
                continue
            seen.add(key)
            by_book[r.get("book") or "?"].append(r)
    rng = random.Random(seed)
    for b in sorted(by_book):
        rng.shuffle(by_book[b])
    # round-robin over books for diversity
    picked, books = [], sorted(by_book)
    while len(picked) < n_cand and any(by_book[b] for b in books):
        for b in books:
            if by_book[b] and len(picked) < n_cand:
                picked.append(by_book[b].pop())
    stats["eligible_after_filters"] = len(seen)
    stats["books"] = len(books)
    return picked, stats


def leaks_dose(question: str, span: str) -> bool:
    nums = re.findall(r"\d+(?:[.,]\d+)?", span or "")
    return any(re.search(r"(?<![\d.])%s(?![\d])" % re.escape(n), question) for n in nums)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--oversample", type=float, default=1.4)
    ap.add_argument("--corpus-dir", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    dirs = [Path(d) for d in args.corpus_dir] or default_corpus_dirs()
    if not dirs:
        raise SystemExit("no corpus dirs (MedRAG textbooks snapshot not found); pass --corpus-dir")
    cands, stats = build_candidates(dirs, int(args.n * args.oversample), args.seed)
    est = sum(est_cost(QUESTION_WRITER["model"], tokens(PROMPT) + tokens(c["evidence"]) + tokens(c["target_sentence"]), 40)
              for c in cands)
    log(STAGE, corpus_dirs=[str(d) for d in dirs], candidates=len(cands), est_cost_usd=round(est, 4), **stats)
    if args.dry_run:
        tmp = Path("/tmp/jr_questions_dryrun.jsonl")
        with tmp.open("w") as fh:
            for i, c in enumerate(cands[: args.n]):
                q = "What dose applies here: " + c["target_sentence"].replace(c["target_span"], "___") + " (dry-run template)"
                fh.write(json.dumps({"qid": "JRQ%03d" % i, "valid": True, "question": q, "target_span": c["target_span"],
                                     "book": c.get("book"), "source_passage_id": c.get("source_passage_id")}) + "\n")
        log(STAGE, dry_run=True, wrote=str(tmp))
        return
    probs = spec_check()
    if probs:
        raise SystemExit("SPEC CHECK FAILED (no API call made): %s" % probs)
    done = {r["qid"]: r for r in read_jsonl(OUT)}
    n_ok = sum(1 for r in done.values() if r.get("valid"))
    for i, c in enumerate(cands):
        if n_ok >= args.n:
            break
        qid = "JRQ%03d" % i
        if qid in done:
            continue
        prompt = PROMPT.format(context=c["evidence"][:1500], sentence=c["target_sentence"])
        assert_budget(est_cost(QUESTION_WRITER["model"], tokens(prompt), 60) * 3, "question writer")
        try:
            res = chat_pinned(QUESTION_WRITER, prompt, max_tokens=80)
        except Exception as exc:  # keep going; record failure (no cost)
            append_jsonl(OUT, [{"qid": qid, "valid": False, "error": str(exc)[:300]}])
            continue
        q = res.pop("text").strip().strip('"').split("\n")[0].strip()
        valid = bool(q) and q.endswith("?") and not leaks_dose(q, c["target_span"])
        row = {"qid": qid, "valid": valid, "question": q, "book": c.get("book"),
               "source_passage_id": c.get("source_passage_id"), "target_sentence": c["target_sentence"],
               "target_span": c["target_span"], "source_evidence": c["evidence"],
               "invalid_reason": None if valid else ("leaks_dose" if q.endswith("?") else "format"), **res}
        append_jsonl(OUT, [row])
        n_ok += int(valid)
    log(STAGE, valid_questions=n_ok, spent=assert_budget()["spent_usd"])
    if n_ok >= min(args.n, 50):
        mark_done(STAGE, valid_questions=n_ok, candidates=len(cands), **{k: v for k, v in stats.items()})


if __name__ == "__main__":
    main()
