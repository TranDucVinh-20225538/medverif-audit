"""CPU MiniCheck-Flan-T5-Large. Official score rule: pred_label 1 iff prob > 0.5."""

from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import minicheck.inference as inference

_from_pretrained = inference.AutoModelForSeq2SeqLM.from_pretrained


def _cpu_pretrained(*args, **kwargs):
    kwargs.pop("device_map", None)
    return _from_pretrained(*args, **kwargs).to("cpu")


inference.AutoModelForSeq2SeqLM.from_pretrained = _cpu_pretrained

from minicheck.minicheck import MiniCheck

CACHE = os.environ.get("HF_HOME")


def load():
    started = __import__("time").perf_counter()
    model = MiniCheck(model_name="flan-t5-large", batch_size=4, cache_dir=CACHE)
    return model, __import__("time").perf_counter() - started


def score_batch(model, rows: list[dict]) -> list[dict]:
    import time

    docs = [row["evidence"] for row in rows]
    claims = [row["claim"] for row in rows]
    started = time.perf_counter()
    labels, probs, _chunks, _per = model.score(docs, claims)
    elapsed = time.perf_counter() - started
    per = elapsed / max(len(rows), 1)
    out = []
    for row, label, prob in zip(rows, labels, probs):
        out.append({
            "instance_id": row["instance_id"],
            "raw_output": str(prob),
            "score": float(prob),
            "verdict": "PASS" if int(label) == 1 else "FAIL",
            "latency_s": per,
            "verifier": "v2a_minicheck",
        })
    return out
