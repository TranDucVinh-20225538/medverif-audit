#!/usr/bin/env python3
"""Human flip_ok Y bases missing node30 scores — pending pack for V2/V3/T6-A."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPU = ROOT / "data/v3/instances_cpu_early.jsonl"
POL_CSV = ROOT / "qc/e1_pol_review.csv"
RAW = ROOT / "results/raw"
OUT = ROOT / "data/v3/instances_pol_flip_pending_node30.jsonl"
MANIFEST = ROOT / "notes/pol_flip_pending_node30_manifest.json"

# 14 bases with V1/V4 flip scores but no V2a on E1-claim (2026-09-29 audit)
DEFAULT_BASES = [
    "P0020",
    "P0033",
    "P0035",
    "P0044",
    "P0048",
    "P0052",
    "P0067",
    "P0073",
    "P0092",
    "P0116",
    "P0120",
    "P0132",
    "P0161",
    "P0171",
]


def flip_ok_bases() -> set[str]:
    out: set[str] = set()
    for row in csv.DictReader(POL_CSV.open()):
        if (row.get("PI_ok") or "").strip().upper() == "Y":
            out.add(row["base_id"].strip())
    return out


def scored_v2a() -> set[str]:
    path = RAW / "v2a_minicheck.jsonl"
    if not path.is_file():
        return set()
    return {json.loads(line)["instance_id"] for line in path.open() if line.strip()}


def main() -> None:
    bases = flip_ok_bases()
    target_bases = set(DEFAULT_BASES) & bases
    done = scored_v2a()
    rows: list[dict] = []
    for line in CPU.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if not row.get("valid", True):
            continue
        if row["base_id"] not in target_bases:
            continue
        if row["instance_id"] in done:
            continue
        rows.append(row)
    rows.sort(key=lambda r: r["instance_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "flip_ok_bases_total": len(bases),
        "target_bases": sorted(target_bases),
        "n_pending_rows": len(rows),
        "score_to": "results/raw/v2a_minicheck.jsonl, v3_alignscore.jsonl (+ t6a in raw/)",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
