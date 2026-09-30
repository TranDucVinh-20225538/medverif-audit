"""Bespoke-MiniCheck-7B (vLLM via MiniCheck); matches node30 t6_bespoke_minicheck metadata."""

from __future__ import annotations

import os
import time

from verifiers.preprocess import verifier_inputs

MODEL_ID = "bespokelabs/Bespoke-MiniCheck-7B"
MINICHECK_NAME = "Bespoke-MiniCheck-7B"
VERIFIER_ID = "v2b_bespoke"
VERSION = (
    "bespoke-minicheck-7b;minicheck@b58b9fa;bf16;P(Yes);thr>0.5;"
    "device_map=auto;max_memory_bf16_policy"
)
CACHE = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")


def load():
    from minicheck.minicheck import MiniCheck

    started = time.perf_counter()
    batch = int(os.environ.get("MEDVERIF_BESPOKE_BATCH", "4"))
    model = MiniCheck(
        model_name=MINICHECK_NAME,
        batch_size=batch,
        cache_dir=CACHE,
        tensor_parallel_size=1,
        max_tokens=1,
    )
    return model, time.perf_counter() - started


def score_batch(model, rows: list[dict]) -> list[dict]:
    docs, claims = [], []
    for row in rows:
        claim, evidence = verifier_inputs(row)
        claims.append(claim)
        docs.append(evidence)
    started = time.perf_counter()
    labels, probs, _chunks, _per = model.score(docs, claims)
    per = (time.perf_counter() - started) / max(len(rows), 1)
    out = []
    for row, label, prob in zip(rows, labels, probs):
        out.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": str(prob),
                "score": float(prob),
                "verdict": "PASS" if int(label) == 1 else "FAIL",
                "latency_s": per,
                "verifier": VERIFIER_ID,
                "model": MODEL_ID,
                "version": VERSION,
                "quantized": False,
                "precision": "bf16",
            }
        )
    return out
