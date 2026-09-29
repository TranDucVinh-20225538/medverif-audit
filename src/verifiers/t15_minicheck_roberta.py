"""T15 fine-tuned MiniCheck-RoBERTa-L (claim/evidence same format as T6-A base)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from verifiers.preprocess import verifier_inputs

ROOT = Path(__file__).resolve().parents[2]
VERIFIER_ID = "t15_minicheck_roberta"


def _checkpoint_dir() -> Path:
    env = os.environ.get("MEDVERIF_T15_CKPT", "").strip()
    if env:
        return Path(env)
    cfg = ROOT / "notes/t15_config.json"
    if cfg.is_file():
        data = json.loads(cfg.read_text())
        return Path(data["best_checkpoint_dir"])
    raise RuntimeError("Set MEDVERIF_T15_CKPT or train T15 (notes/t15_config.json)")


def load():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    ckpt = _checkpoint_dir()
    cache = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(ckpt, cache_dir=cache)
    model = AutoModelForSequenceClassification.from_pretrained(ckpt, cache_dir=cache)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    meta = {"checkpoint": str(ckpt)}
    return (model, tokenizer, meta, device), time.perf_counter() - started


def score_batch(bundle, rows: list[dict], _verifier_id: str = VERIFIER_ID) -> list[dict]:
    import torch

    model, tokenizer, meta, device = bundle
    eos = tokenizer.eos_token or "</s>"
    texts = []
    for row in rows:
        claim, evidence = verifier_inputs(row)
        texts.append(eos.join([evidence, claim]))
    enc = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    started = time.perf_counter()
    with torch.no_grad():
        logits = model(**enc).logits
        probs = torch.softmax(logits, dim=-1)[:, 1].cpu().tolist()
    per = (time.perf_counter() - started) / max(len(rows), 1)
    out = []
    for row, prob in zip(rows, probs):
        label = 1 if prob > 0.5 else 0
        out.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": str(prob),
                "score": float(prob),
                "verdict": "PASS" if label == 1 else "FAIL",
                "latency_s": per,
                "verifier": VERIFIER_ID,
                "t15_checkpoint": meta.get("checkpoint"),
            }
        )
    return out
