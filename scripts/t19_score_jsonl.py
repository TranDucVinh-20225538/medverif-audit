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
    parser.add_argument(
        "--instances",
        type=Path,
        default=None,
        help="default: data/t19/instances_t19.jsonl or MEDVERIF_T19_INSTANCES",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.instances is None:
        env_inst = os.environ.get("MEDVERIF_T19_INSTANCES", "").strip()
        args.instances = Path(env_inst) if env_inst else (ROOT / "data/t19/instances_t19.jsonl")
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
        print(
            json.dumps(
                {
                    "phase": "load",
                    "todo": len(todo),
                    "out": str(out_path),
                    "hf_offline": os.environ.get("HF_HUB_OFFLINE", ""),
                }
            ),
            flush=True,
        )
        llm, tokenizer, params, load_s = module.load()
        print(
            json.dumps(
                {
                    "load_s": load_s,
                    "loaded_model_in_s": load_s,
                    "meta": getattr(llm, "_t19_meta", {}),
                }
            ),
            flush=True,
        )
        print(f"loaded model in {load_s:.1f}s", flush=True)
        batch = max(1, int(os.environ.get("MEDVERIF_SCORE_BATCH", "4")))
        flush_every = max(1, int(os.environ.get("MEDVERIF_SCORE_FLUSH_EVERY", "20")))
        scored_n = 0
        base_lines = len(finished)
        for offset in range(0, len(todo), batch):
            chunk = todo[offset : offset + batch]
            scored = module.score_batch(llm, tokenizer, params, chunk)
            append_jsonl(out_path, scored)
            scored_n += len(scored)
            if scored_n % flush_every < len(scored) or scored_n == len(todo):
                print(
                    json.dumps(
                        {
                            "progress": scored_n,
                            "total": len(todo),
                            "out_lines": base_lines + scored_n,
                        }
                    ),
                    flush=True,
                )
        print(json.dumps({"scored": scored_n, "out": str(out_path)}), flush=True)


if __name__ == "__main__":
    main()
