"""RAGAS-NLI judge (V5) — frontier OpenRouter model, same prompt/parser as V4."""

from __future__ import annotations

import json
import os
import time

from verifiers import v4_ragas_nli as v4

# Logged in notes/t2_models.json — Anthropic only (no overlap with V1/V4/V1b/G/Qwen/Phi/Gemini).
DEFAULT_OR = "anthropic/claude-sonnet-4.6"


def load():
    if os.environ.get("MEDVERIF_USE_OPENROUTER", "").lower() not in ("1", "true", "yes"):
        raise RuntimeError("v5_ragas_nli requires MEDVERIF_USE_OPENROUTER=1")
    from openrouter_runtime import load_openrouter_engine

    or_model = os.environ.get("MEDVERIF_V5_OPENROUTER_MODEL", DEFAULT_OR)
    provider = os.environ.get("MEDVERIF_V5_PROVIDER", "Anthropic")
    # Chat template unused — render() sends raw RAGAS-NLI user text (temperature 0 via _Params).
    tok_model = os.environ.get(
        "MEDVERIF_V5_TOKENIZER_MODEL", "HuggingFaceH4/zephyr-7b-beta"
    )
    tok_rev = os.environ.get("MEDVERIF_V5_TOKENIZER_REVISION") or None
    extra: dict = {}
    if os.environ.get("MEDVERIF_V5_REASONING_JSON"):
        extra = json.loads(os.environ["MEDVERIF_V5_REASONING_JSON"])
    return load_openrouter_engine(
        openrouter_model=or_model,
        tokenizer_model=tok_model,
        tokenizer_revision=tok_rev,
        max_tokens=int(os.environ.get("MEDVERIF_V5_MAX_TOKENS", "512")),
        provider=provider,
        extra_body=extra or None,
        assert_no_thinking=True,
        prompt_suffix=os.environ.get("MEDVERIF_V5_PROMPT_SUFFIX", ""),
    )


def render(tokenizer, evidence: str, claim: str) -> str:
    from verifiers.ragas_nli_prompt import nli_prompt

    del tokenizer  # OpenRouter user message = RAGAS-NLI prompt only (same as V4 task text).
    return nli_prompt(evidence, [claim])


def parse_verdict(raw: str):
    return v4.parse_verdict(raw)


def score_batch(llm, tokenizer, params, pairs: list[dict]) -> list[dict]:
    from verifiers.preprocess import verifier_inputs

    prompts = [
        render(tokenizer, evidence, claim)
        for row in pairs
        for claim, evidence in [verifier_inputs(row)]
    ]
    started = time.perf_counter()
    outputs = llm.generate(prompts, params)
    elapsed = time.perf_counter() - started
    per = elapsed / max(len(pairs), 1)
    rows = []
    metas = getattr(llm, "last_meta", [])
    or_model = os.environ.get("MEDVERIF_V5_OPENROUTER_MODEL", DEFAULT_OR)
    for i, (row, out) in enumerate(zip(pairs, outputs)):
        raw = out.outputs[0].text if out.outputs else ""
        if os.environ.get("MEDVERIF_USE_OPENROUTER", "").lower() in ("1", "true", "yes"):
            from llm_client import assert_no_thinking_leak

            assert_no_thinking_leak(raw)
        verdict, score = parse_verdict(raw)
        rec = {
            "instance_id": row["instance_id"],
            "raw_output": raw,
            "score": score,
            "verdict": verdict,
            "latency_s": per,
            "verifier": "v5_ragas_nli",
            "openrouter_model": or_model,
        }
        if i < len(metas):
            m = metas[i]
            rec.update({
                "api_model": m.model,
                "api_provider": m.provider,
                "api_request_id": m.request_id,
                "api_prompt_tokens": m.prompt_tokens,
                "api_completion_tokens": m.completion_tokens,
                "api_total_tokens": m.total_tokens,
                "api_cost_usd": m.cost_usd,
            })
        rows.append(rec)
    return rows
