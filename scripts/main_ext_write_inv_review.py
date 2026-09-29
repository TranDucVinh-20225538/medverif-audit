#!/usr/bin/env python3
"""Write qc/main_ext_review.csv for all whitelist INV-unit rows in main_ext cohort."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402

INST = ROOT / "data/main_ext/instances_main_ext.jsonl"
QC = ROOT / "qc/main_ext_review.csv"
REPORT = ROOT / "notes/main_ext_cohort_report.md"


def inv_row_fields(row: dict) -> dict:
    diff = row.get("diff") or {}
    claim_diff = diff.get("claim") if isinstance(diff.get("claim"), dict) else {}
    original = claim_diff.get("span_before") or row.get("claim_span") or ""
    converted = claim_diff.get("span_after") or row.get("claim_span") or ""
    claim_after = row.get("claim") or ""
    natural = row.get("claim_c0") or ""
    note = row.get("unit_inv_source") or diff.get("unit_inv_source") or ""
    return {
        "base_id": row.get("base_id", ""),
        "original": original,
        "converted": converted,
        "claim_after": claim_after,
        "natural": natural,
        "note": note,
    }


def main() -> None:
    if not INST.is_file():
        raise SystemExit(f"missing {INST}")
    instances = read_jsonl(INST)
    inv = [
        r
        for r in instances
        if r.get("condition") == "INV-claim"
        and r.get("magnitude") == "unit_conversion"
        and (r.get("unit_inv_source") == "author_whitelist" or (r.get("diff") or {}).get("unit_inv_source") == "author_whitelist")
    ]
    bases = {r["base_id"] for r in inv if r.get("base_id")}
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="") as handle:
        w = csv.DictWriter(
            handle,
            fieldnames=["base_id", "original", "converted", "claim_after", "natural", "note"],
        )
        w.writeheader()
        for row in inv:
            w.writerow(inv_row_fields(row))
    stage1_bases = 0
    bp = ROOT / "data/main_ext/stage1/base_pairs.jsonl"
    if bp.is_file():
        stage1_bases = sum(1 for _ in read_jsonl(bp))
    md = [
        "# main_ext cohort (scoring scope)",
        "",
        f"- **Stage1 expansion bases** (Qwen/Phi pipeline artifact, not the main_ext pack): **{stage1_bases}**",
        f"- **main_ext bases** (`data/main_ext/bases_main_ext.jsonl`): **{sum(1 for _ in read_jsonl(ROOT / 'data/main_ext/bases_main_ext.jsonl')) if (ROOT / 'data/main_ext/bases_main_ext.jsonl').is_file() else 0}**",
        f"- **Bases with a valid author_whitelist INV-unit row** (main_ext scoring cohort): **{len(bases)}**",
        f"- **INV-unit instance rows** in review CSV: **{len(inv)}**",
        "",
        "Only rows in `data/main_ext/instances_main_ext.jsonl` (subset=`main_ext`) are scored as main_ext.",
        "Stage1 `validator_raw.jsonl` / 892-base counts are expand funnel diagnostics only.",
        "",
        f"Review file: `{QC.relative_to(ROOT)}`",
        "",
    ]
    REPORT.write_text("\n".join(md) + "\n")
    print(json.dumps({"inv_rows": len(inv), "bases": len(bases), "qc": str(QC)}, indent=2))


if __name__ == "__main__":
    main()
