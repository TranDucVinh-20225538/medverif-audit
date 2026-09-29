#!/usr/bin/env python3
"""Remove instance_ids from a score JSONL (backup first)."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--ids-file", type=Path, required=True, help="One instance_id per line")
    args = p.parse_args()
    drop = {line.strip() for line in args.ids_file.read_text().splitlines() if line.strip()}
    path = args.path.resolve()
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, backup)
    kept = []
    removed = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("instance_id") in drop:
            removed += 1
            continue
        kept.append(line)
    path.write_text("\n".join(kept) + ("\n" if kept else ""))
    print(json.dumps({"path": str(path), "backup": str(backup), "removed": removed, "kept": len(kept)}))


if __name__ == "__main__":
    main()
