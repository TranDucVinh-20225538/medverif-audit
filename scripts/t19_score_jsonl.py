#!/usr/bin/env python3
"""Score JSONL with t19_ragas_local (resume + flock via scoring_lock)."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
    from scoring_lock import exclusive_score_lock
    from verifiers.io_utils import append_jsonl, done_ids, read_jsonl

    module = importlib.import_module("verifiers.t19_ragas_local")
    out_path = args.out if args.out.is_absolute() else (ROOT / args.out)
    slug = os.environ.get("MEDVERIF_T19_SLUG", "t19_ragas_local")
    with exclusive_score_lock(slug, out_path) as acquired:
        if not acquired:
            print(json.dumps({"skipped": "already_running", "out": str(out_path)}))
            return
        rows = read_jsonl(args.instances)
        finished = done_ids(out_path)
        todo = [r for r in rows if r.get("valid", True) and r["instance_id"] not in finished]
        if args.limit:
            todo = todo[: args.limit]
        if not todo:
            print(json.dumps({"skipped": "complete", "n": len(rows)}))
            return
        llm, tokenizer, params, load_s = module.load()
        print(json.dumps({"load_s": load_s, "meta": getattr(llm, "_t19_meta", {})}), flush=True)
        batch = int(os.environ.get("MEDVERIF_SCORE_BATCH", "4"))
        for offset in range(0, len(todo), batch):
            chunk = todo[offset : offset + batch]
            scored = module.score_batch(llm, tokenizer, params, chunk)
            append_jsonl(out_path, scored)
        print(json.dumps({"scored": len(todo), "out": str(out_path)}))


if __name__ == "__main__":
    main()
