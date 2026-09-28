#!/usr/bin/env python3
"""Mark synthetic T8 INV/E1/C0 instances valid=false (audit retention)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    ROOT / "data/t8/instances_aggrefact_inv.jsonl",
    ROOT / "data/v3/instances_aggrefact_inv.jsonl",
    ROOT / "data/t8/instances_aggrefact_c0.jsonl",
    ROOT / "data/v3/instances_aggrefact_c0.jsonl",
)
REASON = "synthetic_t8_deprecated"


def main() -> None:
    n = 0
    for path in PATHS:
        if not path.is_file():
            continue
        rows = [json.loads(line) for line in path.open() if line.strip()]
        for row in rows:
            row["valid"] = False
            row["invalid_reason"] = REASON
        with path.open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += len(rows)
        print(f"deprecated {len(rows)} → {path}")
    print(json.dumps({"rows_marked_invalid": n, "reason": REASON}))


if __name__ == "__main__":
    main()
