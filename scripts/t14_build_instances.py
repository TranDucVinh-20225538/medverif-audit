#!/usr/bin/env python3
"""Build T14 repr instances + qc/t14_sample.csv (stratified PI_ok empty)."""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t14_repr import MAG_SPACING, MAG_SYMBOL, MAG_THOUS, MAG_UNIT  # noqa: E402
from t14_repr import build_for_base, _try_thousands  # noqa: E402

BASES = ROOT / "data" / "base_pairs.jsonl"
MAIN = ROOT / "data" / "v3" / "instances_main.jsonl"
OUT = ROOT / "data" / "t14" / "instances_t14.jsonl"
OUT_V3 = ROOT / "data" / "v3" / "instances_t14.jsonl"
MANIFEST = ROOT / "data" / "t14" / "manifest_t14.json"
FAILURES = ROOT / "data" / "t14" / "t14_build_failures.json"
QC = ROOT / "qc" / "t14_sample.csv"
SEED = 20261002
PER_UNIT_SPELL = 30
PER_NEW_FAMILY = 15


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


def thousands_sep_appendix_count(bases: list[dict]) -> int:
    n = 0
    for base in bases:
        if base.get("type") != "DOSE":
            continue
        claim0 = base["claim"]
        c0, c1 = base["claim_span_start"], base["claim_span_end"]
        span = claim0[c0:c1]
        if _try_thousands(span):
            n += 1
    return n


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
        for mag, cap in (
            (MAG_UNIT, PER_UNIT_SPELL),
            (MAG_SPACING, PER_NEW_FAMILY),
            (MAG_SYMBOL, PER_NEW_FAMILY),
        ):
            pool = list(by_mag.get(mag, []))
            rng.shuffle(pool)
            for row in pool[:cap]:
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
    all_bases = [b for b in read_jsonl(BASES) if b.get("id") in c0_bases and b.get("subset") in (None, "main")]
    instances: list[dict] = []
    failures: list[dict] = []
    for base in all_bases:
        rows, fails = build_for_base(base)
        instances.extend(rows)
        failures.extend(fails)
    instances.sort(key=lambda r: r["instance_id"])
    write_jsonl(OUT, instances)
    write_jsonl(OUT_V3, instances)
    by_mag = Counter(r["magnitude"] for r in instances)
    thous_n = thousands_sep_appendix_count(all_bases)
    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "path_v3": str(OUT_V3.relative_to(ROOT)),
        "n_instances": len(instances),
        "by_magnitude": dict(by_mag),
        "main_c0_bases": len(c0_bases),
        "qc_sample": str(QC.relative_to(ROOT)),
        "appendix": {
            "thousands_sep": f"Not scored in main pack; n={thous_n} bases would qualify (comma/plain ≥1000).",
            "number_words": "Dropped (no generator rows in main DOSE spans).",
        },
        "families": {
            MAG_UNIT: "unit spelled out (mg↔milligrams, …)",
            MAG_SPACING: 'spacing (e.g. "500 mg" ↔ "500mg")',
            MAG_SYMBOL: "microgram symbol (mcg ↔ µg ↔ ug)",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    FAILURES.write_text(json.dumps({"failures": failures}, indent=2) + "\n")
    write_qc_sample(instances)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
