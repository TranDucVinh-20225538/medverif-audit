#!/usr/bin/env python3
"""IAA review sample (pure sampling from main instances; no generation)."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402

MAIN = ROOT / "data/v3/instances_main.jsonl"
OUT = ROOT / "qc/iaa_sample.csv"
GUIDE = ROOT / "qc/iaa_guidelines.md"
MANIFEST = ROOT / "notes/iaa_sample_manifest.json"


def main() -> None:
    rows = [
        r
        for r in read_jsonl(MAIN)
        if r.get("valid", True)
        and r.get("subset") == "main"
        and r.get("condition") in ("C0", "E1-claim", "E1-evid", "INV-claim")
    ]
    rng = random.Random(2026)
    sample = rng.sample(rows, min(60, len(rows)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "instance_id",
                "base_id",
                "condition",
                "magnitude",
                "expected_verdict",
                "reviewer_a",
                "reviewer_b",
            ]
        )
        for r in sample:
            w.writerow(
                [
                    r["instance_id"],
                    r["base_id"],
                    r["condition"],
                    r.get("magnitude"),
                    r.get("expected_verdict"),
                    "",
                    "",
                ]
            )
    GUIDE.write_text(
        "# IAA guidelines\n\n"
        "Mark `reviewer_a` / `reviewer_b` as PASS or FAIL for whether the claim is supported by the evidence.\n"
        "Do not edit claim/evidence text. Disagreements feed `scripts/iaa_cohen_kappa.py`.\n"
    )
    MANIFEST.write_text(json.dumps({"n": len(sample), "csv": str(OUT.relative_to(ROOT))}, indent=2) + "\n")
    print(json.dumps({"n": len(sample)}, indent=2))


if __name__ == "__main__":
    main()
