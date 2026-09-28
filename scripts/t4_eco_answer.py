#!/usr/bin/env python3
"""T4 ecological: patient-style Q&A given evidence (OpenRouter, temp 0)."""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from llm_client import chat, map_concurrent  # noqa: E402

MODELS_PATH = ROOT / "notes" / "t4_models.json"
TASKS = ROOT / "data" / "t4" / "eco_tasks.jsonl"
OUT = ROOT / "data" / "t4" / "eco_answers.jsonl"

_write_lock = threading.Lock()


def load_tasks() -> list[dict]:
    if not TASKS.is_file():
        raise SystemExit(f"missing {TASKS}; run t4_build_eco_tasks.py first")
    return [json.loads(line) for line in TASKS.open() if line.strip()]


def load_done() -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    if OUT.is_file():
        for line in OUT.open():
            if line.strip():
                row = json.loads(line)
                done.add((row["task_id"], row["answerer_id"]))
    return done


def spend_so_far() -> float:
    total = 0.0
    if OUT.is_file():
        for line in OUT.open():
            if line.strip():
                total += float(json.loads(line).get("api_cost_usd") or 0)
    return total


def _one(job: tuple[dict, dict]) -> dict | None:
    task, ans = job
    budget = float(os.environ.get("MEDVERIF_T4_BUDGET_USD", "5"))
    with _write_lock:
        if spend_so_far() >= budget:
            return None
    messages = [
        {"role": "system", "content": "Answer using only the provided excerpt. Be concise."},
        {"role": "user", "content": task["prompt"]},
    ]
    prov = (ans.get("provider") or "").strip() or None
    resp = chat(
        model=ans["openrouter_model"],
        messages=messages,
        temperature=0.0,
        max_tokens=200,
        provider=prov,
        allow_fallbacks=False,
    )
    cost = float(resp.cost_usd or 0)
    row = {
        **task,
        "answerer_id": ans["id"],
        "openrouter_model": ans["openrouter_model"],
        "provider": resp.provider or prov,
        "answer": resp.text.strip(),
        "api_cost_usd": cost,
        "request_id": resp.request_id,
    }
    with _write_lock:
        if spend_so_far() >= budget:
            return None
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("a") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(
        json.dumps({"task": task["task_id"], "answerer": ans["id"], "cost": cost}),
        flush=True,
    )
    return row


def main() -> None:
    models = json.loads(MODELS_PATH.read_text())["answerers"]
    done = load_done()
    tasks = load_tasks()
    pending: list[tuple[dict, dict]] = []
    for task in tasks:
        for ans in models:
            key = (task["task_id"], ans["id"])
            if key not in done:
                pending.append((task, ans))
    if not pending:
        print(json.dumps({"status": "complete", "n_done": len(done)}))
        return
    workers = int(os.environ.get("MEDVERIF_OR_MAX_INFLIGHT", "3"))
    workers = max(1, min(workers, 8))
    map_concurrent(_one, pending, max_workers=workers)
    still = len(load_done())
    expected = len(tasks) * len(models)
    print(json.dumps({"status": "pass", "answers": still, "expected": expected}))


if __name__ == "__main__":
    main()
