"""Score a JSONL with one verifier. Resume by instance_id."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

import os

import vllm_graceful
from verifiers.io_utils import append_jsonl, done_ids, read_jsonl

USE_OR = os.environ.get("MEDVERIF_USE_OPENROUTER", "").lower() in ("1", "true", "yes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", required=True)
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    module = importlib.import_module(f"verifiers.{args.verifier}")
    rows = read_jsonl(args.instances)
    finished = done_ids(args.out)
    todo = [row for row in rows if row.get("valid", True) and row["instance_id"] not in finished]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print(json.dumps({"verifier": args.verifier, "skipped": "complete", "n": len(rows)}))
        return
    batch = int(os.environ.get("MEDVERIF_SCORE_BATCH", "8"))
    llm, tokenizer, params, load_s = module.load()
    if not USE_OR:
        vllm_graceful.register(llm)
    scored_all: list[dict] = []
    try:
        for offset in range(0, len(todo), batch):
            chunk = todo[offset : offset + batch]
            scored = module.score_batch(llm, tokenizer, params, chunk)
            append_jsonl(args.out, scored)
            scored_all.extend(scored)
            print(json.dumps({
                "verifier": args.verifier,
                "progress": len(scored_all),
                "total_todo": len(todo),
            }), flush=True)
    finally:
        if not USE_OR:
            vllm_graceful.shutdown_all()
    fails = sum(row["verdict"] == "PARSE_FAIL" for row in scored_all)
    print(json.dumps({
        "verifier": args.verifier,
        "load_s": load_s,
        "scored": len(scored_all),
        "parse_fail": fails,
        "out": str(args.out),
    }))


if __name__ == "__main__":
    main()
