#!/usr/bin/env python3
"""(B3a) Answer generation: 2 generator LLMs (pinned providers, temperature 0, seed 42) answer each
question from the top-k fused passages. Resumable by (qid, generator); hard budget check before every
call (shared $5 chain cap).

Output: results/journal/rag/answers.jsonl
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import (GENERATORS, RAG_DIR, append_jsonl, assert_budget, chat_pinned, est_cost, is_done, log,  # noqa: E402
                       mark_done, read_jsonl, spec_check, tokens)

STAGE = "B3a_generate"
RETR = RAG_DIR / "retrieval.jsonl"
OUT = RAG_DIR / "answers.jsonl"
PROMPT = (
    "Answer the clinical question using ONLY the passages below. Answer in 1-3 sentences and state the "
    "dose (number and unit) if the passages give one. If the passages do not contain the answer, say so.\n\n"
    "{passages}\n\nQuestion: {question}\n\nAnswer:"
)


def render(row: dict) -> str:
    ps = "\n\n".join("Passage %d (%s):\n%s" % (i + 1, p.get("title") or "", p["text"]) for i, p in enumerate(row["passages"]))
    return PROMPT.format(passages=ps, question=row["question"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generators", default=",".join(GENERATORS))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--retrieval", default=str(RETR))
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    rows = read_jsonl(Path(args.retrieval))
    gens = [g.strip() for g in args.generators.split(",") if g.strip()]
    est = {g: sum(est_cost(GENERATORS[g]["model"], tokens(render(r)), 180) for r in rows) for g in gens}
    log(STAGE, questions=len(rows), est_cost_usd={g: round(v, 4) for g, v in est.items()})
    if args.dry_run:
        return
    probs = spec_check()
    if probs:
        raise SystemExit("SPEC CHECK FAILED (no API call made): %s" % probs)
    done = {(r["qid"], r["generator"]) for r in read_jsonl(OUT) if r.get("answer")}
    todo = [(r, g) for g in gens for r in rows if (r["qid"], g) not in done]

    def one(item):
        r, g = item
        prompt = render(r)
        try:
            res = chat_pinned(GENERATORS[g], prompt, max_tokens=256)
            return {"qid": r["qid"], "generator": g, "answer": res.pop("text"), "question": r["question"], **res}
        except Exception as exc:
            return {"qid": r["qid"], "generator": g, "answer": "", "error": str(exc)[:300]}

    for off in range(0, len(todo), 20):
        batch = todo[off:off + 20]
        assert_budget(sum(est_cost(GENERATORS[g]["model"], tokens(render(r)), 256) for r, g in batch), "generators")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            out = list(ex.map(one, batch))
        append_jsonl(OUT, out)
        log(STAGE, progress=off + len(batch), total=len(todo), spent=round(assert_budget()["spent_usd"], 4))
    n_ok = len({(r["qid"], r["generator"]) for r in read_jsonl(OUT) if r.get("answer")})
    mark_done(STAGE, answers=n_ok, expected=len(rows) * len(gens))


if __name__ == "__main__":
    main()
