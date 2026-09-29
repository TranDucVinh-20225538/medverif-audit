#!/usr/bin/env python3
"""Build T17 down-dose pack + QC sample (40 rows)."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t17_downdose import generate_all  # noqa: E402

OUT = ROOT / "data/v3/t17_downdose.jsonl"
FAILURES = ROOT / "data/v3/t17_downdose_build_failures.json"
MANIFEST = ROOT / "notes/t17_downdose_manifest.json"
QC = ROOT / "qc/t17_sample.csv"
SEED = 20260929


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_qc_sample(rows: list[dict]) -> None:
    rng = random.Random(SEED)
    by_mag: dict[str, list[dict]] = {}
    for r in rows:
        mag = r.get("magnitude") or ""
        by_mag.setdefault(mag, []).append(r)
    picks: list[dict] = []
    for mag, n in (("down2", 15), ("down10", 10), ("unit-down", 15)):
        pool = list(by_mag.get(mag, []))
        rng.shuffle(pool)
        picks.extend(pool[:n])
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["instance_id", "span_before", "span_after", "human_ok", "note"])
        for row in picks:
            diff = row.get("diff") or {}
            side = row.get("edit_side") or "claim"
            block = diff.get(side) or {}
            w.writerow(
                [
                    row["instance_id"],
                    block.get("span_before", ""),
                    block.get("span_after", ""),
                    "",
                    f"{row.get('condition')} {side}",
                ]
            )


def main() -> None:
    instances, failures, meta = generate_all(ROOT)
    instances.sort(key=lambda r: r["instance_id"])
    write_jsonl(OUT, instances)
    FAILURES.write_text(json.dumps(failures, indent=2) + "\n")
    write_qc_sample(instances)
    manifest = {**meta, "path": str(OUT.relative_to(ROOT)), "qc_sample": str(QC.relative_to(ROOT))}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
