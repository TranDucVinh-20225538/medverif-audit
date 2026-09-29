#!/usr/bin/env python3
"""Extract main_pol (80) rows for T19 3B resume scoring."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/t19/instances_t19.jsonl"
OUT = ROOT / "data/t19/instances_t19_main_pol.jsonl"


def main() -> None:
    rows = []
    for line in SRC.open():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("t19_pack") == "main_pol":
            rows.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for r in rows:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"out": str(OUT), "n": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
