#!/usr/bin/env python3
"""T15 step 2: fine-tune MiniCheck-RoBERTa-L on data/t15 train/dev."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

BASE_CKPT = "lytang/MiniCheck-RoBERTa-Large"
SEED = 42


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(phase: str, **fields) -> None:
    print(json.dumps({"ts": _ts(), "phase": phase, **fields}), flush=True)


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, default=ROOT / "data/t15/train.jsonl")
    parser.add_argument("--dev", type=Path, default=ROOT / "data/t15/dev.jsonl")
    parser.add_argument("--out-dir", type=Path, default=ROOT / ".cache/checkpoints/t15_roberta")
    parser.add_argument("--config-out", type=Path, default=ROOT / "notes/t15_config.json")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--tokenize-batch", type=int, default=256)
    args = parser.parse_args()

    import numpy as np
    import torch
    from datasets import Dataset
    from transformers import (
        AutoConfig,
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainerCallback,
        TrainingArguments,
    )

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    _log("load_data_start", train=str(args.train), dev=str(args.dev))
    train_rows = _read_jsonl(args.train)
    dev_rows = _read_jsonl(args.dev)
    _log("load_data_done", n_train=len(train_rows), n_dev=len(dev_rows))

    cache = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    _log("load_model_start", checkpoint=BASE_CKPT)
    tokenizer = AutoTokenizer.from_pretrained(BASE_CKPT, use_fast=True, cache_dir=cache)
    config = AutoConfig.from_pretrained(
        BASE_CKPT,
        num_labels=2,
        finetuning_task="text-classification",
        cache_dir=cache,
    )
    config.problem_type = "single_label_classification"
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_CKPT, config=config, cache_dir=cache
    )
    _log("load_model_done")

    eos = tokenizer.eos_token or "</s>"

    def rows_to_dataset(rows: list[dict]) -> Dataset:
        return Dataset.from_dict(
            {
                "evidence": [r["evidence"] for r in rows],
                "claim": [r["claim"] for r in rows],
                "labels": [1 if r["label"] == "SUPPORTED" else 0 for r in rows],
            }
        )

    def tokenize_batch(batch: dict) -> dict:
        texts = [
            eos.join([evidence, claim])
            for evidence, claim in zip(batch["evidence"], batch["claim"], strict=True)
        ]
        enc = tokenizer(
            texts,
            truncation=True,
            max_length=args.max_length,
            padding=False,
        )
        enc["labels"] = batch["labels"]
        return enc

    _log("tokenize_start", n_train=len(train_rows), n_dev=len(dev_rows))
    train_ds = rows_to_dataset(train_rows).map(
        tokenize_batch,
        batched=True,
        batch_size=args.tokenize_batch,
        remove_columns=["evidence", "claim"],
    )
    dev_ds = rows_to_dataset(dev_rows).map(
        tokenize_batch,
        batched=True,
        batch_size=args.tokenize_batch,
        remove_columns=["evidence", "claim"],
    )
    _log("tokenize_done", n_train=len(train_ds), n_dev=len(dev_ds))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    n_epochs = int(args.epochs) if args.epochs == int(args.epochs) else args.epochs

    class StageLogger(TrainerCallback):
        def on_epoch_begin(self, args, state, control, **kwargs):
            ep = int(state.epoch or 0) + 1
            _log("epoch_start", epoch=ep, total_epochs=n_epochs)

        def on_epoch_end(self, args, state, control, **kwargs):
            ep = int(state.epoch or 0)
            _log("epoch_end", epoch=ep, total_epochs=n_epochs)

        def on_evaluate(self, args, state, control, metrics=None, **kwargs):
            _log("eval_done", metrics=metrics or {})

    training_args = TrainingArguments(
        output_dir=str(args.out_dir),
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        seed=SEED,
        report_to=[],
        logging_steps=50,
        save_total_limit=int(n_epochs) + 1,
        fp16=torch.cuda.is_available(),
    )

    _log("train_start", epochs=args.epochs, batch_size=args.batch_size)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        tokenizer=tokenizer,
        callbacks=[StageLogger()],
    )
    trainer.train()
    best_dir = args.out_dir / "best"
    best_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    _log("train_done", best=str(best_dir))

    payload = {
        "base_checkpoint": BASE_CKPT,
        "best_checkpoint_dir": str(best_dir),
        "train_file": str(args.train.relative_to(ROOT)),
        "dev_file": str(args.dev.relative_to(ROOT)),
        "n_train": len(train_rows),
        "n_dev": len(dev_rows),
        "hyperparameters": {
            "seed": SEED,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "max_length": args.max_length,
            "threshold": 0.5,
            "input_format": "evidence + eos + claim (MiniCheck RoBERTa)",
        },
        "finished_at": _ts(),
    }
    args.config_out.parent.mkdir(parents=True, exist_ok=True)
    args.config_out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
