"""T6-A Granite Guardian 3.0-2b groundedness (HF transformers, CPU; node30 prompt/rule)."""

from __future__ import annotations

import json
import math
import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from verifiers.preprocess import verifier_inputs

MODEL_ID = "ibm-granite/granite-guardian-3.0-2b"
VERIFIER_ID = "t6a_granite_guardian"
VERSION = (
    "granite-guardian-3.0-2b;groundedness;bf16;score=1-P(Yes);PASS=label No"
)
SAFE_TOKEN = "No"
RISKY_TOKEN = "Yes"


def _yes_no_ids(tokenizer) -> tuple[int, int]:
    yes_id = tokenizer.encode(RISKY_TOKEN, add_special_tokens=False)[0]
    no_id = tokenizer.encode(SAFE_TOKEN, add_special_tokens=False)[0]
    return yes_id, no_id


def _prob_of_risk_from_logits(logits: torch.Tensor, yes_id: int, no_id: int) -> float:
    safe_prob = math.exp(float(logits[no_id]))
    risky_prob = math.exp(float(logits[yes_id]))
    probs = torch.softmax(
        torch.tensor([math.log(safe_prob + 1e-50), math.log(risky_prob + 1e-50)]),
        dim=0,
    )
    return float(probs[1].item())


def load():
    from hf_token_env import sanitize_hf_token_env

    sanitize_hf_token_env()
    cache = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    started = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, cache_dir=cache)
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        torch_dtype=dtype,
        cache_dir=cache,
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()
    return (model, tok, device), time.perf_counter() - started


def _score_one(model, tok, device, claim: str, evidence: str) -> dict:
    messages = [
        {"role": "context", "content": evidence},
        {"role": "assistant", "content": claim},
    ]
    guardian_config = {"risk_name": "groundedness"}
    chat = tok.apply_chat_template(
        messages,
        guardian_config=guardian_config,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tok(chat, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=1,
            do_sample=False,
            output_scores=True,
            return_dict_in_generate=True,
        )
    logits = out.scores[0][0].float().cpu()
    yes_id, no_id = _yes_no_ids(tok)
    prob_of_risk = _prob_of_risk_from_logits(logits, yes_id, no_id)
    gen_text = tok.decode(out.sequences[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    label = gen_text.strip().split()[0] if gen_text.strip() else ""
    if label.lower() == RISKY_TOKEN.lower():
        label = RISKY_TOKEN
    elif label.lower() == SAFE_TOKEN.lower():
        label = SAFE_TOKEN
    else:
        label = RISKY_TOKEN if prob_of_risk >= 0.5 else SAFE_TOKEN
    support = 1.0 - prob_of_risk
    payload = {
        "label": label,
        "prob_of_risk": prob_of_risk,
        "support": support,
    }
    return {
        "raw_output": json.dumps(payload),
        "score": support,
        "verdict": "PASS" if label == SAFE_TOKEN else "FAIL",
        "model": MODEL_ID,
        "version": VERSION,
    }


def score_batch(bundle, rows: list[dict]) -> list[dict]:
    model, tok, device = bundle
    out = []
    started = time.perf_counter()
    for row in rows:
        claim, evidence = verifier_inputs(row)
        scored = _score_one(model, tok, device, claim, evidence)
        out.append(
            {
                "instance_id": row["instance_id"],
                **scored,
                "latency_s": None,
                "verifier": VERIFIER_ID,
            }
        )
    per = (time.perf_counter() - started) / max(len(rows), 1)
    for row in out:
        row["latency_s"] = per
    return out
