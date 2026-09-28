"""Build qc/inv_manual_review.csv from accepted paraphrase rows."""

from __future__ import annotations

import csv
import random
from pathlib import Path

DOSE_SAMPLE_SEED = 2026
DOSE_SAMPLE_N = 40

FIELDNAMES = (
    "base_id",
    "type",
    "mechanism",
    "mapping",
    "sample",
    "original",
    "rewrite",
    "PI_ok",
)


def build_manual_review_rows(accepted: list[dict]) -> list[dict]:
    """Order: all POLARITY, then 40 random DOSE (sample=1), then other DOSE (sample=0)."""
    pol: list[dict] = []
    dose: list[dict] = []
    for row in accepted:
        entry = {
            "base_id": row["base_id"],
            "type": row["type"],
            "mechanism": row.get("mechanism") or "",
            "mapping": row.get("mapping") or "",
            "sample": "",
            "original": row["original"],
            "rewrite": row["rewrite"],
            "PI_ok": "",
        }
        if row["type"] == "POLARITY":
            pol.append(entry)
        else:
            dose.append(entry)
    pol.sort(key=lambda r: r["base_id"])
    dose.sort(key=lambda r: r["base_id"])
    rng = random.Random(DOSE_SAMPLE_SEED)
    if len(dose) <= DOSE_SAMPLE_N:
        sampled = dose
        rest: list[dict] = []
    else:
        picks = rng.sample(dose, DOSE_SAMPLE_N)
        pick_ids = {r["base_id"] for r in picks}
        sampled = sorted(picks, key=lambda r: r["base_id"])
        rest = [r for r in dose if r["base_id"] not in pick_ids]
    for r in sampled:
        r["sample"] = "1"
    for r in rest:
        r["sample"] = "0"
    return pol + sampled + rest


def write_manual_review_csv(path: Path, accepted: list[dict]) -> None:
    rows = build_manual_review_rows(accepted)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
