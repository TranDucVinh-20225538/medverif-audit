#!/usr/bin/env python3
"""Build JSONL of main-dose C0 + E1 + INV-unit rows missing from cohort OR scores."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import read_jsonl  # noqa: E402
from non_dose_targets import invalidate_non_dose_row  # noqa: E402
from review_filters import analysis_keep_row  # noqa: E402

OUT = ROOT / "data/v3/instances_main_dose_or_backfill.jsonl"
# Cohort OR encoders for backfill (instance must appear in every file to be "done").
BACKFILL_SCORE_FILES = (
    ROOT / "results/raw/t2_full/v1b_medscore.jsonl",
    ROOT / "results/raw/t2_full/v5_ragas_nli.jsonl",
    ROOT / "results/raw/t6b/full/v1c_medscore.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_gpt4o_mini.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_haiku45.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_mistral_small32.jsonl",
)


def cohort_instance_ids() -> set[str]:
    need: set[str] = set()
    for row in read_jsonl(ROOT / "data/v3/instances_main.jsonl"):
        row = dict(row)
        invalidate_non_dose_row(row)
        if not row.get("valid", True) or not analysis_keep_row(row):
            continue
        if row.get("subset") != "main":
            continue
        cond = row.get("condition")
        mag = row.get("magnitude")
        if cond == "C0" or cond in ("E1-claim", "E1-evid"):
            need.add(row["instance_id"])
        elif cond == "INV-claim" and mag == "unit_conversion":
            need.add(row["instance_id"])
    return need


def scored_ids(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.is_file():
        return out
    for line in path.open():
        if line.strip():
            out.add(json.loads(line)["instance_id"])
    return out


def target_instance_ids() -> set[str]:
    need = cohort_instance_ids()
    scores = {path: scored_ids(path) for path in BACKFILL_SCORE_FILES}
    return {
        iid
        for iid in need
        if any(iid not in scores[path] for path in BACKFILL_SCORE_FILES)
    }


def main() -> None:
    missing = target_instance_ids()
    by_id: dict[str, dict] = {}
    for row in read_jsonl(ROOT / "data/v3/instances_main.jsonl"):
        row = dict(row)
        iid = row.get("instance_id")
        if iid in missing:
            by_id[iid] = row
    rows = [by_id[i] for i in sorted(by_id)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"out": str(OUT), "n": len(rows), "missing_ids": len(missing)}))


if __name__ == "__main__":
    main()
