"""T15 fine-tuned MiniCheck-RoBERTa-L via MiniCheck library (same path as T6-A base)."""

from __future__ import annotations

from verifiers import minicheck_roberta_lib as mcl

VERIFIER_ID = "t15_minicheck_roberta"
VERSION = f"minicheck@{mcl.MINICHECK_COMMIT};roberta-large;T15-ft;thr>0.5"


def load():
    model, meta, latency = mcl.load(fine_tuned=True, force_cpu=False)
    return (model, meta), latency


def score_batch(bundle, rows: list[dict], _verifier_id: str = VERIFIER_ID) -> list[dict]:
    model, meta = bundle
    return mcl.score_batch(model, rows, VERIFIER_ID, meta=meta)
