"""T6-A HHEM (Vectara hallucination evaluation model)."""

from __future__ import annotations

import time

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from verifiers.preprocess import verifier_inputs

MODEL_ID = "vectara/hallucination_evaluation_model"
VERIFIER_ID = "t6a_hhem"


def load():
    started = time.perf_counter()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(
        MODEL_ID, trust_remote_code=True, use_fast=False
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID, trust_remote_code=True
    ).to(device)
    model.eval()
    return (model, tok, device), time.perf_counter() - started


def score_batch(bundle, rows: list[dict]) -> list[dict]:
    model, tok, device = bundle
    out = []
    started = time.perf_counter()
    for row in rows:
        claim, evidence = verifier_inputs(row)
        text = f"{evidence} [SEP] {claim}"
        inputs = tok(text, return_tensors="pt", truncation=True, max_length=512).to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
            prob = torch.softmax(logits, dim=-1)[0, 1].item()
        out.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": str(prob),
                "score": float(prob),
                "verdict": "PASS" if prob > 0.5 else "FAIL",
                "latency_s": None,
                "verifier": VERIFIER_ID,
            }
        )
    per = (time.perf_counter() - started) / max(len(rows), 1)
    for row in out:
        row["latency_s"] = per
    return out
