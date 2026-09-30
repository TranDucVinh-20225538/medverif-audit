"""RAGAS-NLI only. OpenRouter: Llama-3.3-70B-Instruct (see notes/openrouter_verifiers.json)."""

from __future__ import annotations

import json
import os
import time

from verifiers.ragas_nli_prompt import nli_prompt

MODEL = "Qwen/Qwen3-14B"
REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"
LLAMA_OR = "meta-llama/llama-3.3-70b-instruct"
LLAMA_TOK = "meta-llama/Llama-3.3-70B-Instruct"


def _tokenizer_spec() -> tuple[str, str | None]:
    tok = os.environ.get("MEDVERIF_V4_TOKENIZER_MODEL", "").strip()
    rev = os.environ.get("MEDVERIF_V4_TOKENIZER_REVISION", "").strip() or None
    if tok:
        return tok, rev
    or_model = os.environ.get("MEDVERIF_V4_OPENROUTER_MODEL", LLAMA_OR)
    if "llama-3.3-70b" in or_model.lower():
        return LLAMA_TOK, rev
    return MODEL, REVISION


def load():
    if os.environ.get("MEDVERIF_USE_OPENROUTER", "").lower() in ("1", "true", "yes"):
        from openrouter_runtime import load_openrouter_engine

        or_model = os.environ.get("MEDVERIF_V4_OPENROUTER_MODEL", LLAMA_OR)
        provider = os.environ.get("MEDVERIF_V4_PROVIDER", "DeepInfra")
        extra: dict = {}
        if os.environ.get("MEDVERIF_V4_REASONING_JSON"):
            import json as _json

            extra.update(_json.loads(os.environ["MEDVERIF_V4_REASONING_JSON"]))
        tok_model, tok_rev = _tokenizer_spec()
        suffix = os.environ.get("MEDVERIF_V4_PROMPT_SUFFIX", "")
        return load_openrouter_engine(
            openrouter_model=or_model,
            tokenizer_model=tok_model,
            tokenizer_revision=tok_rev,
            max_tokens=int(os.environ.get("MEDVERIF_V4_MAX_TOKENS", "512")),
            provider=provider,
            extra_body=extra or None,
            assert_no_thinking=True,
            prompt_suffix=suffix,
        )

    import vllm_graceful
    import huggingface_hub.file_download as fd
    from vllm import LLM, SamplingParams

    fd.is_xet_available = lambda: False
    started = time.perf_counter()
    llm = LLM(
        model=MODEL,
        revision=REVISION,
        dtype="bfloat16",
        seed=42,
        trust_remote_code=True,
        max_model_len=8192,
        gpu_memory_utilization=0.90,
        enforce_eager=True,
        download_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    )
    tokenizer = llm.get_tokenizer()
    params = SamplingParams(temperature=0.0, max_tokens=512, seed=42)
    vllm_graceful.register(llm)
    return llm, tokenizer, params, time.perf_counter() - started


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


def parse_verdict(raw: str) -> tuple[str, float | None]:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return "PARSE_FAIL", None
    try:
        payload = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return "PARSE_FAIL", None
    statements = payload.get("statements") if isinstance(payload, dict) else None
    if not isinstance(statements, list) or not statements:
        return "PARSE_FAIL", None
    verdict = statements[0].get("verdict") if isinstance(statements[0], dict) else None
    if verdict == 1:
        return "PASS", 1.0
    if verdict == 0:
        return "FAIL", 0.0
    return "PARSE_FAIL", None


def score_batch(llm, tokenizer, params, pairs: list[dict]) -> list[dict]:
    prompts = [render(tokenizer, row["evidence"], row["claim"]) for row in pairs]
    started = time.perf_counter()
    outputs = llm.generate(prompts, params)
    elapsed = time.perf_counter() - started
    per = elapsed / max(len(pairs), 1)
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
            "verifier": "v4_ragas_nli",
        }
        if i < len(metas):
            m = metas[i]
            rec.update(
                {
                    "api_model": m.model,
                    "api_provider": m.provider,
                    "api_request_id": m.request_id,
                    "api_prompt_tokens": m.prompt_tokens,
                    "api_completion_tokens": m.completion_tokens,
                    "api_total_tokens": m.total_tokens,
                    "api_cost_usd": m.cost_usd,
                }
            )
        rows.append(rec)
    return rows
