#!/usr/bin/env python3
"""Build qc/e1_pol_review.csv for manual PI review of POLARITY E1-claim flips."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "v3" / "instances_audit.jsonl"
OUT = ROOT / "qc" / "e1_pol_review.csv"
FIELDNAMES = ("base_id", "flip_mechanism", "original_claim", "flipped_claim", "PI_ok")


def read_jsonl(path: Path) -> list[dict]:
    import json

    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    audit = read_jsonl(AUDIT)
    c0_rows = [
        r
        for r in audit
        if r.get("type") == "POLARITY"
        and r.get("condition") == "C0"
        and r.get("valid")
        and r.get("subset") == "main"
    ]
    e1_by_base = {
        r["base_id"]: r
        for r in audit
        if r.get("type") == "POLARITY"
        and r.get("condition") == "E1-claim"
        and r.get("magnitude") == "flip"
    }
    rows: list[dict] = []
    for c0 in sorted(c0_rows, key=lambda r: (r.get("flip_mechanism") or "", r["base_id"])):
        bid = c0["base_id"]
        e1 = e1_by_base.get(bid)
        if e1 is None:
            raise SystemExit(f"missing E1-claim flip for {bid}")
        rows.append(
            {
                "base_id": bid,
                "flip_mechanism": c0.get("flip_mechanism") or e1.get("flip_mechanism") or "",
                "original_claim": c0["claim"],
                "flipped_claim": e1["claim"],
                "PI_ok": "",
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
