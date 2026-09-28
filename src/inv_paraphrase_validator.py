"""Combined fluency + meaning validator for INV paraphrase (OpenRouter)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from llm_client import chat
from openrouter_runtime import load_tokenizer
from stage12_llm import render

VAL_SYSTEM = (
    "You judge medical sentence paraphrases. Reply with JSON only, no markdown."
)

VAL_USER_TEMPLATE = """Original (A):
{original}

Rewrite (B):
{rewrite}

Is B grammatical and natural? Does B state exactly the same facts as A — no added/removed causal relations, conditions, qualifiers, or subjects?

Answer JSON: {{"fluent": "yes" or "no", "same_meaning": "yes" or "no", "reason": "brief"}}

Examples that must be rejected (same_meaning=no and/or fluent=no):
- Added causation: "can lead to" when A only lists co-occurring factors.
- Wrong drug framing: "as etanercept" when A names etanercept as the administered drug.
- Wrong indication framing: "for tranexamic acid" when A gives dosing of tranexamic acid, not a reason.
- Subject changed: passive rewrite shifts who receives the antibiotic vs A."""

DEFAULT_VAL_MODEL = "google/gemini-2.5-flash"
CANDIDATE_MODELS = (
    "google/gemini-2.5-flash",
    "openai/gpt-4o-mini",
)


def meaning_hard_reject(original: str, rewrite: str) -> str | None:
    """Pilot reference failures that judges may miss."""
    o = (original or "").strip().lower()
    r = (rewrite or "").strip().lower()
    if re.search(r"\b(can lead to|leads to|leading to)\b", r) and not re.search(
        r"\b(can lead|leads to|lead to|cause|causes|causing)\b", o
    ):
        return "added_causation"
    if re.search(r"\bas etanercept\b", r):
        return "drug_framing_as"
    if re.search(r"\bfor tranexamic acid\b", r) and o.startswith("tranexamic"):
        return "indication_framing_for"
    if r.startswith("a single dose") and o.startswith("the most effective"):
        return "subject_reorder"
    return None


def _parse_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[^{}]*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _yes_no(val: Any) -> str:
    s = str(val or "").strip().lower()
    if s in {"yes", "y", "true"}:
        return "yes"
    if s in {"no", "n", "false"}:
        return "no"
    return "?"


def pick_validator_model(provider: str | None = None) -> tuple[str, str]:
    """Return (model_id, tokenizer_id). Logs choice via print."""
    forced = os.environ.get("MEDVERIF_PARA_VAL_MODEL", "").strip()
    tok_id = os.environ.get("MEDVERIF_PARA_VAL_TOKENIZER", "meta-llama/Llama-3.2-3B-Instruct")
    if forced:
        print(json.dumps({"inv_validator_model": forced}), flush=True)
        return forced, tok_id
    tok = load_tokenizer(tok_id, None)
    last_err: Exception | None = None
    for model in CANDIDATE_MODELS:
        try:
            if meaning_hard_reject(
                "Etanercept is given by subcutaneous injection, 50 mg once weekly.",
                "A subcutaneous injection of 50 mg is administered once weekly as etanercept.",
            ):
                chat(
                    model=model,
                    messages=[{"role": "user", "content": "Reply with JSON: {\"ok\": true}"}],
                    max_tokens=16,
                    temperature=0.0,
                    provider=provider,
                    allow_fallbacks=True,
                )
                print(json.dumps({"inv_validator_model": model}), flush=True)
                return model, tok_id
        except Exception as exc:  # noqa: BLE001 — probe loop
            last_err = exc
            continue
    print(json.dumps({"inv_validator_model": DEFAULT_VAL_MODEL}), flush=True)
    return DEFAULT_VAL_MODEL, tok_id


def validate_pair_llm_only(
    original: str,
    rewrite: str,
    *,
    model: str,
    tok,
    provider: str | None,
) -> tuple[bool, dict[str, Any]]:
    """Gemini/OpenRouter judge only — no meaning_hard_reject."""
    user = VAL_USER_TEMPLATE.format(original=original.strip(), rewrite=rewrite.strip())
    prompt = render(tok, VAL_SYSTEM, user)
    resp = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.0,
        provider=provider,
        allow_fallbacks=True,
    )
    parsed = _parse_json(resp.text or "") or {}
    fluent = _yes_no(parsed.get("fluent"))
    same = _yes_no(parsed.get("same_meaning"))
    passed = fluent == "yes" and same == "yes"
    meta = {
        "provider": resp.provider,
        "request_id": resp.request_id,
        "model": resp.model or model,
        "tokens": resp.total_tokens,
        "cost_usd": resp.cost_usd,
        "fluent": fluent,
        "same_meaning": same,
        "reason": parsed.get("reason"),
        "raw": resp.text,
    }
    return passed, meta


def validate_pair(
    original: str,
    rewrite: str,
    *,
    model: str,
    tok,
    provider: str | None,
) -> tuple[bool, dict[str, Any]]:
    hard = meaning_hard_reject(original, rewrite)
    if hard:
        return False, {"hard_reject": hard, "fluent": "no", "same_meaning": "no", "reason": hard}
    return validate_pair_llm_only(original, rewrite, model=model, tok=tok, provider=provider)
