#!/usr/bin/env python3
"""Keep first row per instance_id in JSONL outputs (in-place with .bak)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def dedupe(path: Path) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    kept: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            kept.append(line)
            continue
        iid = row.get("instance_id")
        if iid is None:
            kept.append(line)
            continue
        key = str(iid)
        if key in seen:
            continue
        seen.add(key)
        kept.append(line)
    before = len([ln for ln in lines if ln.strip()])
    after = len(kept)
    if after != before:
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            bak.write_text("\n".join(lines) + ("\n" if lines and lines[-1].endswith("\n") else ""), encoding="utf-8")
        path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return before, after


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", type=Path, help="JSONL files (default: results/raw/*.jsonl)")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = args.paths or sorted((root / "results" / "raw").glob("*.jsonl"))
    paths += sorted((root / "results" / "raw_threshold").glob("*.jsonl")) if not args.paths else []
    for p in paths:
        if not p.is_file():
            continue
        before, after = dedupe(p)
        print(json.dumps({"file": str(p), "before": before, "after": after, "removed": before - after}))


if __name__ == "__main__":
    main()
