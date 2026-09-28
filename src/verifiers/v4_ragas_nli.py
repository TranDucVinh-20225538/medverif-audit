"""RAGAS-NLI only. Qwen3-14B, thinking off, greedy. Statement split is not run."""

from __future__ import annotations

import json
import os
import time

from verifiers.ragas_nli_prompt import nli_prompt

MODEL = "Qwen/Qwen3-14B"
REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"


def load():
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
        download_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    )
    tokenizer = llm.get_tokenizer()
    params = SamplingParams(temperature=0.0, max_tokens=512, seed=42)
    return llm, tokenizer, params, time.perf_counter() - started


def render(tokenizer, evidence: str, claim: str) -> str:
    user = nli_prompt(evidence, [claim])
    try:
        return tokenizer.apply_chat_template(
            [{"role": "user", "content": user}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError as exc:
        raise RuntimeError(
            "Qwen3 chat template did not accept enable_thinking=False. "
            "Refusing to run with thinking left on."
        ) from exc


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
    for row, out in zip(pairs, outputs):
        raw = out.outputs[0].text if out.outputs else ""
        verdict, score = parse_verdict(raw)
        rows.append({
            "instance_id": row["instance_id"],
            "raw_output": raw,
            "score": score,
            "verdict": verdict,
            "latency_s": per,
            "verifier": "v4_ragas_nli",
        })
    return rows
