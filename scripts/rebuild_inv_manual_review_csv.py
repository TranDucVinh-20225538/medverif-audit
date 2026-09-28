#!/usr/bin/env python3
"""Rebuild qc/inv_manual_review.csv from instances_g_inv_paraphrase.jsonl."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
sys.path.insert(0, str(ROOT / "src"))

from inv_manual_review_csv import write_manual_review_csv  # noqa: E402

INST = ROOT / "data" / "v3" / "instances_g_inv_paraphrase.jsonl"
OUT = ROOT / "qc" / "inv_manual_review.csv"
C0_MAIN = ROOT / "data" / "v3" / "instances_cpu_main.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    c0 = {r["base_id"]: r["claim"] for r in read_jsonl(C0_MAIN) if r.get("condition") == "C0"}
    accepted = []
    for row in read_jsonl(INST):
        if not row.get("valid"):
            continue
        bid = row["base_id"]
        accepted.append(
            {
                "base_id": bid,
                "type": row["type"],
                "mechanism": "llm",
                "mapping": "",
                "original": c0.get(bid, row.get("claim_c0") or ""),
                "rewrite": row["claim"],
            }
        )
    write_manual_review_csv(OUT, accepted)
    print(json.dumps({"csv": str(OUT), "n": len(accepted)}))


if __name__ == "__main__":
    main()
