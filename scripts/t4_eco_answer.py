#!/usr/bin/env python3
"""T4 ecological: patient-style Q&A given evidence (OpenRouter, temp 0)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openrouter_client import chat_completion  # noqa: E402

MODELS_PATH = ROOT / "notes" / "t4_models.json"
TASKS = ROOT / "data" / "t4" / "eco_tasks.jsonl"
OUT = ROOT / "data" / "t4" / "eco_answers.jsonl"


def patient_question(base: dict) -> str:
    drug = (base.get("target_sentence") or base.get("claim") or "").split(",")[0][:120]
    return (
        "You are helping a patient understand their prescription. "
        "Using ONLY the medical excerpt below, answer in 1–3 plain sentences: "
        "what dose and how should they take the medication?\n\n"
        f"Excerpt:\n{base['evidence']}"
    )


def load_tasks() -> list[dict]:
    if not TASKS.is_file():
        raise SystemExit(f"missing {TASKS}; run t4_build_eco_tasks.py first")
    return [json.loads(line) for line in TASKS.open() if line.strip()]


def spend_so_far() -> float:
    total = 0.0
    if OUT.is_file():
        for line in OUT.open():
            if line.strip():
                total += float(json.loads(line).get("api_cost_usd") or 0)
    return total


def main() -> None:
    budget = float(os.environ.get("MEDVERIF_T4_BUDGET_USD", "5"))
    models = json.loads(MODELS_PATH.read_text())["answerers"]
    done = set()
    if OUT.is_file():
        for line in OUT.open():
            if line.strip():
                row = json.loads(line)
                done.add((row["task_id"], row["answerer_id"]))
    tasks = load_tasks()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a") as handle:
        for task in tasks:
            for ans in models:
                key = (task["task_id"], ans["id"])
                if key in done:
                    continue
                if spend_so_far() >= budget:
                    print(json.dumps({"stop": "budget", "spent": spend_so_far()}))
                    return
                messages = [
                    {"role": "system", "content": "Answer using only the provided excerpt. Be concise."},
                    {"role": "user", "content": task["prompt"]},
                ]
                text, meta = chat_completion(
                    model=ans["openrouter_model"],
                    messages=messages,
                    temperature=0.0,
                    max_tokens=200,
                    provider_order=[ans.get("provider")] if ans.get("provider") else None,
                )
                cost = float((meta.raw.get("usage") or {}).get("cost") or 0)
                row = {
                    **task,
                    "answerer_id": ans["id"],
                    "openrouter_model": ans["openrouter_model"],
                    "provider": meta.provider or ans.get("provider"),
                    "answer": text.strip(),
                    "api_cost_usd": cost,
                    "request_id": meta.id,
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                print(json.dumps({"task": task["task_id"], "answerer": ans["id"], "cost": cost}), flush=True)


if __name__ == "__main__":
    main()
