"""T19: local Llama RAGAS-NLI (transformers bf16, batched greedy gen, p_yes from logits)."""

from __future__ import annotations

import json
import math
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

import torch

from verifiers import v4_ragas_nli as v4
from verifiers.preprocess import verifier_inputs
from verifiers.ragas_nli_prompt import nli_prompt

DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
parse_verdict = v4.parse_verdict


def _model_spec() -> tuple[str, str | None]:
    model = os.environ.get("MEDVERIF_T19_HF_MODEL", DEFAULT_MODEL).strip()
    rev = os.environ.get("MEDVERIF_T19_HF_REVISION", "").strip() or None
    return model, rev


@dataclass
class T19Engine:
    model: Any
    tokenizer: Any
    device: torch.device
    max_model_len: int = 8192
    _t19_meta: dict = field(default_factory=dict)


def render(tokenizer, evidence: str, claim: str) -> str:
    user = nli_prompt(evidence, [claim])
    messages = [{"role": "user", "content": user}]
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )


def _token_id_sets(tokenizer) -> tuple[set[int], set[int]]:
    ones: set[int] = set()
    zeros: set[int] = set()
    for text in ("1", " 1", "0", " 0"):
        ids = tokenizer.encode(text, add_special_tokens=False)
        if not ids:
            continue
        if text.strip() == "1":
            ones.add(ids[-1])
        else:
            zeros.add(ids[-1])
    return ones, zeros


def _p_yes_from_logits(logits: torch.Tensor, ones: set[int], zeros: set[int]) -> float | None:
    lp1 = lp0 = None
    for tid in ones:
        v = float(logits[tid].item())
        lp1 = v if lp1 is None else max(lp1, v)
    for tid in zeros:
        v = float(logits[tid].item())
        lp0 = v if lp0 is None else max(lp0, v)
    if lp1 is None and lp0 is None:
        return None
    if lp1 is None:
        lp1 = -1e9
    if lp0 is None:
        lp0 = -1e9
    m = max(lp1, lp0)
    p1 = math.exp(lp1 - m)
    p0 = math.exp(lp0 - m)
    return p1 / (p1 + p0)


def _verdict_prefix(raw: str) -> str | None:
    idx = raw.find('"verdict"')
    if idx < 0:
        return None
    tail = raw[: idx + len('"verdict"')]
    rest = raw[idx + len('"verdict"') :]
    m = re.match(r"\s*:\s*", rest)
    if not m:
        return None
    return tail + rest[: m.end()]


def load():
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(json.dumps({"t19_load": "enter"}), flush=True)
    offline = os.environ.get("HF_HUB_OFFLINE", "").lower() in ("1", "true", "yes")
    if offline:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    model_id, revision = _model_spec()
    cache = os.environ.get("HUGGINGFACE_HUB_CACHE") or os.environ.get("HF_HOME")
    tok_kw: dict[str, Any] = {"trust_remote_code": True}
    model_kw: dict[str, Any] = {
        "trust_remote_code": True,
        "torch_dtype": torch.bfloat16,
    }
    if cache:
        tok_kw["cache_dir"] = cache
        model_kw["cache_dir"] = cache
    if revision:
        tok_kw["revision"] = revision
        model_kw["revision"] = revision
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True, **tok_kw)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_id, **model_kw)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    load_s = time.perf_counter() - started
    resolved_rev = revision or "main"
    engine = T19Engine(
        model=model,
        tokenizer=tokenizer,
        device=device,
        max_model_len=int(os.environ.get("MEDVERIF_T19_MAX_MODEL_LEN", "8192")),
        _t19_meta={"hf_model": model_id, "hf_revision": resolved_rev},
    )
    print(json.dumps({"loaded_model_s": round(load_s, 2), "hf_model": model_id}), flush=True)
    print(f"loaded model in {load_s:.1f}s", flush=True)
    return engine, tokenizer, None, load_s


@torch.inference_mode()
def _generate_texts(engine: T19Engine, prompts: list[str], max_new_tokens: int = 512) -> list[str]:
    tok = engine.tokenizer
    enc = tok(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=engine.max_model_len - max_new_tokens,
    )
    enc = {k: v.to(engine.model.device) for k, v in enc.items()}
    out_ids = engine.model.generate(
        **enc,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=None,
        pad_token_id=tok.pad_token_id,
    )
    texts = []
    for i in range(len(prompts)):
        inp_len = int(enc["attention_mask"][i].sum().item())
        new_ids = out_ids[i, inp_len:]
        texts.append(tok.decode(new_ids, skip_special_tokens=True))
    return texts


@torch.inference_mode()
def p_yes_probe(
    engine: T19Engine,
    prompt: str,
    raw: str,
    ones: set[int],
    zeros: set[int],
) -> float | None:
    prefix = _verdict_prefix(raw)
    if prefix is None:
        return None
    full = prompt + prefix
    tok = engine.tokenizer
    enc = tok(full, return_tensors="pt", truncation=True, max_length=engine.max_model_len)
    enc = {k: v.to(engine.model.device) for k, v in enc.items()}
    logits = engine.model(**enc).logits[0, -1, :].float().cpu()
    return _p_yes_from_logits(logits, ones, zeros)


def score_batch(llm: T19Engine, tokenizer, _params, pairs: list[dict]) -> list[dict]:
    engine = llm
    meta = engine._t19_meta
    model_name = meta.get("hf_model") or _model_spec()[0]
    revision = meta.get("hf_revision")
    ones, zeros = _token_id_sets(tokenizer)
    prompts = []
    for row in pairs:
        claim, evidence = verifier_inputs(row)
        prompts.append(render(tokenizer, evidence, claim))
    started = time.perf_counter()
    raws = _generate_texts(engine, prompts)
    elapsed = time.perf_counter() - started
    per = elapsed / max(len(pairs), 1)
    slug = os.environ.get("MEDVERIF_T19_SLUG", "t19_ragas_local")
    rows = []
    for row, prompt, raw in zip(pairs, prompts, raws):
        verdict, score = parse_verdict(raw)
        p_yes = p_yes_probe(engine, prompt, raw, ones, zeros)
        if p_yes is None and score is not None:
            p_yes = float(score)
        rows.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": raw,
                "score": score,
                "p_yes": p_yes,
                "verdict": verdict,
                "latency_s": per,
                "verifier": slug,
                "hf_model": model_name,
                "hf_revision": revision,
            }
        )
    return rows
