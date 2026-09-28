#!/usr/bin/env python3
"""Build T3 INV-family instances (rule-based, claim-side) → data/v3/instances_inv_families.jsonl."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inv_families import FAMILY_MAG, generate_inv_family_instances  # noqa: E402

OUT_V3 = ROOT / "data" / "v3" / "instances_inv_families.jsonl"
OUT_T3 = ROOT / "data" / "t3" / "instances_inv_families.jsonl"
MANIFEST = ROOT / "data" / "t3" / "manifest_inv_families.json"
QC_CSV = ROOT / "qc" / "inv_families_sample.csv"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_qc_sample(rows: list[dict], seed: int = 42, per_family: int = 30) -> None:
    by_mag: dict[str, list[dict]] = {}
    for row in rows:
        by_mag.setdefault(row["magnitude"], []).append(row)
    rng = random.Random(seed)
    QC_CSV.parent.mkdir(parents=True, exist_ok=True)
    with QC_CSV.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "instance_id",
                "base_id",
                "family",
                "inv_tag",
                "span_before",
                "span_after",
                "claim_c0",
                "claim_inv",
                "evidence",
                "PI_ok",
            ]
        )
        for mag in sorted(by_mag):
            pool = list(by_mag[mag])
            rng.shuffle(pool)
            for row in pool[:per_family]:
                diff = row.get("diff") or {}
                claim = diff.get("claim") or {}
                w.writerow(
                    [
                        row["instance_id"],
                        row["base_id"],
                        mag,
                        diff.get("inv_tag", ""),
                        claim.get("span_before", ""),
                        claim.get("span_after", ""),
                        row.get("claim_c0", ""),
                        row.get("claim", ""),
                        row.get("evidence", ""),
                        "",
                    ]
                )


def main() -> None:
    instances, counts = generate_inv_family_instances(ROOT)
    instances.sort(key=lambda r: r["instance_id"])
    write_jsonl(OUT_V3, instances)
    write_jsonl(OUT_T3, instances)
    meta = {
        "path_v3": str(OUT_V3.relative_to(ROOT)),
        "path_t3": str(OUT_T3.relative_to(ROOT)),
        "n_instances": len(instances),
        "by_family": counts,
        "families": list(FAMILY_MAG.values()),
        "ready_for_scoring": len(instances) > 0,
    }
    MANIFEST.write_text(json.dumps(meta, indent=2) + "\n")
    write_qc_sample(instances)
    print(json.dumps(meta, indent=2))
    print(f"wrote QC {QC_CSV}")


if __name__ == "__main__":
    main()
