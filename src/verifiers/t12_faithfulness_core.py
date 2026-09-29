"""Shared OpenRouter LLM judge for T12 framework pins (RAGAS / DeepEval / TruLens defaults)."""

from __future__ import annotations

import json
import os
import time
from typing import Callable

from verifiers.preprocess import verifier_inputs

TOK_MODEL = "mistralai/Mistral-Small-24B-Instruct-2501"
TOK_REV = "9527884be6e5616bdd54de542f9ae13384489724"

PROMPTS: dict[str, str] = {
    "t12_ragas_faithfulness": (
        "You are evaluating faithfulness (RAGAS-style). "
        "Decide if the claim is fully supported by the evidence text.\n\n"
        "Evidence:\n{evidence}\n\nClaim:\n{claim}\n\n"
        'Reply with JSON only: {{"faithful": true|false, "reason": "..."}}'
    ),
    "t12_deepeval_faithfulness": (
        "You are DeepEval FaithfulnessMetric (threshold 0.5). "
        "Score how faithful the claim is to the evidence from 0.0 to 1.0.\n\n"
        "Evidence:\n{evidence}\n\nClaim:\n{claim}\n\n"
        'Reply with JSON only: {{"score": <float>, "reason": "..."}}'
    ),
    "t12_trulens_groundedness": (
        "You are TruLens groundedness feedback. "
        "Score groundedness of the claim in the evidence from 0.0 to 1.0.\n\n"
        "Evidence:\n{evidence}\n\nClaim:\n{claim}\n\n"
        'Reply with JSON only: {{"groundedness": <float>, "reason": "..."}}'
    ),
}


def _env_pair(slug: str) -> tuple[str, str]:
    mapping = {
        "t12_ragas_faithfulness": ("MEDVERIF_T12_RAGAS_MODEL", "MEDVERIF_T12_RAGAS_PROVIDER"),
        "t12_deepeval_faithfulness": ("MEDVERIF_T12_DEEVAL_MODEL", "MEDVERIF_T12_DEEVAL_PROVIDER"),
        "t12_trulens_groundedness": ("MEDVERIF_T12_TRULENS_MODEL", "MEDVERIF_T12_TRULENS_PROVIDER"),
    }
    return mapping[slug]


def load_for(slug: str):
    if os.environ.get("MEDVERIF_USE_OPENROUTER", "").lower() not in ("1", "true", "yes"):
        raise RuntimeError(f"{slug} requires MEDVERIF_USE_OPENROUTER=1")
    from openrouter_runtime import load_openrouter_engine

    model_key, prov_key = _env_pair(slug)
    or_model = os.environ.get(model_key, "")
    provider = os.environ.get(prov_key, "")
    if not or_model:
        from verifier_registry import expected_openrouter

        spec = expected_openrouter(slug)
        or_model = spec["openrouter_model"]
        provider = spec.get("provider") or ""
    return load_openrouter_engine(
        openrouter_model=or_model,
        tokenizer_model=TOK_MODEL,
        tokenizer_revision=TOK_REV,
        max_tokens=256,
        provider=provider or None,
    )


def render(tokenizer, slug: str, evidence: str, claim: str) -> str:
    tmpl = PROMPTS[slug]
    user = tmpl.format(evidence=evidence, claim=claim)
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )


def _parse_json_blob(raw: str) -> dict | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def verdict_for(slug: str, raw: str) -> tuple[str, float | None]:
    payload = _parse_json_blob(raw)
    if not payload:
        return "PARSE_FAIL", None
    if slug == "t12_ragas_faithfulness":
        val = payload.get("faithful")
        if val is True:
            return "PASS", 1.0
        if val is False:
            return "FAIL", 0.0
        return "PARSE_FAIL", None
    if slug == "t12_deepeval_faithfulness":
        try:
            score = float(payload.get("score"))
        except (TypeError, ValueError):
            return "PARSE_FAIL", None
        return ("PASS" if score >= 0.5 else "FAIL"), score
    if slug == "t12_trulens_groundedness":
        try:
            score = float(payload.get("groundedness"))
        except (TypeError, ValueError):
            return "PARSE_FAIL", None
        return ("PASS" if score >= 0.5 else "FAIL"), score
    return "PARSE_FAIL", None


def score_batch_factory(slug: str) -> Callable:
    def score_batch(llm, tokenizer, params, pairs: list[dict]) -> list[dict]:
        prompts = [
            render(tokenizer, slug, evidence, claim)
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
            verdict, score = verdict_for(slug, raw)
            rec = {
                "instance_id": row["instance_id"],
                "raw_output": raw,
                "score": score,
                "verdict": verdict,
                "latency_s": per,
                "verifier": slug,
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

    return score_batch
