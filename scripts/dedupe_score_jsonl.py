#!/usr/bin/env python3
"""Backup then dedupe score JSONL by instance_id (keep last row)."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--verifier", default="", help="label for report only")
    args = p.parse_args()
    path = args.path.resolve()
    if not path.exists():
        print(json.dumps({"error": "missing", "path": str(path)}))
        return
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, backup)
    order: list[str] = []
    by_id: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        iid = row.get("instance_id")
        if not iid:
            continue
        if iid not in by_id:
            order.append(iid)
        by_id[iid] = row
    dupes = sum(1 for _ in path.read_text().splitlines()) - len(by_id)
    with path.open("w") as handle:
        for iid in order:
            handle.write(json.dumps(by_id[iid], ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "path": str(path),
                "verifier": args.verifier,
                "backup": str(backup),
                "unique": len(by_id),
                "duplicates_removed": max(0, dupes),
            }
        )
    )


if __name__ == "__main__":
    main()
