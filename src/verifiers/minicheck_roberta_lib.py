"""MiniCheck library path for RoBERTa-L (paper checkpoint + optional T15 ft weights)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from verifiers.preprocess import verifier_inputs

MODEL_NAME = "roberta-large"
DEFAULT_BASE_CKPT = "lytang/MiniCheck-RoBERTa-Large"
MINICHECK_COMMIT = "b58b9fa69acbd1015ec970fa65dd752413a053d2"
CACHE = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
ROOT = Path(__file__).resolve().parents[2]

# LLM-AggreFact leaderboard / MiniCheck-RoBERTa-L (full test, library eval).
PUBLISHED_AGGREFACT_BACC = 0.730


def _use_cpu_patch() -> None:
    import minicheck.inference as inference

    def _patch(cls):
        if getattr(cls, "_medverif_cpu_patched", False):
            return
        orig = cls.from_pretrained.__func__

        @classmethod
        def from_pretrained(cls_inner, *args, **kwargs):
            kwargs.pop("device_map", None)
            return orig(cls_inner, *args, **kwargs).to("cpu")

        cls.from_pretrained = from_pretrained
        cls._medverif_cpu_patched = True

    _patch(inference.AutoModelForSeq2SeqLM)
    _patch(inference.AutoModelForSequenceClassification)


def _patch_roberta_ckpt(ckpt: str) -> None:
    """Load weights from local/HF path instead of default lytang hub id."""
    import minicheck.inference as inference

    if getattr(inference.Inferencer, "_medverif_ckpt_patched", False):
        return
    orig_init = inference.Inferencer.__init__

    def __init__(self, model_name, max_model_len, batch_size, cache_dir):
        if model_name != "roberta-large":
            return orig_init(self, model_name, max_model_len, batch_size, cache_dir)
        self.model_name = model_name
        if cache_dir is not None and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.max_model_len = 512 if max_model_len is None else max_model_len
        config = inference.AutoConfig.from_pretrained(
            ckpt,
            num_labels=2,
            finetuning_task="text-classification",
            revision="main",
            token=None,
            cache_dir=cache_dir,
        )
        config.problem_type = "single_label_classification"
        self.tokenizer = inference.AutoTokenizer.from_pretrained(
            ckpt, use_fast=True, revision="main", token=None, cache_dir=cache_dir
        )
        self.model = inference.AutoModelForSequenceClassification.from_pretrained(
            ckpt,
            config=config,
            revision="main",
            token=None,
            ignore_mismatched_sizes=False,
            cache_dir=cache_dir,
            device_map="auto",
        )
        self.model.eval()
        self.batch_size = batch_size
        import torch.nn as nn

        self.softmax = nn.Softmax(dim=-1)

    inference.Inferencer.__init__ = __init__
    inference.Inferencer._medverif_ckpt_patched = True


def _t15_checkpoint_dir() -> Path | None:
    env = os.environ.get("MEDVERIF_T15_CKPT", "").strip()
    if env:
        return Path(env)
    cfg = ROOT / "notes/t15_config.json"
    if cfg.is_file():
        return Path(json.loads(cfg.read_text())["best_checkpoint_dir"])
    return None


def load(*, fine_tuned: bool = False, force_cpu: bool = False):
    """
    Returns (MiniCheck instance, load_meta dict).
    fine_tuned=True swaps Inferencer weights to T15 best checkpoint (same chunking/score path).
    """
    os.environ.setdefault("TQDM_DISABLE", "1")
    if force_cpu:
        _use_cpu_patch()
    ckpt = None
    if fine_tuned:
        ckpt = str(_t15_checkpoint_dir())
        _patch_roberta_ckpt(ckpt)
    from minicheck.minicheck import MiniCheck

    batch = int(os.environ.get("MEDVERIF_MINICHECK_BATCH", os.environ.get("MEDVERIF_T15_BATCH", "16")))
    started = time.perf_counter()
    model = MiniCheck(model_name=MODEL_NAME, batch_size=batch, cache_dir=CACHE)
    meta = {
        "minicheck_commit": MINICHECK_COMMIT,
        "model_name": MODEL_NAME,
        "base_checkpoint": DEFAULT_BASE_CKPT,
        "weights": ckpt or DEFAULT_BASE_CKPT,
        "fine_tuned": fine_tuned,
        "device": "cpu" if force_cpu else "cuda/auto",
        "batch_size": batch,
    }
    return model, meta, time.perf_counter() - started


def score_batch(model, rows: list[dict], verifier_id: str, *, meta: dict | None = None) -> list[dict]:
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
                "minicheck_weights": (meta or {}).get("weights"),
            }
        )
    return out
