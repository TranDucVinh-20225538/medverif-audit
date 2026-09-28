"""OpenRouter chat-completions client. API key from OPENROUTER_API_KEY only (never commit)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_BASE = "https://openrouter.ai/api/v1/chat/completions"


@dataclass
class OpenRouterMeta:
    id: str | None
    model: str | None
    provider: str | None
    quantization: str | None
    raw: dict[str, Any]


def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return key


def chat_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 256,
    seed: int | None = 42,
    provider_order: list[str] | None = None,
    allow_fallbacks: bool = False,
    extra_body: dict[str, Any] | None = None,
    timeout_s: float = 300.0,
) -> tuple[str, OpenRouterMeta]:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if seed is not None:
        body["seed"] = seed
    provider = os.environ.get("MEDVERIF_OPENROUTER_PROVIDER", "").strip()
    order = provider_order or ([provider] if provider else None)
    if order:
        body["provider"] = {"order": order, "allow_fallbacks": allow_fallbacks}
    if extra_body:
        body.update(extra_body)

    req = urllib.request.Request(
        os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE),
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.environ.get("MEDVERIF_OPENROUTER_REFERER", "https://medverif-audit.local"),
            "X-Title": os.environ.get("MEDVERIF_OPENROUTER_TITLE", "medverif-audit"),
        },
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    _ = time.perf_counter() - started

    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    text = message.get("content") or ""
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))

    prov = payload.get("provider") or message.get("provider")
    quant = None
    if isinstance(prov, dict):
        quant = prov.get("quantization") or prov.get("quant")
    meta = OpenRouterMeta(
        id=payload.get("id"),
        model=payload.get("model"),
        provider=prov if isinstance(prov, str) else (prov or {}).get("name") if isinstance(prov, dict) else None,
        quantization=quant,
        raw=payload,
    )
    return text, meta


def assert_no_thinking_leak(text: str) -> None:
    low = text.lower()
    think_open = "<" + "think>"
    think_close = "</" + "think>"
    if "redacted_thinking" in low or think_open in low or think_close in low:
        raise RuntimeError("thinking leak in model output (refusing to score)")
