#!/usr/bin/env python3
"""Held-out QC sheet: non-dev surface/freq/changed + verbatim spot-check."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

INP = ROOT / "data" / "t4" / "eco_classified.jsonl"
DEV = ROOT / "qc" / "eco_PI_ok_labels.csv"
OUT = ROOT / "qc" / "eco_review2.csv"
SEED = 43
N_VERBATIM = 20
TARGET_CATS = frozenset(
    {"exact_surface_variant", "frequency_rephrased", "changed_value"}
)


def main() -> None:
    from t4_eco_compare import load_pi_sheet_keys

    dev = load_pi_sheet_keys(DEV) if DEV.is_file() else set()

    rows = [json.loads(line) for line in INP.open() if line.strip()]
    must = [
        r
        for r in rows
        if (r.get("eco_category") or "") in TARGET_CATS
        and (r["task_id"], r["answerer_id"]) not in dev
    ]
    verbatim_pool = [
        r
        for r in rows
        if r.get("eco_category") == "exact_verbatim"
        and (r["task_id"], r["answerer_id"]) not in dev
    ]
    rng = random.Random(SEED)
    rng.shuffle(verbatim_pool)
    spot = verbatim_pool[: min(N_VERBATIM, len(verbatim_pool))]

    seen = set()
    sample = []
    for r in must + spot:
        key = (r["task_id"], r["answerer_id"])
        if key in seen:
            continue
        seen.add(key)
        sample.append(r)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "task_id",
                "base_id",
                "answerer_id",
                "openrouter_model",
                "eco_category",
                "answer",
                "evidence",
                "target_span_evidence",
                "PI_ok",
                "correct_category",
                "note",
            ]
        )
        for row in sample:
            w.writerow(
                [
                    row.get("task_id"),
                    row.get("base_id"),
                    row.get("answerer_id"),
                    row.get("openrouter_model"),
                    row.get("eco_category"),
                    row.get("answer"),
                    row.get("evidence"),
                    row.get("target_span_evidence"),
                    "",
                    "",
                    "",
                ]
            )
    print(
        f"wrote {OUT} n={len(sample)} "
        f"(non-dev target cats={len(must)}, verbatim spot={len(spot)})"
    )


if __name__ == "__main__":
    main()
