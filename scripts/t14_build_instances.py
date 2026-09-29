#!/usr/bin/env python3
"""Build T14 repr instances + qc/t14_sample.csv (30 per family, empty PI_ok)."""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t14_repr import MAG_THOUS, MAG_UNIT, MAG_WORDS  # noqa: E402
from t14_repr import build_for_base  # noqa: E402

BASES = ROOT / "data" / "base_pairs.jsonl"
MAIN = ROOT / "data" / "v3" / "instances_main.jsonl"
OUT = ROOT / "data" / "t14" / "instances_t14.jsonl"
OUT_V3 = ROOT / "data" / "v3" / "instances_t14.jsonl"
MANIFEST = ROOT / "data" / "t14" / "manifest_t14.json"
FAILURES = ROOT / "data" / "t14" / "t14_build_failures.json"
QC = ROOT / "qc" / "t14_sample.csv"
SEED = 20261002
PER_FAMILY = 30


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main_c0_bases() -> set[str]:
    out: set[str] = set()
    for row in read_jsonl(MAIN):
        if not row.get("valid", True):
            continue
        if row.get("type") != "DOSE" or row.get("subset") != "main":
            continue
        if row.get("condition") == "C0":
            out.add(row["base_id"])
    return out


def write_qc_sample(rows: list[dict]) -> None:
    by_mag: dict[str, list[dict]] = {}
    for row in rows:
        by_mag.setdefault(row["magnitude"], []).append(row)
    rng = random.Random(SEED)
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "instance_id",
                "base_id",
                "t14_family",
                "span_before",
                "span_after",
                "claim_c0",
                "claim",
                "expected_verdict",
                "PI_ok",
                "note",
            ]
        )
        for mag in (MAG_UNIT, MAG_THOUS, MAG_WORDS):
            pool = list(by_mag.get(mag, []))
            rng.shuffle(pool)
            for row in pool[:PER_FAMILY]:
                diff = (row.get("diff") or {}).get("claim") or {}
                w.writerow(
                    [
                        row["instance_id"],
                        row["base_id"],
                        row.get("t14_family", mag),
                        diff.get("span_before", ""),
                        diff.get("span_after", ""),
                        row.get("claim_c0", ""),
                        row.get("claim", ""),
                        row.get("expected_verdict", ""),
                        "",
                        "",
                    ]
                )


def main() -> None:
    c0_bases = main_c0_bases()
    instances: list[dict] = []
    failures: list[dict] = []
    for base in read_jsonl(BASES):
        if base.get("id") not in c0_bases:
            continue
        if base.get("subset") not in (None, "main"):
            continue
        rows, fails = build_for_base(base)
        instances.extend(rows)
        failures.extend(fails)
    instances.sort(key=lambda r: r["instance_id"])
    write_jsonl(OUT, instances)
    write_jsonl(OUT_V3, instances)
    by_mag = Counter(r["magnitude"] for r in instances)
    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "path_v3": str(OUT_V3.relative_to(ROOT)),
        "n_instances": len(instances),
        "by_magnitude": dict(by_mag),
        "main_c0_bases": len(c0_bases),
        "qc_sample": str(QC.relative_to(ROOT)),
        "families": {
            MAG_UNIT: "unit spelled out (mg↔milligrams, …)",
            MAG_THOUS: "thousands separator (≥1000 numerals)",
            MAG_WORDS: "number words (≤10 tablets/doses/times)",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    FAILURES.write_text(json.dumps({"failures": failures}, indent=2) + "\n")
    write_qc_sample(instances)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
