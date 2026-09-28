"""Score a JSONL with one verifier. Resume by instance_id."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from verifiers.io_utils import append_jsonl, done_ids, read_jsonl


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
    llm, tokenizer, params, load_s = module.load()
    scored = module.score_batch(llm, tokenizer, params, todo)
    append_jsonl(args.out, scored)
    fails = sum(row["verdict"] == "PARSE_FAIL" for row in scored)
    print(json.dumps({
        "verifier": args.verifier,
        "load_s": load_s,
        "scored": len(scored),
        "parse_fail": fails,
        "out": str(args.out),
    }))


if __name__ == "__main__":
    main()
