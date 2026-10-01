#!/usr/bin/env python3
"""(J3-JG) Small local LLM judges with vLLM: one model per Slurm array task (resumable by instance_id).

Protocol = the paper's RAGAS-NLI judge (v4_ragas_nli local path / v6 API path / T19 local Llama): user turn =
nli_prompt(evidence, [claim]) from the frozen RAGAS prompt (vendored in j3_ragas_prompt.py), rendered with the model's
chat template (add_generation_prompt, enable_thinking=False when supported; tokenized without re-adding BOS); greedy (temperature 0, seed 42),
max_tokens 512; verdict = first statement's 0/1 (PARSE_FAIL otherwise).  Continuous score p_yes = P('1') /
(P('1') + P('0')) at the verdict digit, from the top-20 logprobs vLLM returns for that generated token (for the
threshold-free inversion / AUC); falls back to the 0/1 score when the digit is not found.
Model weights: exact revision recorded by the login-node download step (results/journal3/models.json), loaded offline.
Packs: card (frozen main DOSE card, 958), rag (journal RAG pack, 1622), rd (real-dose answers, 1451).
Output: results/journal3/judges/scores/<slug>__<pack>.jsonl ; marker J3_JG_<slug>.done when all packs complete.
Backends: vllm (default), hf (transformers fallback, used automatically if vLLM cannot load the model), mock
(MEDVERIF_J3_MOCK=1 or --backend mock: deterministic stub, for smoke tests without GPU).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from j3_common import J3, JUDGE_SCORES, MOCK, append_jsonl, done_ids, is_done, log, mark_done, pack_rows  # noqa: E402
from j3_models import JUDGE_PACKS, judge  # noqa: E402
from j3_ragas_prompt import PROMPT_ID, nli_prompt, parse_verdict  # noqa: E402

MAX_TOKENS = 512
_VERDICT_PREFIX = re.compile(r'"verdict"\s*:\s*$')


def render(tokenizer, evidence: str, claim: str) -> str:
    messages = [{"role": "user", "content": nli_prompt(evidence, [claim])}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def verdict_step(pieces: list):
    """Index of the first generated digit token that directly follows '"verdict":' (None if absent)."""
    text = ""
    for i, piece in enumerate(pieces):
        if piece.strip()[:1] in ("0", "1") and _VERDICT_PREFIX.search(text):
            return i
        text += piece
    return None


def p_yes_from_step(cands: dict):
    """cands = {decoded candidate token: logprob} at the verdict step -> P('1') / (P('1') + P('0'))."""
    p1 = sum(math.exp(lp) for tok, lp in cands.items() if tok.strip() == "1")
    p0 = sum(math.exp(lp) for tok, lp in cands.items() if tok.strip() == "0")
    return p1 / (p1 + p0) if (p1 + p0) > 0 else None


def p_yes_from_steps(pieces: list, step_logprobs: list):
    i = verdict_step(pieces)
    return None if i is None else p_yes_from_step(step_logprobs[i])


class VLLMBackend:
    name = "vllm"

    def __init__(self, hf_id: str, revision: str | None, family: str, max_model_len: int):
        import vllm
        from vllm import LLM, SamplingParams

        kw = dict(model=hf_id, revision=revision, tokenizer_revision=revision, dtype="bfloat16", seed=42,
                  max_model_len=max_model_len, gpu_memory_utilization=float(os.environ.get("MEDVERIF_J3_GPU_UTIL", "0.85")),
                  enforce_eager=os.environ.get("MEDVERIF_J3_EAGER", "1") == "1",
                  download_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"), trust_remote_code=False)
        if family == "gemma3":
            kw["limit_mm_per_prompt"] = {"image": 0}  # text-only use of the multimodal MedGemma
        try:
            self.llm = LLM(**kw)
        except TypeError:
            kw.pop("limit_mm_per_prompt", None)
            self.llm = LLM(**kw)
        self.tok = self.llm.get_tokenizer()
        self.params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=MAX_TOKENS, seed=42, logprobs=20)
        self.version = getattr(vllm, "__version__", "?")
        self.max_len = max_model_len

    def generate(self, prompts: list) -> list:
        # token ids of the rendered chat prompt WITHOUT re-adding special tokens (the chat template already carries BOS;
        # passing the string would double it for Llama / Gemma)
        inputs = [{"prompt_token_ids": self.tok(p, add_special_tokens=False)["input_ids"]} for p in prompts]
        fits = [len(x["prompt_token_ids"]) + MAX_TOKENS <= self.max_len for x in inputs]
        outs = iter(self.llm.generate([x for x, f in zip(inputs, fits) if f], self.params, use_tqdm=False)) if any(fits) else iter([])
        res = []
        for x, f in zip(inputs, fits):
            if not f:  # cannot happen on the chain-3 packs (prompts ~1-2.5k tokens); kept so one row cannot kill a batch
                res.append({"raw": "PROMPT_TOO_LONG", "p_yes": None, "n_prompt_tokens": len(x["prompt_token_ids"]), "n_gen_tokens": 0})
                continue
            o = next(outs)
            c = o.outputs[0]
            pieces = [self.tok.decode([tid]) for tid in c.token_ids]
            i, py = verdict_step(pieces), None
            if i is not None and c.logprobs and i < len(c.logprobs):
                py = p_yes_from_step({(v.decoded_token if getattr(v, "decoded_token", None) is not None else self.tok.decode([k])): v.logprob
                                      for k, v in c.logprobs[i].items()})
            res.append({"raw": c.text, "p_yes": py,
                        "n_prompt_tokens": len(o.prompt_token_ids or []), "n_gen_tokens": len(c.token_ids)})
        return res


class HFBackend:
    """transformers fallback: greedy generation, p_yes from a forward pass at the verdict position (T19 method)."""
    name = "hf"

    def __init__(self, hf_id: str, revision: str | None, family: str, max_model_len: int):
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(hf_id, revision=revision)
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.tok.padding_side = "left"
        try:
            self.model = AutoModelForCausalLM.from_pretrained(hf_id, revision=revision, torch_dtype=torch.bfloat16)
        except Exception:  # noqa: BLE001  (Gemma-3 multimodal checkpoints)
            from transformers import AutoModelForImageTextToText

            self.model = AutoModelForImageTextToText.from_pretrained(hf_id, revision=revision, torch_dtype=torch.bfloat16)
        self.model = self.model.to("cuda" if torch.cuda.is_available() else "cpu").eval()
        self.max_len = max_model_len
        self.version = "transformers-" + transformers.__version__

    def generate(self, prompts: list) -> list:
        torch = self.torch
        res = []
        for i in range(0, len(prompts), 8):
            chunk = prompts[i:i + 8]
            enc = self.tok(chunk, return_tensors="pt", padding=True, add_special_tokens=False).to(self.model.device)
            with torch.inference_mode():
                out = self.model.generate(**enc, max_new_tokens=MAX_TOKENS, do_sample=False, temperature=None, top_p=None,
                                          pad_token_id=self.tok.pad_token_id, output_scores=True, return_dict_in_generate=True)
            L = enc["input_ids"].shape[1]
            for b in range(len(chunk)):
                ids = out.sequences[b, L:].tolist()
                pieces = [self.tok.decode([tid]) for tid in ids]
                i, py = verdict_step(pieces), None
                if i is not None:
                    top = torch.topk(torch.log_softmax(out.scores[i][b].float(), -1), 20)
                    py = p_yes_from_step({self.tok.decode([int(k)]): float(v) for v, k in zip(top.values, top.indices)})
                raw = self.tok.decode(ids, skip_special_tokens=True)
                res.append({"raw": raw, "p_yes": py, "n_prompt_tokens": int(enc["attention_mask"][b].sum()),
                            "n_gen_tokens": sum(1 for t in ids if t != self.tok.pad_token_id)})
        return res


class MockBackend:
    """Deterministic stub: PASS iff every number in the claim occurs in the evidence (no GPU/model)."""
    name = "mock"
    version = "mock"

    class _Tok:
        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, **kw):
            return "<user>" + messages[0]["content"] + "<assistant>"

    def __init__(self, *a, **k):
        self.tok = self._Tok()

    def generate(self, prompts: list) -> list:
        out = []
        for p in prompts:
            tail = p[p.rfind("input: "):]
            try:
                inp = json.loads(tail[len("input: "):tail.rfind("}") + 1])
                ctx, st = inp["context"], inp["statements"][0]
            except Exception:  # noqa: BLE001
                ctx, st = "", ""
            nums = re.findall(r"\d+(?:\.\d+)?", st)
            ok = all(n in ctx for n in nums)
            pv = 0.9 if ok else 0.2
            out.append({"raw": json.dumps({"statements": [{"statement": st, "reason": "mock", "verdict": int(ok)}]}),
                        "p_yes": pv, "n_prompt_tokens": len(p) // 4, "n_gen_tokens": 40})
        return out


def load_backend(kind: str, hf_id: str, revision, family: str, max_model_len: int):
    if kind == "mock" or MOCK:
        return MockBackend()
    if kind in ("auto", "vllm"):
        try:
            return VLLMBackend(hf_id, revision, family, max_model_len)
        except Exception as exc:  # noqa: BLE001
            if kind == "vllm":
                raise
            log("J3_JG", vllm_failed="%s: %s" % (type(exc).__name__, str(exc)[:400]), fallback="hf")
    return HFBackend(hf_id, revision, family, max_model_len)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--array-index", type=int)
    ap.add_argument("--model", help="slug from j3_models.JUDGES")
    ap.add_argument("--packs", default=",".join(JUDGE_PACKS))
    ap.add_argument("--backend", default=os.environ.get("MEDVERIF_J3_BACKEND", "auto"), choices=["auto", "vllm", "hf", "mock"])
    ap.add_argument("--limit", type=int, default=int(os.environ.get("MEDVERIF_J3_LIMIT", "0") or 0), help="max NEW rows per pack (smoke)")
    ap.add_argument("--chunk", type=int, default=256)
    ap.add_argument("--max-model-len", type=int, default=8192)
    ap.add_argument("--out-dir", default=str(JUDGE_SCORES))
    args = ap.parse_args()
    slug, hf_id, params_b, size_gb, family, gated = judge(args.array_index if args.array_index is not None else args.model)
    stage = "J3_JG_%s" % slug
    if is_done(stage) and not args.limit:
        log(stage, skipped="marker present")
        return
    models = json.loads((J3 / "models.json").read_text()) if (J3 / "models.json").is_file() else {}
    mrec = models.get(slug) or {}
    if not (MOCK or args.backend == "mock"):
        if mrec.get("status") == "skipped":
            mark_done(stage, skipped=mrec.get("reason"), hf_id=hf_id)
            log(stage, skipped=mrec.get("reason"))
            return
        if mrec.get("status") != "ok":
            raise SystemExit("%s: weights not downloaded (results/journal3/models.json status=%s); run the login-node download "
                             "step: bash jobs/run_journal_chain3.sh (or python scripts/journal3/j3_download.py)" % (slug, mrec.get("status")))
    revision = mrec.get("revision")
    out_dir = Path(args.out_dir)
    packs = [p for p in args.packs.split(",") if p]
    todo_by_pack = {}
    for pack in packs:
        out = out_dir / ("%s__%s.jsonl" % (slug, pack))
        have = done_ids(out)
        rows = [r for r in pack_rows(pack) if r["instance_id"] not in have]
        todo_by_pack[pack] = rows[:args.limit] if args.limit else rows
    if not any(todo_by_pack.values()):
        if not args.limit:
            mark_done(stage, hf_id=hf_id, revision=revision, packs=packs, rows={p: len(done_ids(out_dir / ("%s__%s.jsonl" % (slug, p)))) for p in packs})
        log(stage, nothing_to_do=True)
        return
    t0 = time.time()
    be = load_backend(args.backend, hf_id, revision, family, args.max_model_len)
    log(stage, loaded=hf_id, revision=revision, backend=be.name, backend_version=be.version, load_s=round(time.time() - t0, 1),
        todo={p: len(v) for p, v in todo_by_pack.items()})
    for pack, rows in todo_by_pack.items():
        out = out_dir / ("%s__%s.jsonl" % (slug, pack))
        t1 = time.time()
        for off in range(0, len(rows), args.chunk):
            sel = rows[off:off + args.chunk]
            prompts = [render(be.tok, r["evidence"], r["claim"]) for r in sel]
            gens = be.generate(prompts)
            recs = []
            for r, g in zip(sel, gens):
                verdict, score = parse_verdict(g["raw"])
                recs.append({"instance_id": r["instance_id"], "verdict": verdict, "score": score, "p_yes": g["p_yes"],
                             "raw_output": g["raw"], "n_prompt_tokens": g["n_prompt_tokens"], "n_gen_tokens": g["n_gen_tokens"],
                             "verifier": "j3_" + slug, "hf_model": hf_id, "hf_revision": revision, "backend": be.name,
                             "backend_version": be.version, "prompt": PROMPT_ID, "temperature": 0.0, "seed": 42})
            append_jsonl(out, recs)
            log(stage, pack=pack, progress=off + len(sel), total=len(rows), secs=round(time.time() - t1),
                parse_fail=sum(1 for x in recs if x["verdict"] == "PARSE_FAIL"))
    left = {}
    for p in packs:
        have = done_ids(out_dir / ("%s__%s.jsonl" % (slug, p)))
        left[p] = sum(1 for r in pack_rows(p) if r["instance_id"] not in have)
    if not any(left.values()) and not args.limit:
        mark_done(stage, hf_id=hf_id, revision=revision, backend=be.name, backend_version=be.version, packs=packs,
                  secs=round(time.time() - t0))
    log(stage, done=True, left=left)


if __name__ == "__main__":
    main()
