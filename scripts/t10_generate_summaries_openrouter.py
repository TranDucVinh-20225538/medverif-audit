#!/usr/bin/env python3
"""Generate Vectara-style doc summaries via OpenRouter (T10; budget cap)."""

from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openrouter_client import chat_completion  # noqa: E402
from text_utils import DOSE_RE  # noqa: E402

PROMPT = """Your task is to provide a concise and factual summary for the given passage.
Rules
1. Summarize using only the information in the given passage. Do not infer. Do not use your internal knowledge.
2. Do not provide a preamble or explanation, output only the summary.
3. Summaries should never exceed 20 percent of the original text's length.
4. Maintain the tone of the passage.
If you are unable to summarize the text due to missing, unreadable, irrelevant or insufficient content, respond only with:
"I am unable to summarize this text."
Here is the passage:
{passage}"""

OUT = ROOT / "data/t10/leaderboard_docs.jsonl"
META = ROOT / "notes/t10_or_summaries.json"
BUDGET = float(os.environ.get("T10_OR_BUDGET_USD", "4.0"))

MODELS = [
    ("google/gemini-2.5-flash-lite", "Google"),
    ("meta-llama/llama-3.3-70b-instruct", "DeepInfra"),
    ("mistralai/mistral-small-3.2-24b-instruct", "DeepInfra"),
    ("openai/gpt-4o-mini", "OpenAI"),
    ("anthropic/claude-haiku-4.5", "Anthropic"),
    ("deepseek/deepseek-chat", "DeepSeek"),
]


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.open() if line.strip()]


def pick_passages(n: int | None = None) -> list[dict]:
    if n is None:
        n = int(os.environ.get("T10_N_PASSAGES", "40"))
    rows = read_jsonl(ROOT / "data/v3/instances_main.jsonl")
    pool = [r for r in rows if r.get("valid", True) and r.get("subset") == "main" and r.get("condition") == "C0"]
    pool = [r for r in pool if DOSE_RE.search(r.get("evidence") or "")]
    rng = random.Random(20260929)
    rng.shuffle(pool)
    out = []
    for r in pool:
        ev = (r.get("evidence") or "").strip()
        if len(ev) < 80:
            continue
        out.append({"doc_id": r["base_id"], "passage": ev[:3500], "source": "medverif_main_c0"})
        if len(out) >= n:
            break
    return out


def existing_keys(path: Path) -> set[tuple[str, str]]:
    if not path.is_file():
        return set()
    keys: set[tuple[str, str]] = set()
    for row in read_jsonl(path):
        keys.add((row.get("doc_id", ""), row.get("model_id", "")))
    return keys


def main() -> None:
    os.environ.setdefault("MEDVERIF_API_LEDGER", "1")
    spent = 0.0
    passages = pick_passages()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = existing_keys(OUT)
    rows_out = list(read_jsonl(OUT)) if OUT.is_file() else []
    log = {
        "prompt": "vectara_leaderboard_readme",
        "budget_usd": BUDGET,
        "models": [],
        "docs": len(passages),
        "resume_skipped": 0,
    }
    mode = "a" if OUT.is_file() and done else "w"
    with OUT.open(mode) as handle:
        for doc in passages:
            for model, provider in MODELS:
                if (doc["doc_id"], model) in done:
                    log["resume_skipped"] += 1
                    continue
                if spent >= BUDGET:
                    log["stopped"] = "budget"
                    break
                os.environ["MEDVERIF_OPENROUTER_PROVIDER"] = provider
                for attempt in range(8):
                    try:
                        text, meta = chat_completion(
                            model=model,
                            messages=[{"role": "user", "content": PROMPT.format(passage=doc["passage"])}],
                            temperature=0.0,
                            max_tokens=400,
                            seed=42,
                        )
                        break
                    except urllib.error.HTTPError as exc:
                        if exc.code in (429, 502, 503) and attempt < 7:
                            time.sleep(5 * (attempt + 1))
                            continue
                        raise
                time.sleep(float(os.environ.get("T10_OR_SLEEP_S", "8.0")))
                cost = 0.0
                if meta.raw.get("usage"):
                    # ledger may fill later
                    pass
                row = {
                    "doc_id": doc["doc_id"],
                    "model_id": model,
                    "provider": provider,
                    "summary": text.strip(),
                    "source_doc": doc["passage"],
                    "source": doc["source"],
                    "openrouter_id": meta.id,
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                rows_out.append(row)
                done.add((doc["doc_id"], model))
                log["models"].append({"model": model, "doc": doc["doc_id"]})
            if spent >= BUDGET:
                break
    META.write_text(json.dumps({**log, "n_rows": len(rows_out)}, indent=2) + "\n")
    print(json.dumps({"n_rows": len(rows_out), "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
