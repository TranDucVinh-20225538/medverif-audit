#!/usr/bin/env python3
"""(RD-2) Generator answers to the real-label dosing questions (API; pinned generators from chain 1:
openai/gpt-4o-mini@OpenAI, google/gemma-3-27b-it@DeepInfra via OpenRouter; temperature 0, seed 42).

Conditions: grounded (label excerpt in the prompt) and closed (no excerpt).  Resumable by
(qid, generator, condition).  Spec check before any call; real-dose budget check (separate ledger,
default $5) before every batch of 20 calls.

Output: results/journal2/real_dose/answers.jsonl
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr2_common import (GENERATORS, RD, append_jsonl, chat_pinned, est_cost, is_done, log, mark_done,  # noqa: E402
                        rd_assert_budget, rd_spec_check, read_jsonl, tokens)

STAGE = "RD2_generate"
QS = RD / "questions.jsonl"
OUT = RD / "answers.jsonl"
CONDITIONS = ("grounded", "closed")
PROMPTS = {
    "grounded": ("Answer the question using ONLY the drug label excerpt below. Answer in 1-2 sentences and state the "
                 "dose (number and unit).\n\nLabel excerpt ({drug}):\n{excerpt}\n\nQuestion: {question}\n\nAnswer:"),
    "closed": ("Answer from your own knowledge of the US prescribing information (no reference text is provided). "
               "Answer in 1-2 sentences and state the dose (number and unit).\n\nQuestion: {question}\n\nAnswer:"),
}
MAX_TOKENS = 160


def render(q: dict, cond: str) -> str:
    return PROMPTS[cond].format(drug=q["drug"], excerpt=q["excerpt"], question=q["question"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generators", default=",".join(GENERATORS))
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="first N questions only (smoke)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    qs = read_jsonl(QS)
    if args.limit:
        qs = qs[: args.limit]
    gens = [g for g in args.generators.split(",") if g]
    conds = [c for c in args.conditions.split(",") if c]
    est = {"%s/%s" % (g, c): round(sum(est_cost(GENERATORS[g]["model"], tokens(render(q, c)), MAX_TOKENS) for q in qs), 4)
           for g in gens for c in conds}
    log(STAGE, questions=len(qs), calls=len(qs) * len(gens) * len(conds), est_cost_usd=est,
        est_total_usd=round(sum(est.values()), 4), generators={g: GENERATORS[g] for g in gens})
    if args.dry_run:
        return
    probs = rd_spec_check()
    if probs:
        raise SystemExit("SPEC CHECK FAILED (no API call made): %s" % probs)
    done = {(r["qid"], r["generator"], r["condition"]) for r in read_jsonl(OUT) if r.get("answer")}
    todo = [(q, g, c) for g in gens for c in conds for q in qs if (q["qid"], g, c) not in done]

    def one(item):
        q, g, c = item
        try:
            res = chat_pinned(GENERATORS[g], render(q, c), max_tokens=MAX_TOKENS)
            if res["api_model"] and not res["api_model"].startswith(GENERATORS[g]["model"].split(":")[0]):
                raise RuntimeError("model drift: asked %s, served %s" % (GENERATORS[g]["model"], res["api_model"]))
            return {"qid": q["qid"], "drug": q["drug"], "generator": g, "condition": c, "answer": res.pop("text"), **res}
        except Exception as exc:  # noqa: BLE001
            return {"qid": q["qid"], "drug": q["drug"], "generator": g, "condition": c, "answer": "", "error": str(exc)[:300]}

    for off in range(0, len(todo), 20):
        batch = todo[off:off + 20]
        rd_assert_budget(sum(est_cost(GENERATORS[g]["model"], tokens(render(q, c)), MAX_TOKENS) for q, g, c in batch), "generators")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            out = list(ex.map(one, batch))
        append_jsonl(OUT, out)
        errs = [o for o in out if o.get("error")]
        if len(errs) == len(out):
            raise SystemExit("whole batch failed (first error: %s)" % errs[0]["error"])
        log(STAGE, progress=off + len(batch), total=len(todo), errors=len(errs), spent=round(rd_assert_budget()["spent_usd"], 4))
    ok = {(r["qid"], r["generator"], r["condition"]) for r in read_jsonl(OUT) if r.get("answer")}
    if not args.limit:
        mark_done(STAGE, answers=len(ok), expected=len(qs) * len(gens) * len(conds))


if __name__ == "__main__":
    main()
