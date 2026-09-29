"""T6-A HHEM 2.1 (Vectara; flan-t5 tokenizer — matches node30 raw)."""

from __future__ import annotations

import os
import time

import torch
from transformers import AutoModelForSequenceClassification

from verifiers.preprocess import verifier_inputs

MODEL_ID = "vectara/hallucination_evaluation_model"
TOKENIZER_ID = "google/flan-t5-base"
VERIFIER_ID = "t6a_hhem"
VERSION = "hhem-2.1-open;predict(premise,hypothesis);thr>0.5"


def _patch_hhem_class() -> None:
    from transformers.dynamic_module_utils import get_class_from_dynamic_module

    cls = get_class_from_dynamic_module(
        "modeling_hhem_v2.HHEMv2ForSequenceClassification", MODEL_ID
    )
    if not hasattr(cls, "all_tied_weights_keys"):
        cls.all_tied_weights_keys = property(lambda self: {})


def load():
    started = time.perf_counter()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    _patch_hhem_class()
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        cache_dir=cache,
    ).to(device)
    model.eval()
    return (model, None, device), time.perf_counter() - started


def score_batch(bundle, rows: list[dict]) -> list[dict]:
    model, _tok, device = bundle
    out = []
    started = time.perf_counter()
    pairs = []
    for row in rows:
        claim, evidence = verifier_inputs(row)
        pairs.append((evidence, claim))
    scores = model.predict(pairs)
    for row, prob_t in zip(rows, scores):
        prob = float(prob_t.item() if hasattr(prob_t, "item") else prob_t)
        out.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": str(prob),
                "score": prob,
                "verdict": "PASS" if prob > 0.5 else "FAIL",
                "latency_s": None,
                "verifier": VERIFIER_ID,
                "model": MODEL_ID,
                "version": VERSION,
            }
        )
    per = (time.perf_counter() - started) / max(len(rows), 1)
    for row in out:
        row["latency_s"] = per
    return out
