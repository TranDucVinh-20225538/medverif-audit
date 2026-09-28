#!/usr/bin/env python3
"""Build T7 E1-unit instances (valid DOSE main, old + expand when present)."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t7_e1_unit import generate_all  # noqa: E402

OUT = ROOT / "data/t7/instances_e1_unit.jsonl"
OUT_V3 = ROOT / "data/v3/instances_e1_unit.jsonl"
MANIFEST = ROOT / "data/t7/manifest_e1_unit.json"
FAILURES = ROOT / "data/t7/e1_unit_build_failures.json"
QC = ROOT / "qc/t7_e1_unit_sample.csv"
SEED = 20260929


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_qc_sample(rows: list[dict], n: int = 30) -> None:
    rng = random.Random(SEED)
    pool = list(rows)
    rng.shuffle(pool)
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "instance_id",
                "base_id",
                "condition",
                "unit_pair",
                "span_before",
                "span_after",
                "claim_c0",
                "claim",
                "evidence",
                "expected_verdict",
                "PI_ok",
                "note",
            ]
        )
        for row in pool[:n]:
            diff = row.get("diff") or {}
            side = diff.get("claim") or diff.get("evidence") or {}
            w.writerow(
                [
                    row["instance_id"],
                    row["base_id"],
                    row["condition"],
                    row.get("unit_pair", ""),
                    side.get("span_before", ""),
                    side.get("span_after", ""),
                    row.get("claim_c0", ""),
                    row.get("claim", ""),
                    row.get("evidence", ""),
                    row.get("expected_verdict", ""),
                    "",
                    "",
                ]
            )


def main() -> None:
    instances, failures, meta = generate_all(ROOT)
    instances.sort(key=lambda r: r["instance_id"])
    write_jsonl(OUT, instances)
    write_jsonl(OUT_V3, instances)
    FAILURES.write_text(json.dumps({"failures": failures, **meta}, indent=2) + "\n")
    by_cond = {}
    for r in instances:
        by_cond[r["condition"]] = by_cond.get(r["condition"], 0) + 1
    manifest = {
        **meta,
        "path": str(OUT.relative_to(ROOT)),
        "path_v3": str(OUT_V3.relative_to(ROOT)),
        "by_condition": by_cond,
        "magnitude": "x1000",
        "expected_verdict": "FAIL",
        "qc_sample": str(QC.relative_to(ROOT)),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    write_qc_sample(instances)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
