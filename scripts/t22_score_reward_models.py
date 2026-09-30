#!/usr/bin/env python3
"""T22: RewardBench-style open RLHF reward models on frozen main (GPU, sequential)."""

from __future__ import annotations

import gc
import json
import os
import sys
import time
from pathlib import Path

import torch
from huggingface_hub import model_info
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lane_b_env import append_stamped  # noqa: E402
from verifiers.io_utils import done_ids, read_jsonl  # noqa: E402
from verifiers.preprocess import verifier_inputs  # noqa: E402

INST = ROOT / "data/v3/instances_main.jsonl"
OUT_DIR = ROOT / "results/raw/t22"
MANIFEST = ROOT / "notes/t22_reward_models.json"

# RewardBench v1 open seq-classifier RMs (no Qwen/Gemini); fit one 48G GPU one-at-a-time.
MODELS = (
    {"model_id": "internlm/internlm2-7b-reward", "slug": "internlm2_7b_reward", "kind": "internlm"},
    {"model_id": "sfairXC/FsfairX-LLaMA3-RM-v0.1", "slug": "fsfairx_llama3_rm_v01", "kind": "llama3_rm"},
    {"model_id": "internlm/internlm2-1_8b-reward", "slug": "internlm2_1_8b_reward", "kind": "internlm"},
)


def hf_revision(model_id: str) -> str:
    try:
        return model_info(model_id).sha or ""
    except Exception as exc:  # noqa: BLE001
        return f"error:{exc}"[:120]


def score_internlm(model, tokenizer, evidence: str, claim: str, device: str) -> float:
    dialog = [{"role": "user", "content": evidence}, {"role": "assistant", "content": claim}]
    if hasattr(model, "get_scores"):
        scores = model.get_scores(tokenizer, [dialog])
        return float(scores[0])
    inputs = tokenizer.apply_chat_template(dialog, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model(inputs)
        if hasattr(out, "logits"):
            return float(out.logits[0].item())
        return float(out[0].item())


def score_llama3_rm(model, tokenizer, evidence: str, claim: str, device: str) -> float:
    messages = [{"role": "user", "content": evidence}, {"role": "assistant", "content": claim}]
    if hasattr(tokenizer, "apply_chat_template"):
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048).to(device)
    else:
        inputs = tokenizer(evidence, claim, return_tensors="pt", truncation=True, max_length=2048).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits
    return float(logits[0, 0].item())


def load_bundle(spec: dict, device: str):
    mid = spec["model_id"]
    tok = AutoTokenizer.from_pretrained(mid, trust_remote_code=True)
    if spec["kind"] == "internlm":
        model = AutoModel.from_pretrained(mid, trust_remote_code=True, torch_dtype=torch.float16).to(device)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            mid, trust_remote_code=True, torch_dtype=torch.float16, num_labels=1
        ).to(device)
    model.eval()
    return model, tok


def score_row(spec: dict, model, tokenizer, device: str, row: dict) -> dict:
    claim, evidence = verifier_inputs(row)
    if spec["kind"] == "internlm":
        score = score_internlm(model, tokenizer, evidence, claim, device)
    else:
        score = score_llama3_rm(model, tokenizer, evidence, claim, device)
    return {
        "instance_id": row["instance_id"],
        "raw_output": str(score),
        "score": score,
        "verdict": "PASS" if score > 0.0 else "FAIL",
        "latency_s": None,
        "verifier": f"t22_{spec['slug']}",
        "reward_model": spec["model_id"],
    }


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows = [r for r in read_jsonl(INST) if r.get("valid", True)]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"models": [], "instances": len(rows), "device": device}
    for spec in MODELS:
        rev = hf_revision(spec["model_id"])
        manifest["models"].append(
            {
                "model_id": spec["model_id"],
                "slug": spec["slug"],
                "revision": rev,
                "rewardbench_v1_note": "open seq-classifier; excludes Qwen/Gemini",
            }
        )
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    for spec in MODELS:
        out_path = OUT_DIR / f"t22_{spec['slug']}.jsonl"
        finished = done_ids(out_path)
        todo = [r for r in rows if r["instance_id"] not in finished]
        print(json.dumps({"t22": "load", "model": spec["model_id"], "todo": len(todo)}), flush=True)
        model, tokenizer = load_bundle(spec, device)
        t0 = time.perf_counter()
        batch: list[dict] = []
        for row in todo:
            batch.append(score_row(spec, model, tokenizer, device, row))
            if len(batch) >= 8:
                append_stamped(out_path, batch)
                batch = []
        if batch:
            append_stamped(out_path, batch)
        print(
            json.dumps(
                {
                    "t22": "done",
                    "model": spec["model_id"],
                    "n": len(done_ids(out_path)),
                    "elapsed_s": round(time.perf_counter() - t0, 1),
                }
            ),
            flush=True,
        )
        del model, tokenizer
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
