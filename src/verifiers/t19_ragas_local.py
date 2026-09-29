"""T19: local Llama RAGAS-NLI (V4/T6-B prompt + parser) with P(yes) at verdict token."""

from __future__ import annotations

import json
import math
import os
import re
import time
from typing import Any

from verifiers import v4_ragas_nli as v4
from verifiers.preprocess import verifier_inputs
from verifiers.ragas_nli_prompt import nli_prompt

DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
_VERDICT_TAIL = re.compile(r'"verdict"\s*:\s*$')


def _model_spec() -> tuple[str, str | None]:
    model = os.environ.get("MEDVERIF_T19_HF_MODEL", DEFAULT_MODEL).strip()
    rev = os.environ.get("MEDVERIF_T19_HF_REVISION", "").strip() or None
    return model, rev


def load():
    import vllm_graceful
    import huggingface_hub.file_download as fd
    from huggingface_hub import model_info
    from vllm import LLM, SamplingParams

    fd.is_xet_available = lambda: False
    model, revision = _model_spec()
    started = time.perf_counter()
    llm = LLM(
        model=model,
        revision=revision,
        dtype="bfloat16",
        seed=42,
        trust_remote_code=True,
        max_model_len=int(os.environ.get("MEDVERIF_T19_MAX_MODEL_LEN", "8192")),
        gpu_memory_utilization=float(os.environ.get("MEDVERIF_T19_GPU_UTIL", "0.90")),
        enforce_eager=True,
        download_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    )
    tokenizer = llm.get_tokenizer()
    try:
        info = model_info(model, revision=revision)
        resolved_rev = info.sha
    except Exception:
        resolved_rev = revision or "main"
    gen_params = SamplingParams(temperature=0.0, max_tokens=512, seed=42)
    probe_params = SamplingParams(temperature=0.0, max_tokens=1, logprobs=20, seed=42)
    load_s = time.perf_counter() - started
    vllm_graceful.register(llm)
    llm._t19_meta = {"hf_model": model, "hf_revision": resolved_rev}
    return llm, tokenizer, (gen_params, probe_params), load_s


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


def _token_id_sets(tokenizer) -> tuple[set[int], set[int], set[int]]:
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
    return ones, zeros, ones | zeros


def _p_yes_from_logprobs(logprobs: Any, ones: set[int], zeros: set[int]) -> float | None:
    if not logprobs:
        return None
    lp1 = None
    lp0 = None
    for tid, lp in logprobs.items():
        if tid in ones:
            lp1 = max(lp1, lp.logprob) if lp1 is not None else lp.logprob
        if tid in zeros:
            lp0 = max(lp0, lp.logprob) if lp0 is not None else lp.logprob
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


def p_yes_probe(
    llm,
    tokenizer,
    probe_params,
    prompt: str,
    raw: str,
    ones: set[int],
    zeros: set[int],
) -> float | None:
    prefix = _verdict_prefix(raw)
    if prefix is None:
        return None
    full = prompt + prefix
    out = llm.generate([full], probe_params)
    if not out or not out[0].outputs:
        return None
    o0 = out[0].outputs[0]
    if o0.logprobs:
        return _p_yes_from_logprobs(o0.logprobs[0], ones, zeros)
    return None


parse_verdict = v4.parse_verdict


def score_batch(llm, tokenizer, params, pairs: list[dict]) -> list[dict]:
    gen_params, probe_params = params
    meta = getattr(llm, "_t19_meta", {})
    model = meta.get("hf_model") or _model_spec()[0]
    revision = meta.get("hf_revision")
    ones, zeros, _ = _token_id_sets(tokenizer)
    prompts = []
    for row in pairs:
        claim, evidence = verifier_inputs(row)
        prompts.append(render(tokenizer, evidence, claim))
    started = time.perf_counter()
    outputs = llm.generate(prompts, gen_params)
    elapsed = time.perf_counter() - started
    per = elapsed / max(len(pairs), 1)
    slug = os.environ.get("MEDVERIF_T19_SLUG", "t19_ragas_local")
    rows = []
    for row, prompt, out in zip(pairs, prompts, outputs):
        raw = out.outputs[0].text if out.outputs else ""
        verdict, score = parse_verdict(raw)
        p_yes = p_yes_probe(llm, tokenizer, probe_params, prompt, raw, ones, zeros)
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
                "hf_model": model,
                "hf_revision": revision,
            }
        )
    return rows
