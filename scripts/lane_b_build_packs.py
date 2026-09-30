#!/usr/bin/env python3
"""Lane B: calibration (200) + main E1-evid packs for local T6-A scoring."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lane_a_instance_filters import lane_b_e1_evid_row  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402

CPU_EARLY = ROOT / "data/v3/instances_cpu_early.jsonl"
MAIN = ROOT / "data/v3/instances_main.jsonl"
NODE30 = ROOT / "results/raw_node30"
OUT_CAL = ROOT / "data/lane_b/calibration_200.jsonl"
OUT_E1 = ROOT / "data/lane_b/main_e1_evid.jsonl"
MANIFEST = ROOT / "notes/lane_b_packs.json"


def main() -> None:
    early = [r for r in read_jsonl(CPU_EARLY) if r.get("valid", True)]
    node_ids: set[str] = set()
    for name in ("t6_minicheck_roberta.jsonl", "v2a_minicheck.jsonl"):
        p = NODE30 / name
        if p.is_file():
            for row in read_jsonl(p):
                node_ids.add(row["instance_id"])
    pool = [r for r in early if r["instance_id"] in node_ids]
    rng = random.Random(42)
    rng.shuffle(pool)
    cal = pool[:200]
    OUT_CAL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CAL.open("w") as handle:
        for row in cal:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    raw_e1 = sum(
        1
        for r in read_jsonl(MAIN)
        if r.get("subset") == "main" and r.get("condition") == "E1-evid" and r.get("valid", True)
    )
    evid = [r for r in read_jsonl(MAIN) if lane_b_e1_evid_row(r)]
    with OUT_E1.open("w") as handle:
        for row in evid:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "calibration_n": len(cal),
        "calibration_path": str(OUT_CAL.relative_to(ROOT)),
        "e1_evid_n": len(evid),
        "e1_evid_n_raw_valid": raw_e1,
        "e1_evid_filter": "non_dose_targets + valid + analysis_keep_row (POL flip_ok)",
        "e1_evid_path": str(OUT_E1.relative_to(ROOT)),
        "node30_overlap_pool": len(pool),
        "note_221": "independent_audit_gaps.md cites 221 E1-evid; current main JSONL has "
        f"{raw_e1} valid rows — non-dose bases already removed from pack; filtered n={len(evid)}",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
