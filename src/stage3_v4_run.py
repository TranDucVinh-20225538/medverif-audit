"""Score cpu_early main + threshold with one V4 load."""

from __future__ import annotations

import importlib
from pathlib import Path

from verifiers.io_utils import append_jsonl, done_ids, read_jsonl

ROOT = Path("/data2/hpcshared/medverif-audit")


def score_file(module, llm, tokenizer, params, instances: Path, out: Path) -> None:
    rows = read_jsonl(instances)
    finished = done_ids(out)
    todo = [row for row in rows if row.get("valid", True) and row["instance_id"] not in finished]
    if not todo:
        return
    scored = module.score_batch(llm, tokenizer, params, todo)
    append_jsonl(out, scored)


def main() -> None:
    import vllm_graceful

    module = importlib.import_module("verifiers.v4_ragas_nli")
    llm, tokenizer, params, load_s = module.load()
    print(f"v4 load_s={load_s:.1f}", flush=True)
    try:
        score_file(
            module, llm, tokenizer, params,
            ROOT / "data" / "v3" / "instances_cpu_main.jsonl",
            ROOT / "results" / "raw" / "v4_ragas_nli.jsonl",
        )
        score_file(
            module, llm, tokenizer, params,
            ROOT / "data" / "v3" / "instances_cpu_threshold.jsonl",
            ROOT / "results" / "raw_threshold" / "v4_ragas_nli.jsonl",
        )
    finally:
        vllm_graceful.shutdown_all()


if __name__ == "__main__":
    main()
