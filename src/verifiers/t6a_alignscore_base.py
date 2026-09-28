"""T6-A AlignScore-base (roberta-base backbone)."""

from __future__ import annotations

import os
import time

from huggingface_hub import hf_hub_download

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

from alignscore.alignscore import AlignScore


def load():
    cache = os.environ.get("HUGGINGFACE_HUB_CACHE")
    ckpt = hf_hub_download(
        repo_id="yzha/AlignScore",
        filename="AlignScore-base.ckpt",
        revision="8509e78d25bb914939fc585c626500c9b2944249",
        cache_dir=cache,
    )
    started = time.perf_counter()
    model = AlignScore(
        model="roberta-base",
        batch_size=4,
        device="cpu",
        ckpt_path=ckpt,
        evaluation_mode="nli_sp",
        verbose=False,
    )
    return model, time.perf_counter() - started


def score_batch(model, rows: list[dict]) -> list[dict]:
    docs = [row["evidence"] for row in rows]
    claims = [row["claim"] for row in rows]
    started = time.perf_counter()
    scores = model.score(docs, claims)
    per = (time.perf_counter() - started) / max(len(rows), 1)
    out = []
    for row, score in zip(rows, scores):
        value = float(score)
        out.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": str(value),
                "score": value,
                "verdict": "PASS" if value > 0.5 else "FAIL",
                "latency_s": per,
                "verifier": "t6a_alignscore_base",
            }
        )
    return out
