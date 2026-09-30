#!/usr/bin/env python3
"""Stratified random sample of T24b rule edits for author QC."""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path = ROOT / "src"
import sys

sys.path.insert(0, str(ROOT / "analysis"))

from analyze import read_jsonl  # noqa: E402

INST = ROOT / "data/t24/instances_t24b.jsonl"
OUT = ROOT / "qc/t24b_edit_sample.csv"
SEED = 42

STRATA = (
    ("T24b-unit-up", 7),
    ("T24b-unit-down", 7),
    ("T24b-value-x10", 6),
)


def span_before(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or diff
    if isinstance(claim, dict) and claim.get("span_before"):
        return str(claim["span_before"])
    return str(diff.get("span_before") or row.get("claim_span") or "")


def span_after(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or diff
    if isinstance(claim, dict) and claim.get("span_after"):
        return str(claim["span_after"])
    return str(row.get("claim_span") or "")


def main() -> None:
    rows = read_jsonl(INST)
    c0_claim = {r["question_id"]: r["claim"] for r in rows if r.get("condition") == "T24b-C0"}
    by_cond: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        cond = r.get("condition") or ""
        if cond == "T24b-C0":
            continue
        by_cond[cond].append(r)

    rng = random.Random(SEED)
    picked: list[dict] = []
    for cond, k in STRATA:
        pool = by_cond.get(cond, [])
        if len(pool) < k:
            raise SystemExit(f"not enough rows for {cond}: have {len(pool)} need {k}")
        picked.extend(rng.sample(pool, k))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(
            handle,
            fieldnames=[
                "question_id",
                "condition",
                "answer_before",
                "answer_after",
                "span_before",
                "span_after",
                "edit_ok",
            ],
        )
        w.writeheader()
        for r in sorted(picked, key=lambda x: (x["condition"], x["question_id"])):
            qid = r["question_id"]
            w.writerow(
                {
                    "question_id": qid,
                    "condition": r["condition"],
                    "answer_before": c0_claim.get(qid, ""),
                    "answer_after": r.get("claim") or "",
                    "span_before": span_before(r),
                    "span_after": span_after(r),
                    "edit_ok": "",
                }
            )
    print(f"wrote {OUT} ({len(picked)} rows)")


if __name__ == "__main__":
    main()
