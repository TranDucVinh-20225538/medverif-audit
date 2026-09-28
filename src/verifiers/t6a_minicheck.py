"""T6-A MiniCheck variants (roberta / deberta / granite via MiniCheck API)."""

from __future__ import annotations

import os
import time

from verifiers.preprocess import verifier_inputs

CACHE = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")

MODEL_BY_VERIFIER = {
    "t6a_minicheck_roberta": "roberta-large",
    "t6a_minicheck_deberta": "deberta-v3-large",
    "t6a_granite_guardian": "Granite-Guardian-3.3-8B",
}


def _use_cpu_patch(model_name: str) -> None:
    if model_name == "Granite-Guardian-3.3-8B":
        return
    import minicheck.inference as inference

    _from_pretrained = inference.AutoModelForSeq2SeqLM.from_pretrained

    def _cpu_pretrained(*args, **kwargs):
        kwargs.pop("device_map", None)
        return _from_pretrained(*args, **kwargs).to("cpu")

    inference.AutoModelForSeq2SeqLM.from_pretrained = _cpu_pretrained


def load(verifier_id: str):
    from minicheck.minicheck import MiniCheck

    model_name = MODEL_BY_VERIFIER[verifier_id]
    _use_cpu_patch(model_name)
    started = time.perf_counter()
    batch = 4 if model_name != "Granite-Guardian-3.3-8B" else 1
    model = MiniCheck(model_name=model_name, batch_size=batch, cache_dir=CACHE)
    return model, time.perf_counter() - started


def score_batch(model, rows: list[dict], verifier_id: str) -> list[dict]:
    docs, claims = [], []
    for row in rows:
        claim, evidence = verifier_inputs(row)
        claims.append(claim)
        docs.append(evidence)
    started = time.perf_counter()
    labels, probs, _c, _p = model.score(docs, claims)
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
                "verifier": verifier_id,
            }
        )
    return out
