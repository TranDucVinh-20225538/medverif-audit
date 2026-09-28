"""CPU AlignScore-large, evaluation_mode nli_sp. PASS iff score > 0.5."""

from __future__ import annotations

import os
import time

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

from alignscore.alignscore import AlignScore


def load(ckpt_path: str):
    started = time.perf_counter()
    model = AlignScore(
        model="roberta-large",
        batch_size=4,
        device="cpu",
        ckpt_path=ckpt_path,
        evaluation_mode="nli_sp",
        verbose=False,
    )
    return model, time.perf_counter() - started


def score_batch(model, rows: list[dict]) -> list[dict]:
    docs = [row["evidence"] for row in rows]
    claims = [row["claim"] for row in rows]
    started = time.perf_counter()
    scores = model.score(docs, claims)
    elapsed = time.perf_counter() - started
    per = elapsed / max(len(rows), 1)
    out = []
    for row, score in zip(rows, scores):
        value = float(score)
        out.append({
            "instance_id": row["instance_id"],
            "raw_output": str(value),
            "score": value,
            "verdict": "PASS" if value > 0.5 else "FAIL",
            "latency_s": per,
            "verifier": "v3_alignscore",
        })
    return out
