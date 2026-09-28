"""T6-B zoo: RAGAS-NLI on OpenRouter (model via MEDVERIF_V6_OPENROUTER_MODEL)."""

from __future__ import annotations

import json
import os
import time

from verifiers import v5_ragas_nli as v5

DEFAULT_OR = "openai/gpt-4o-mini"


def load():
    if os.environ.get("MEDVERIF_USE_OPENROUTER", "").lower() not in ("1", "true", "yes"):
        raise RuntimeError("v6_ragas_nli requires MEDVERIF_USE_OPENROUTER=1")
    from openrouter_runtime import load_openrouter_engine

    or_model = os.environ.get("MEDVERIF_V6_OPENROUTER_MODEL", DEFAULT_OR)
    provider = os.environ.get("MEDVERIF_V6_PROVIDER", "OpenAI")
    if "anthropic" in or_model.lower() or "claude" in or_model.lower():
        provider = os.environ.get("MEDVERIF_V6_PROVIDER", "Anthropic")
    elif "meta-llama" in or_model.lower():
        provider = os.environ.get("MEDVERIF_V6_PROVIDER", "DeepInfra")
    elif "mistral" in or_model.lower():
        provider = os.environ.get("MEDVERIF_V6_PROVIDER", "DeepInfra")
    tok_model = os.environ.get(
        "MEDVERIF_V6_TOKENIZER_MODEL", "HuggingFaceH4/zephyr-7b-beta"
    )
    tok_rev = os.environ.get("MEDVERIF_V6_TOKENIZER_REVISION") or None
    extra: dict = {}
    if os.environ.get("MEDVERIF_V6_REASONING_JSON"):
        extra = json.loads(os.environ["MEDVERIF_V6_REASONING_JSON"])
    return load_openrouter_engine(
        openrouter_model=or_model,
        tokenizer_model=tok_model,
        tokenizer_revision=tok_rev,
        max_tokens=int(os.environ.get("MEDVERIF_V6_MAX_TOKENS", "512")),
        provider=provider,
        extra_body=extra or None,
        assert_no_thinking=True,
        prompt_suffix=os.environ.get("MEDVERIF_V6_PROMPT_SUFFIX", ""),
    )


# Reuse v5 prompt path (raw RAGAS-NLI user text).
render = v5.render
parse_verdict = v5.parse_verdict


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
    slug = os.environ.get("MEDVERIF_V6_VERIFIER_SLUG", "v6_ragas_nli")
    or_model = os.environ.get("MEDVERIF_V6_OPENROUTER_MODEL", DEFAULT_OR)
    rows = []
    metas = getattr(llm, "last_meta", [])
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
            "verifier": slug,
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
