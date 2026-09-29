#!/usr/bin/env python3
"""Block commit/push when tracked data/ or results/raw/ JSONL shrinks vs HEAD."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = ROOT / "notes" / "allow_data_shrink.json"
PREFIXES = ("data/", "results/raw/")


def line_count_bytes(blob: bytes) -> int:
    if not blob:
        return 0
    return blob.count(b"\n")


def line_count_file(path: Path) -> int:
    if not path.exists():
        return 0
    return line_count_bytes(path.read_bytes())


def allowed(rel: str) -> bool:
    if not OVERRIDE.exists():
        return False
    try:
        data = json.loads(OVERRIDE.read_text())
    except json.JSONDecodeError:
        return False
    paths = set(data.get("paths") or data.get("allow") or [])
    return rel in paths or data.get("allow_all") is True


def staged_jsonl() -> list[str]:
    out = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True)
    paths = [p.strip() for p in out.splitlines() if p.strip().endswith(".jsonl")]
    return [p for p in paths if p.startswith(PREFIXES)]


def head_bytes(rel: str) -> bytes | None:
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=ROOT, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre-commit"
    paths = staged_jsonl()
    if mode == "pre-push":
        # All tracked jsonl under data/ and results/raw/ that differ from upstream
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD", "@{upstream}"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        paths = [
            p.strip()
            for p in out.splitlines()
            if p.strip().endswith(".jsonl") and p.strip().startswith(PREFIXES)
        ]
    if not paths:
        return 0

    bad: list[str] = []
    for rel in paths:
        if allowed(rel):
            continue
        new_n = line_count_file(ROOT / rel)
        old_b = head_bytes(rel)
        old_n = line_count_bytes(old_b) if old_b is not None else None
        if old_n is not None and new_n < old_n:
            bad.append(f"{rel}: {old_n} -> {new_n} lines")

    if bad:
        print("DATA INTEGRITY: refusing shrink without notes/allow_data_shrink.json", file=sys.stderr)
        for line in bad:
            print(f"  {line}", file=sys.stderr)
        print(f"Override: add path to {OVERRIDE.relative_to(ROOT)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
