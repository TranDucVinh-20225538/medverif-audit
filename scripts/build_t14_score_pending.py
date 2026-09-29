#!/usr/bin/env python3
"""T14 score pending: OpenRouter (V1/V4/V1b/V5 + T6-B) and node30 (V2/V3/T6-A/Bespoke)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data/t14/instances_t14.jsonl"
OUT_OR = ROOT / "data/t14/instances_t14_pending_openrouter.jsonl"
OUT_N30 = ROOT / "data/v3/instances_t14_pending_node30.jsonl"
RAW_T14 = ROOT / "results/raw/t14"
META = ROOT / "notes/t14_score_pending_manifest.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def scored_ids() -> set[str]:
    done: set[str] = set()
    if not RAW_T14.is_dir():
        return done
    for path in RAW_T14.glob("*.jsonl"):
        for line in path.open():
            if line.strip():
                done.add(json.loads(line)["instance_id"])
    return done


def main() -> None:
    all_rows = read_jsonl(INST)
    done = scored_ids()
    pending = [r for r in all_rows if r["instance_id"] not in done]
    write_jsonl(OUT_OR, pending)
    write_jsonl(OUT_N30, pending)
    manifest = {
        "instances_total": len(all_rows),
        "pending": len(pending),
        "scored_in_raw_t14": len(done),
        "openrouter_verifiers": [
            "v1_medscore",
            "v4_ragas_nli",
            "v1b_medscore",
            "v5_ragas_nli",
            "v6_ragas_gpt4o_mini",
            "v6_ragas_haiku45",
            "v6_ragas_llama31_8b",
            "v6_ragas_mistral_small32",
        ],
        "openrouter_note": "T6-B LLM judges on HPC; keep total OpenRouter spend ≤ USD 3 for T14 pack.",
        "node30_verifiers": [
            "v2a_minicheck",
            "v3_alignscore",
            "v2b_bespoke",
            "t6a_minicheck_roberta",
            "t6a_minicheck_deberta",
            "t6a_alignscore_base",
            "t6a_summac_zs",
            "t6a_summac_conv",
            "t6a_hhem",
            "t6a_granite_guardian",
        ],
        "paths": {
            "instances": str(INST.relative_to(ROOT)),
            "pending_openrouter": str(OUT_OR.relative_to(ROOT)),
            "pending_node30": str(OUT_N30.relative_to(ROOT)),
            "score_to": "results/raw/t14/",
        },
        "node30_cmd": "jobs/run_t14_score_node30.sh",
        "openrouter_cmd": "jobs/run_t14_score_openrouter.sh",
    }
    META.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
