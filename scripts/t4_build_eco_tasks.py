#!/usr/bin/env python3
"""Build T4 ecological tasks from valid DOSE bases."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inv_families import load_bases, valid_base_ids_from_instances  # noqa: E402


def patient_question(base: dict) -> str:
    return (
        "You are helping a patient understand their prescription. "
        "Using ONLY the medical excerpt below, answer in 1–3 plain sentences: "
        "what dose and how should they take the medication?\n\n"
        f"Excerpt:\n{base['evidence']}"
    )

OUT = ROOT / "data" / "t4" / "eco_tasks.jsonl"
MANIFEST = ROOT / "data" / "t4" / "manifest_eco.json"
SEED = 20260929
# 0 or unset cap = all valid DOSE bases (~148).
def _max_tasks(n_pool: int) -> int:
    raw = __import__("os").environ.get("MEDVERIF_T4_MAX_TASKS", "0").strip()
    if not raw or raw == "0":
        return n_pool
    return min(int(raw), n_pool)


def main() -> None:
    inst_paths = [
        ROOT / "data/v3/instances_main.jsonl",
        ROOT / "data/v3/instances_threshold.jsonl",
        ROOT / "data/expand/instances_cpu_early.jsonl",
    ]
    valid_ids = valid_base_ids_from_instances(inst_paths)
    bases = load_bases(ROOT)
    pool = [bases[bid] for bid in sorted(valid_ids) if bid in bases]
    rng = random.Random(SEED)
    rng.shuffle(pool)
    cap = _max_tasks(len(pool))
    pool = pool[:cap]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for base in pool:
            task = {
                "task_id": f"{base['id']}__eco",
                "base_id": base["id"],
                "type": "DOSE",
                "evidence": base["evidence"],
                "claim_c0": base["claim"],
                "target_span_evidence": base.get("target_span_evidence"),
                "target_span_claim": base.get("target_span_claim"),
                "prompt": patient_question(base),
                "subset": base.get("subset", "main"),
            }
            handle.write(json.dumps(task, ensure_ascii=False) + "\n")
    meta = {"n_tasks": len(pool), "path": str(OUT.relative_to(ROOT)), "max_tasks_cap": cap}
    MANIFEST.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
