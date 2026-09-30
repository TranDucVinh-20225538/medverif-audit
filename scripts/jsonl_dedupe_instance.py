#!/usr/bin/env python3
"""Keep last row per instance_id (in-place backup to .bak)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def dedupe(path: Path) -> tuple[int, int]:
    rows_by_id: dict[str, dict] = {}
    order: list[str] = []
    for line in path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        iid = row["instance_id"]
        if iid not in rows_by_id:
            order.append(iid)
        rows_by_id[iid] = row
    before = sum(1 for _ in path.open() if _.strip())
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.is_file():
        bak.write_bytes(path.read_bytes())
    with path.open("w") as handle:
        for iid in order:
            handle.write(json.dumps(rows_by_id[iid], ensure_ascii=False) + "\n")
    return before, len(order)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    for p in args.paths:
        b, a = dedupe(p)
        print(f"{p}: {b} -> {a} unique")


if __name__ == "__main__":
    main()
