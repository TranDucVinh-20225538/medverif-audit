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
ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", required=True)
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    from scoring_lock import exclusive_score_lock

    out_path = args.out if args.out.is_absolute() else (ROOT / args.out)
    with exclusive_score_lock(args.verifier, out_path) as acquired:
        if not acquired:
            print(
                json.dumps(
                    {
                        "skipped": "already_running",
                        "verifier": args.verifier,
                        "out": str(out_path),
                    }
                )
            )
            return
        _run_score(args, out_path)


def _run_score(args: argparse.Namespace, out_path: Path) -> None:
    module = importlib.import_module(f"verifiers.{args.verifier}")
    if USE_OR:
        from verifier_registry import apply_env_defaults, expected_openrouter

        apply_env_defaults(args.verifier)
        spec = expected_openrouter(args.verifier)
        if spec:
            print(
                json.dumps(
                    {
                        "registry_model": spec["openrouter_model"],
                        "registry_provider": spec.get("provider"),
                    }
                ),
                flush=True,
            )
    rows = read_jsonl(args.instances)
    finished = done_ids(out_path)
    todo = [row for row in rows if row.get("valid", True) and row["instance_id"] not in finished]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print(json.dumps({"verifier": args.verifier, "skipped": "complete", "n": len(rows)}))
        return
    default_batch = "4" if (ROOT / ".cache" / "g_full.active").exists() else "8"
    batch = int(os.environ.get("MEDVERIF_SCORE_BATCH", default_batch))
    llm, tokenizer, params, load_s = module.load()
    if not USE_OR:
        vllm_graceful.register(llm)
    scored_all: list[dict] = []
    try:
        for offset in range(0, len(todo), batch):
            chunk = todo[offset : offset + batch]
            scored = module.score_batch(llm, tokenizer, params, chunk)
            if USE_OR:
                from verifier_registry import assert_row_model

                for row in scored:
                    assert_row_model(args.verifier, row)
            append_jsonl(out_path, scored)
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
        "out": str(out_path),
    }))


if __name__ == "__main__":
    main()
