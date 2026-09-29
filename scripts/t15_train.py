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
    args = parser.parse_args()

    import numpy as np
    import torch
    from datasets import Dataset
    from transformers import (
        AutoConfig,
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    train_rows = _read_jsonl(args.train)
    dev_rows = _read_jsonl(args.dev)

    cache = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
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

    def to_features(rows: list[dict]) -> Dataset:
        texts, labels = [], []
        eos = tokenizer.eos_token or "</s>"
        for row in rows:
            texts.append(eos.join([row["evidence"], row["claim"]]))
            labels.append(1 if row["label"] == "SUPPORTED" else 0)
        enc = tokenizer(
            texts,
            truncation=True,
            max_length=args.max_length,
            padding=False,
        )
        enc["labels"] = labels
        return Dataset.from_dict(enc)

    train_ds = to_features(train_rows)
    dev_ds = to_features(dev_rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(args.out_dir),
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        seed=SEED,
        report_to=[],
        logging_steps=50,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        tokenizer=tokenizer,
    )
    trainer.train()
    best_dir = args.out_dir / "best"
    best_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))

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
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    args.config_out.parent.mkdir(parents=True, exist_ok=True)
    args.config_out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
