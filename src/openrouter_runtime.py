"""HF tokenizer + OpenRouter generation shim (vLLM-shaped generate API)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from llm_client import LLMResponse, assert_no_thinking_leak, chat, map_concurrent


@dataclass
class _GenPiece:
    text: str
    finish_reason: str = "stop"


@dataclass
class _GenOut:
    outputs: list[_GenPiece]


class OpenRouterEngine:
    def __init__(
        self,
        *,
        model: str,
        tokenizer,
        max_tokens: int,
        provider: str | None = None,
        extra_body: dict[str, Any] | None = None,
        assert_no_thinking: bool = False,
        prompt_suffix: str = "",
        refuse_reasoning_only: bool = True,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
        self.provider = provider
        self.extra_body = extra_body or {}
        self.assert_no_thinking = assert_no_thinking
        self.prompt_suffix = prompt_suffix
        self.refuse_reasoning_only = refuse_reasoning_only
        self.last_meta: list[LLMResponse] = []

    def generate(self, prompts: list[str], params) -> list[_GenOut]:
        max_tokens = getattr(params, "max_tokens", None) or self.max_tokens
        temperature = getattr(params, "temperature", 0.0)
        seed = getattr(params, "seed", 42)
        workers = int(os.environ.get("MEDVERIF_OR_BATCH_WORKERS", "8"))

        def _one(prompt: str) -> tuple[LLMResponse, _GenOut]:
            user = prompt + (self.prompt_suffix or "")
            resp = chat(
                model=self.model,
                messages=[{"role": "user", "content": user}],
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
                provider=self.provider,
                allow_fallbacks=False,
                extra_body=self.extra_body or None,
                refuse_reasoning_only=self.refuse_reasoning_only,
            )
            text = resp.text
            if self.assert_no_thinking:
                assert_no_thinking_leak(text)
            return resp, _GenOut(outputs=[_GenPiece(text=text)])

        pairs = map_concurrent(_one, prompts, max_workers=workers)
        self.last_meta = [p[0] for p in pairs]
        return [p[1] for p in pairs]

    def get_tokenizer(self):
        return self.tokenizer


@dataclass
class _Params:
    temperature: float = 0.0
    max_tokens: int = 256
    seed: int = 42


class Llama3InstructTokenizer:
    """Llama 3.x instruct chat template (no HF download; matches OpenRouter Meta models)."""

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool = False,
        add_generation_prompt: bool = True,
        **_: Any,
    ) -> str:
        if tokenize:
            raise NotImplementedError("tokenize=True not supported for Llama3InstructTokenizer")
        h = "<|" + "start_header_id|>"
        eh = "<|" + "end_header_id|>"
        eot = "<|eot_id|>"
        out = "<|begin_of_text|>"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            out += f"{h}{role}{eh}\n\n{content}{eot}"
        if add_generation_prompt:
            out += f"{h}assistant{eh}\n\n"
        return out


def load_tokenizer(model: str, revision: str | None = None):
    use_llama_string = os.environ.get("MEDVERIF_V4_LLAMA_STRING_TEMPLATE", "1").lower() in (
        "1",
        "true",
        "yes",
    )
    if use_llama_string and "llama" in model.lower():
        return Llama3InstructTokenizer()
    from transformers import AutoTokenizer

    kwargs: dict[str, Any] = {"trust_remote_code": True}
    if revision:
        kwargs["revision"] = revision
    cache = (os.environ.get("HUGGINGFACE_HUB_CACHE") or "").strip()
    if not cache:
        hf_home = (os.environ.get("HF_HOME") or "").strip()
        if hf_home:
            cache = os.path.join(hf_home, "hub")
    if cache:
        kwargs["cache_dir"] = cache
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        kwargs["token"] = token
    try:
        return AutoTokenizer.from_pretrained(model, **kwargs)
    except OSError as exc:
        if "llama" in model.lower() and use_llama_string:
            return Llama3InstructTokenizer()
        raise exc


def load_openrouter_engine(
    *,
    openrouter_model: str,
    tokenizer_model: str,
    tokenizer_revision: str | None,
    max_tokens: int,
    provider: str | None = None,
    extra_body: dict[str, Any] | None = None,
    assert_no_thinking: bool = False,
    prompt_suffix: str = "",
    refuse_reasoning_only: bool = True,
) -> tuple[OpenRouterEngine, Any, _Params, float]:
    started = time.perf_counter()
    tok = load_tokenizer(tokenizer_model, tokenizer_revision)
    engine = OpenRouterEngine(
        model=openrouter_model,
        tokenizer=tok,
        max_tokens=max_tokens,
        provider=provider,
        extra_body=extra_body,
        assert_no_thinking=assert_no_thinking,
        prompt_suffix=prompt_suffix,
        refuse_reasoning_only=refuse_reasoning_only,
    )
    return engine, tok, _Params(max_tokens=max_tokens), time.perf_counter() - started
