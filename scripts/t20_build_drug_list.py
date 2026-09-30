#!/usr/bin/env python3
"""T20 step 1: ~100 distinct drugs with dose spans from main + main_ext DOSE bases."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import DRUG_RE, DOSE_CONTEXT_RE  # noqa: E402

OUT = ROOT / "data/t20/drug_list.jsonl"
MANIFEST = ROOT / "notes/t20_drug_list_manifest.json"
TARGET = 100

DOSE_IN_CLAIM = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(mg|g|mcg|µg|μg|mg/kg|g/kg|units?|IU|mL|ml)\b",
    re.I,
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def drug_from_row(row: dict) -> str | None:
    claim = row.get("claim_c0") or row.get("claim") or ""
    m = DRUG_RE.search(claim)
    if not m:
        return None
    if not DOSE_CONTEXT_RE.search(claim) and not DOSE_IN_CLAIM.search(claim):
        return None
    return m.group(0).strip().lower()


def main() -> None:
    paths = [
        ROOT / "data/v3/instances_main.jsonl",
        ROOT / "data/main_ext/instances_main_ext.jsonl",
    ]
    by_drug: dict[str, dict] = {}
    for path in paths:
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            if not row.get("valid", True):
                continue
            if row.get("type") != "DOSE":
                continue
            drug = drug_from_row(row)
            if not drug:
                continue
            bid = row.get("base_id") or row.get("id")
            claim = row.get("claim_c0") or row.get("claim") or ""
            rec = by_drug.setdefault(
                drug,
                {"drug": drug, "bases": set(), "packs": set(), "example_claim": claim[:200]},
            )
            rec["bases"].add(str(bid))
            rec["packs"].add(path.parent.name)
    drugs = sorted(by_drug.values(), key=lambda r: (-len(r["bases"]), r["drug"]))
    picked = drugs[:TARGET]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for rec in picked:
            handle.write(
                json.dumps(
                    {
                        "drug": rec["drug"],
                        "n_bases": len(rec["bases"]),
                        "bases": sorted(rec["bases"])[:8],
                        "packs": sorted(rec["packs"]),
                        "example_claim": rec["example_claim"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    manifest = {
        "target": TARGET,
        "distinct_drugs_found": len(by_drug),
        "written": len(picked),
        "path": str(OUT.relative_to(ROOT)),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
