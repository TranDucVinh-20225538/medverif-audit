"""MedScore via OpenRouter gpt-4o-mini (T6-B zoo). Same prompt/parser as V1."""

from __future__ import annotations

import os
import time

from v1_parser import released_parse_verification_output, released_verdict

from verifiers import v1_medscore as v1

MODEL = "openai/gpt-4o-mini"
TOK_MODEL = os.environ.get(
    "MEDVERIF_V1C_TOKENIZER_MODEL", "mistralai/Mistral-Small-24B-Instruct-2501"
)
TOK_REV = os.environ.get(
    "MEDVERIF_V1C_TOKENIZER_REVISION", "9527884be6e5616bdd54de542f9ae13384489724"
)


def format_input(evidence: str, claim: str) -> str:
    return v1.format_input(evidence, claim)


def load():
    if os.environ.get("MEDVERIF_USE_OPENROUTER", "").lower() not in ("1", "true", "yes"):
        raise RuntimeError("v1c_medscore requires MEDVERIF_USE_OPENROUTER=1")
    from openrouter_runtime import load_openrouter_engine

    or_model = os.environ.get("MEDVERIF_V1C_OPENROUTER_MODEL", MODEL)
    provider = os.environ.get("MEDVERIF_V1C_PROVIDER", "OpenAI")
    return load_openrouter_engine(
        openrouter_model=or_model,
        tokenizer_model=TOK_MODEL,
        tokenizer_revision=TOK_REV,
        max_tokens=256,
        provider=provider,
    )


def render(tokenizer, evidence: str, claim: str) -> str:
    user = format_input(evidence, claim)
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )


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
    for i, (row, out) in enumerate(zip(pairs, outputs)):
        raw = out.outputs[0].text if out.outputs else ""
        rec = {
            "instance_id": row["instance_id"],
            "raw_output": raw,
            "released_parser_score": released_parse_verification_output(raw),
            "verdict": released_verdict(raw),
            "latency_s": per,
            "verifier": "v1c_medscore",
            "openrouter_model": os.environ.get("MEDVERIF_V1C_OPENROUTER_MODEL", MODEL),
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
