"""OpenRouter chat client: pinned provider, retries, cost log → results/api_cost.json."""

from __future__ import annotations

import http.client
import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
COST_PATH = ROOT / "results" / "api_cost.json"
DEFAULT_BASE = "https://openrouter.ai/api/v1/chat/completions"
MAX_WORKERS = 10

_lock = threading.Lock()
_calls: list[dict[str, Any]] = []
_inflight = threading.Semaphore(int(os.environ.get("MEDVERIF_OR_MAX_INFLIGHT", "8")))


def _retry_sleep(attempt: int, exc: Exception) -> None:
    wait: float | None = None
    if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
        raw = exc.headers.get("Retry-After") if exc.headers else None
        if raw is not None:
            try:
                wait = float(raw)
            except ValueError:
                wait = None
    if wait is None:
        wait = min(120.0, 5.0 * (2**attempt) + random.uniform(0, 3.0))
    time.sleep(wait)


@dataclass
class LLMResponse:
    text: str
    model: str | None
    provider: str | None
    request_id: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None
    latency_s: float
    reasoning: str | None = None


def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return key


def _usage_cost(payload: dict[str, Any]) -> float | None:
    usage = payload.get("usage") or {}
    if "cost" in usage and usage["cost"] is not None:
        return float(usage["cost"])
    if "total_cost" in payload and payload["total_cost"] is not None:
        return float(payload["total_cost"])
    return None


def _provider_name(payload: dict[str, Any]) -> str | None:
    prov = payload.get("provider")
    if isinstance(prov, str):
        return prov
    if isinstance(prov, dict):
        return prov.get("name") or prov.get("slug")
    return None


def _record_call(entry: dict[str, Any]) -> None:
    with _lock:
        _calls.append(entry)
        _flush_cost_file()


def _flush_cost_file() -> None:
    COST_PATH.parent.mkdir(parents=True, exist_ok=True)
    total_cost = sum(c.get("cost_usd") or 0.0 for c in _calls)
    total_tokens = sum(c.get("total_tokens") or 0 for c in _calls)
    payload = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_calls": len(_calls),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "calls": _calls,
    }
    COST_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def chat(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 256,
    seed: int | None = 42,
    provider: str | None = None,
    allow_fallbacks: bool = False,
    extra_body: dict[str, Any] | None = None,
    timeout_s: float = 300.0,
    max_retries: int = 12,
    refuse_reasoning_only: bool = True,
) -> LLMResponse:
    prov = provider or os.environ.get("MEDVERIF_OPENROUTER_PROVIDER", "").strip() or None
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if seed is not None:
        body["seed"] = seed
    if prov:
        body["provider"] = {"order": [prov], "allow_fallbacks": allow_fallbacks}
    if extra_body:
        body.update(extra_body)

    url = os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE)
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            with _inflight:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(body).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {_api_key()}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.environ.get(
                            "MEDVERIF_OPENROUTER_REFERER", "https://medverif-audit.local"
                        ),
                        "X-Title": os.environ.get("MEDVERIF_OPENROUTER_TITLE", "medverif-audit"),
                    },
                    method="POST",
                )
                t0 = time.perf_counter()
                with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            latency = time.perf_counter() - t0
            choice = (payload.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            text = message.get("content") or ""
            if isinstance(text, list):
                text = "".join(
                    part.get("text", "") for part in text if isinstance(part, dict)
                )
            reasoning = message.get("reasoning")
            if isinstance(reasoning, str) and not reasoning.strip():
                reasoning = None
            if refuse_reasoning_only and not str(text).strip() and reasoning:
                raise RuntimeError(
                    "model returned empty content with reasoning present (refusing to score)"
                )
            usage = payload.get("usage") or {}
            pt = int(usage.get("prompt_tokens") or 0)
            ct = int(usage.get("completion_tokens") or 0)
            tt = int(usage.get("total_tokens") or pt + ct)
            cost = _usage_cost(payload)
            out = LLMResponse(
                text=text,
                model=payload.get("model"),
                provider=_provider_name(payload),
                request_id=payload.get("id"),
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=tt,
                cost_usd=cost,
                latency_s=latency,
                reasoning=reasoning if isinstance(reasoning, str) else None,
            )
            if os.environ.get("MEDVERIF_API_LEDGER", "").lower() in ("1", "true", "yes"):
                _record_call({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "model": out.model or model,
                "provider": out.provider or prov,
                "request_id": out.request_id,
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "total_tokens": tt,
                "cost_usd": cost,
                "latency_s": round(latency, 3),
                })
            print(
                json.dumps({
                    "llm": out.model or model,
                    "provider": out.provider,
                    "request_id": out.request_id,
                    "tokens": tt,
                    "cost_usd": cost,
                }),
                flush=True,
            )
            return out
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code < 500 and exc.code not in (408, 429):
                break
            if attempt + 1 >= max_retries:
                break
            _retry_sleep(attempt, exc)
        except (
            urllib.error.URLError,
            TimeoutError,
            http.client.RemoteDisconnected,
            ConnectionError,
            ConnectionResetError,
        ) as exc:
            last_err = exc
            if attempt + 1 >= max_retries:
                break
            _retry_sleep(attempt, exc)
    raise RuntimeError(f"OpenRouter chat failed after {max_retries} tries: {last_err}")


def assert_no_thinking_leak(text: str) -> None:
    low = text.lower()
    think_open = "<" + "think>"
    think_close = "</" + "think>"
    if "redacted_thinking" in low or think_open in low or think_close in low:
        raise RuntimeError("thinking leak in model output (refusing to score)")


def map_concurrent(
    fn: Callable[[Any], Any],
    items: list[Any],
    *,
    max_workers: int = MAX_WORKERS,
) -> list[Any]:
    workers = min(max_workers, MAX_WORKERS, max(len(items), 1))
    if workers <= 1:
        return [fn(x) for x in items]
    out: list[Any] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fn, item): i for i, item in enumerate(items)}
        for fut in as_completed(futs):
            out[futs[fut]] = fut.result()
    return out
