"""Wrap MedScore's provided-evidence verifier. Prompt and parser are not edited."""

from __future__ import annotations

import os
import time

from v1_parser import released_parse_verification_output, released_verdict

MODEL = "mistralai/Mistral-Small-24B-Instruct-2501"
REVISION = "9527884be6e5616bdd54de542f9ae13384489724"


def format_input(evidence: str, claim: str) -> str:
    # medscore/verifier.py ProvidedEvidenceVerifier.format_input, commit 207c2b7.
    return f"Answer the question based on the given context.\n\n{evidence}\n\nInput: {claim} True or False?\nOutput:"


def load():
    from vllm import LLM, SamplingParams

    started = time.perf_counter()
    llm = LLM(
        model=MODEL,
        revision=REVISION,
        dtype="bfloat16",
        seed=42,
        trust_remote_code=True,
        max_model_len=4096,
        gpu_memory_utilization=0.90,
        enforce_eager=True,
        download_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    )
    tokenizer = llm.get_tokenizer()
    params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=256, seed=42)
    load_s = time.perf_counter() - started
    return llm, tokenizer, params, load_s


def render(tokenizer, evidence: str, claim: str) -> str:
    user = format_input(evidence, claim)
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )


def score_batch(llm, tokenizer, params, pairs: list[dict]) -> list[dict]:
    prompts = [render(tokenizer, row["evidence"], row["claim"]) for row in pairs]
    started = time.perf_counter()
    outputs = llm.generate(prompts, params)
    elapsed = time.perf_counter() - started
    per = elapsed / max(len(pairs), 1)
    rows = []
    for row, out in zip(pairs, outputs):
        raw = out.outputs[0].text if out.outputs else ""
        released = released_parse_verification_output(raw)
        rows.append({
            "instance_id": row["instance_id"],
            "raw_output": raw,
            "released_parser_score": released,
            "verdict": released_verdict(raw),
            "latency_s": per,
            "verifier": "v1_medscore",
        })
    return rows
