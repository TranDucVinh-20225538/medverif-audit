#!/usr/bin/env python3
"""Re-export qc/t18_sample.csv with review columns (FINAL generation)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data/t18/instances_t18.jsonl"
QC = ROOT / "qc/t18_sample.csv"
MANIFEST = ROOT / "notes/t18_qc_final.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def span_fields(row: dict) -> tuple[str, str, str, str]:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    evid = diff.get("evidence") or {}
    span_before = claim.get("span_before") or evid.get("span_before") or ""
    span_after = claim.get("span_after") or evid.get("span_after") or ""
    return (
        row.get("claim_c0") or row.get("claim") or "",
        row.get("claim") or "",
        row.get("evidence") or "",
        span_before,
        span_after,
    )


def main() -> None:
    rows = read_jsonl(INST)
    inv = [r for r in rows if r.get("condition") == "INV-claim" and r.get("valid", True)]
    inv.sort(key=lambda r: r.get("instance_id") or "")
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "instance_id",
                "base_id",
                "condition",
                "claim_c0",
                "claim",
                "evidence",
                "span_before",
                "span_after",
                "PI_ok",
                "notes",
            ]
        )
        for row in inv:
            c0, claim, evid, sb, sa = span_fields(row)
            w.writerow(
                [
                    row.get("instance_id"),
                    row.get("base_id"),
                    row.get("condition"),
                    c0,
                    claim,
                    evid,
                    sb,
                    sa,
                    "",
                    "FINAL export 2026-09-30",
                ]
            )
    doc = {
        "status": "FINAL",
        "inv_rows": len(inv),
        "qc_path": str(QC.relative_to(ROOT)),
        "instances_path": str(INST.relative_to(ROOT)),
    }
    MANIFEST.write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
