#!/usr/bin/env python3
"""(RD2-2) Generator answers to the pre-registered RD2 questions.  Python >= 3.8.  Resumable.

Prompts: IDENTICAL to RD -- rd_generate.PROMPTS / rd_generate.render / MAX_TOKENS=160 are imported from
scripts/journal2/rd_generate.py (sha256 frozen in prereg/rd2_freeze.json); conditions grounded (label excerpt in the
prompt) and closed (no excerpt).  Greedy decoding (temperature 0), seed 42.

Backends
  vllm        open models already on the HPC Hub cache (results/journal3/models.json: exact revision, offline load), one
              model per process / Slurm array task.  The prompt is sent as ONE user turn through the model's chat template
              (add_generation_prompt; enable_thinking=False / thinking_mode="off" where the template supports it -- same
              rendering as the chain-3 judges, scripts/journal3/j3_judge_score.render), tokenized without re-adding BOS.
              If a reasoning model still emits a closed <think>...</think> block, the answer is the text after it (raw kept).
  openrouter  the two RD generators (jr_common.GENERATORS: gpt4o_mini = openai/gpt-4o-mini@OpenAI, gemma3_27b =
              google/gemma-3-27b-it@DeepInfra) through the SAME call path as RD (jr_common.chat_pinned: temperature 0,
              seed 42, pinned provider, no fallbacks).  --max-usd guard (default $3): before every batch, spent (sum of
              api_cost_usd over results/journal5/rd2/**.jsonl) + worst-case batch cost (prompt tokens + 160 completion
              tokens at the price table) must stay <= --max-usd, else stop.
  mock        deterministic stub (no GPU / network) for smoke tests.

Output: results/journal5/rd2/real_dose/answers/<generator>.jsonl (one file per generator, so parallel tasks never share a
file); `--merge` concatenates them into results/journal5/rd2/real_dose/answers.jsonl in a fixed order.
Retry: rows with an empty answer / error are retried on the next pass (--passes, default 3) and on re-runs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import (ANSWERS, QUESTIONS, RD2, RD2_DIR, ROOT, append_jsonl, assert_frozen, log, mark_done,  # noqa: E402
                        read_jsonl, sha256_text, write_jsonl)
from rd_generate import CONDITIONS, MAX_TOKENS, PROMPTS, render  # noqa: E402  (original RD prompts, unchanged)

ANS_DIR = RD2 / "answers"
MODELS_JSON = ROOT / "results" / "journal3" / "models.json"
# local open generators (slug -> hf id, family); weights + pinned revisions come from results/journal3/models.json
LOCAL = {
    "llama31_8b": ("meta-llama/Llama-3.1-8B-Instruct", "llama3"),
    "qwen25_14b": ("Qwen/Qwen2.5-14B-Instruct", "qwen2.5"),
    "medgemma_27b": ("google/medgemma-27b-text-it", "gemma3_text"),
    "baichuan_m2_32b": ("baichuan-inc/Baichuan-M2-32B", "qwen2.5"),
    "qwen25_7b": ("Qwen/Qwen2.5-7B-Instruct", "qwen2.5"),  # optional 5th
}
LOCAL_DEFAULT = ("llama31_8b", "qwen25_14b", "medgemma_27b", "baichuan_m2_32b")
OPENROUTER_DEFAULT = ("gpt4o_mini", "gemma3_27b")
PROMPT_SHA = {c: sha256_text(PROMPTS[c]) for c in PROMPTS}
_THINK = re.compile(r"^.*?</think>\s*", re.S)


def todo_items(qs, gen, conds, out: Path):
    done = {(r["qid"], r["condition"]) for r in read_jsonl(out) if r.get("answer")}
    return [(q, c) for c in conds for q in qs if (q["qid"], c) not in done]


def clean(text: str) -> str:
    """Answer text as stored (RD: .strip()).  Reasoning models: drop a closed <think>...</think> block; an UNTERMINATED
    <think> block (reasoning cut off by the 160-token cap, no answer) is recorded as an empty answer (= missing)."""
    t = (text or "").strip()
    if "</think>" in t:
        t = _THINK.sub("", t, count=1).strip()
    elif t.startswith("<think>"):
        return ""
    return t


# ------------------------------------------------------------------ vLLM
class VLLMGen:
    def __init__(self, slug: str, max_model_len: int):
        import vllm
        from vllm import LLM, SamplingParams

        hf_id, family = LOCAL[slug]
        models = json.loads(MODELS_JSON.read_text()) if MODELS_JSON.is_file() else {}
        rec = models.get(slug) or {}
        if rec.get("status") != "ok" or not rec.get("revision"):
            raise SystemExit("%s: weights not in results/journal3/models.json (status=%s); run scripts/journal3/j3_download.py "
                             "--models <index> on the login node" % (slug, rec.get("status")))
        self.hf_id, self.revision = hf_id, rec["revision"]
        kw = dict(model=hf_id, revision=self.revision, tokenizer_revision=self.revision, dtype="bfloat16", seed=42,
                  max_model_len=max_model_len, gpu_memory_utilization=float(os.environ.get("MEDVERIF_RD2_GPU_UTIL", "0.90")),
                  tensor_parallel_size=int(os.environ.get("MEDVERIF_RD2_TP", "1")),
                  enforce_eager=os.environ.get("MEDVERIF_RD2_EAGER", "1") == "1",
                  download_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"), trust_remote_code=False)
        if family == "gemma3":
            kw["limit_mm_per_prompt"] = {"image": 0}
        self.llm = LLM(**kw)
        self.tok = self.llm.get_tokenizer()
        self.params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=MAX_TOKENS, seed=42)
        self.version = "vllm-" + getattr(vllm, "__version__", "?")
        self.max_len = max_model_len

    def render_chat(self, prompt: str) -> str:
        msgs = [{"role": "user", "content": prompt}]
        try:
            return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False,
                                                thinking_mode="off")
        except TypeError:
            return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def generate(self, prompts):
        ids = [self.tok(self.render_chat(p), add_special_tokens=False)["input_ids"] for p in prompts]
        fits = [len(x) + MAX_TOKENS <= self.max_len for x in ids]
        outs = iter(self.llm.generate([{"prompt_token_ids": x} for x, f in zip(ids, fits) if f], self.params, use_tqdm=False)) \
            if any(fits) else iter([])
        res = []
        for x, f in zip(ids, fits):
            if not f:
                res.append({"raw": "", "error": "PROMPT_TOO_LONG", "n_prompt_tokens": len(x), "n_gen_tokens": 0})
                continue
            c = next(outs).outputs[0]
            res.append({"raw": c.text, "n_prompt_tokens": len(x), "n_gen_tokens": len(c.token_ids),
                        "finish_reason": c.finish_reason})
        return res


class MockGen:
    """Deterministic stub: grounded -> copies the first excerpt dose; closed -> drops the /kg basis every 3rd question."""
    version = "mock"
    hf_id = "mock"
    revision = "mock"

    def __init__(self, qs_by_prompt):
        self.q = qs_by_prompt

    def generate(self, prompts):
        sys.path.insert(0, str(ROOT / "src"))
        from unit_norm_fix import find_spans
        out = []
        for p in prompts:
            q, cond = self.q[p]
            sp = [s for s in find_spans(q["target_sentence"]) if not s.conc]
            dose = sp[0].text if sp else "10 mg"
            h = int(sha256_text(q["qid"])[:4], 16)
            if cond == "closed" and h % 3 == 0:
                dose = re.sub(r"\s*(/|per)\s*(kg|m2|m²)\b", "", dose)
            out.append({"raw": "The recommended dose is %s." % dose, "n_prompt_tokens": len(p) // 4, "n_gen_tokens": 8,
                        "finish_reason": "stop"})
        return out


def run_local(args, qs, conds):
    for slug in args.generators.split(","):
        out = ANS_DIR / ("%s.jsonl" % slug)
        be = None
        for ps in range(args.passes):
            todo = todo_items(qs, slug, conds, out)
            if args.limit:
                todo = todo[: args.limit]
            if not todo:
                break
            if be is None:
                t0 = time.time()
                if args.backend == "mock":
                    be = MockGen({render(q, c): (q, c) for q in qs for c in conds})
                else:
                    be = VLLMGen(slug, args.max_model_len)
                log("RD2_generate", generator=slug, loaded=be.hf_id, revision=be.revision, backend=be.version,
                    load_s=round(time.time() - t0, 1), todo=len(todo))
            for off in range(0, len(todo), args.chunk):
                sel = todo[off: off + args.chunk]
                prompts = [render(q, c) for q, c in sel]
                gens = be.generate(prompts)
                recs = []
                for (q, c), g in zip(sel, gens):
                    ans = clean(g.get("raw"))
                    recs.append(dict({"qid": q["qid"], "drug": q["drug"], "generator": slug, "condition": c, "answer": ans,
                                      "raw_output": g.get("raw"), "hf_model": be.hf_id, "hf_revision": be.revision,
                                      "backend": be.version, "prompt_sha256": PROMPT_SHA[c], "temperature": 0.0, "seed": 42,
                                      "max_tokens": MAX_TOKENS, "pass": ps},
                                     **{k: g.get(k) for k in ("n_prompt_tokens", "n_gen_tokens", "finish_reason", "error")}))
                append_jsonl(out, recs)
                log("RD2_generate", generator=slug, pass_=ps, progress=off + len(sel), total=len(todo),
                    empty=sum(1 for r in recs if not r["answer"]))
        left = len(todo_items(qs, slug, conds, out))
        log("RD2_generate", generator=slug, done=True, left=left)
        if not left and not args.limit and args.backend != "mock":
            mark_done("RD2_generate_%s" % slug, hf_model=LOCAL[slug][0], revision=be.revision if be else "cached",
                      answers=len(qs) * len(conds))


# ------------------------------------------------------------------ OpenRouter
def rd2_spent_usd() -> float:
    tot = 0.0
    for p in RD2_DIR.rglob("*.jsonl"):
        if p == ANSWERS:  # merged copy of answers/<generator>.jsonl -- do not count twice
            continue
        for r in read_jsonl(p):
            c = r.get("api_cost_usd")
            if isinstance(c, (int, float)):
                tot += float(c)
    return tot


def run_openrouter(args, qs, conds):
    from jr_common import GENERATORS, PRICES, chat_pinned, est_cost, tokens
    gens = [g for g in args.generators.split(",") if g]
    bad = [g for g in gens if g not in GENERATORS or GENERATORS[g]["model"] not in PRICES]
    if bad:
        raise SystemExit("unknown / unpriced OpenRouter generator(s) %s (pinned: %s)" % (bad, sorted(GENERATORS)))
    worst = lambda q, c, g: est_cost(GENERATORS[g]["model"], tokens(render(q, c)) + 16, MAX_TOKENS)  # noqa: E731
    plan = {g: todo_items(qs, g, conds, ANS_DIR / ("%s.jsonl" % g)) for g in gens}
    est = {g: round(sum(worst(q, c, g) for q, c in t), 4) for g, t in plan.items()}
    spent = rd2_spent_usd()
    log("RD2_generate", backend="openrouter", todo={g: len(t) for g, t in plan.items()}, worst_case_usd=est,
        spent_usd=round(spent, 4), max_usd=args.max_usd)
    if args.dry_run:
        return
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY not set (source ~/.medverif_keys); no call made")
    if spent + sum(est.values()) > args.max_usd:
        log("RD2_generate", warning="worst-case estimate exceeds --max-usd; will stop at the cap")

    for g in gens:
        out = ANS_DIR / ("%s.jsonl" % g)
        spec = GENERATORS[g]

        def one(item, g=g, spec=spec):
            q, c = item
            try:
                res = chat_pinned(spec, render(q, c), max_tokens=MAX_TOKENS)
                if res["api_model"] and not res["api_model"].startswith(spec["model"].split(":")[0]):
                    raise RuntimeError("model drift: asked %s, served %s" % (spec["model"], res["api_model"]))
                return dict({"qid": q["qid"], "drug": q["drug"], "generator": g, "condition": c, "answer": res.pop("text"),
                             "prompt_sha256": PROMPT_SHA[c], "temperature": 0.0, "seed": 42, "max_tokens": MAX_TOKENS}, **res)
            except Exception as exc:  # noqa: BLE001
                return {"qid": q["qid"], "drug": q["drug"], "generator": g, "condition": c, "answer": "", "error": str(exc)[:300]}

        for ps in range(args.passes):
            todo = todo_items(qs, g, conds, out)
            if args.limit:
                todo = todo[: args.limit]
            for off in range(0, len(todo), 20):
                batch = todo[off: off + 20]
                spent = rd2_spent_usd()
                nxt = sum(worst(q, c, g) for q, c in batch)
                if spent + nxt > args.max_usd:
                    raise SystemExit("BUDGET STOP: spent $%.4f + next batch worst case $%.4f > --max-usd $%.2f" % (spent, nxt, args.max_usd))
                with ThreadPoolExecutor(max_workers=args.workers) as ex:
                    recs = list(ex.map(one, batch))
                append_jsonl(out, recs)
                errs = [r for r in recs if r.get("error")]
                log("RD2_generate", generator=g, pass_=ps, progress=off + len(batch), total=len(todo), errors=len(errs),
                    spent=round(rd2_spent_usd(), 4))
                if len(errs) == len(recs):
                    raise SystemExit("whole batch failed (first error: %s)" % errs[0]["error"])
        left = len(todo_items(qs, g, conds, out))
        log("RD2_generate", generator=g, done=True, left=left)
        if not left and not args.limit:
            mark_done("RD2_generate_%s" % g, model=spec["model"], provider=spec["provider"], answers=len(qs) * len(conds))


# ------------------------------------------------------------------ merge
def merge(qs, conds) -> dict:
    order = {q["qid"]: i for i, q in enumerate(qs)}
    rows, missing = [], {}
    for p in sorted(ANS_DIR.glob("*.jsonl")):
        best = {}
        for r in read_jsonl(p):
            k = (r["qid"], r["condition"])
            if r.get("answer") and k not in best:  # first non-empty answer wins (greedy decoding: re-runs are identical)
                best[k] = r
        missing[p.stem] = len(qs) * len(conds) - len(best)
        rows.extend(best.values())
    rows.sort(key=lambda r: (r["generator"], r["condition"], order.get(r["qid"], 10 ** 9)))
    write_jsonl(ANSWERS, rows)
    return {"answers": len(rows), "missing_by_generator": missing, "out": str(ANSWERS)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["vllm", "openrouter", "mock"], default="vllm")
    ap.add_argument("--generators", default="", help="comma list (default: 4 local for vllm/mock, 2 RD generators for openrouter)")
    ap.add_argument("--array-index", type=int, help="pick one generator from --generators (Slurm array)")
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--limit", type=int, default=0, help="max NEW rows per generator per pass (smoke)")
    ap.add_argument("--passes", type=int, default=3, help="retry passes for empty / failed rows")
    ap.add_argument("--chunk", type=int, default=512)
    ap.add_argument("--max-model-len", type=int, default=4096)
    ap.add_argument("--max-usd", type=float, default=3.0, help="OpenRouter hard cap (whole RD2 ledger)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--merge", action="store_true", help="only merge per-generator files into answers.jsonl")
    args = ap.parse_args()
    if not args.generators:
        args.generators = ",".join(OPENROUTER_DEFAULT if args.backend == "openrouter" else LOCAL_DEFAULT)
    if args.array_index is not None:
        args.generators = args.generators.split(",")[args.array_index]
    assert_frozen(require_questions=True)
    qs = read_jsonl(QUESTIONS)
    conds = [c for c in args.conditions.split(",") if c]
    if args.merge:
        log("RD2_merge", **merge(qs, conds))
        return
    log("RD2_generate", backend=args.backend, generators=args.generators, questions=len(qs), conditions=conds,
        prompt_sha256=PROMPT_SHA, max_tokens=MAX_TOKENS)
    if args.backend == "openrouter":
        run_openrouter(args, qs, conds)
    elif args.dry_run:
        for g in args.generators.split(","):
            log("RD2_generate", generator=g, todo=len(todo_items(qs, g, conds, ANS_DIR / ("%s.jsonl" % g))))
    else:
        run_local(args, qs, conds)


if __name__ == "__main__":
    main()
