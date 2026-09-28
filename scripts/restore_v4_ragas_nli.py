#!/usr/bin/env python3
"""Restore v4_ragas_nli.jsonl from git history + overlay newer rows (latest instance_id wins)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from raw_jsonl_backup import backup_raw  # noqa: E402

OUT = ROOT / "results" / "raw" / "v4_ragas_nli.jsonl"
GIT_PATH = "results/raw/v4_ragas_nli.jsonl"


def git_commits() -> list[str]:
    out = subprocess.check_output(
        ["/usr/bin/git", "log", "--format=%H", "--", GIT_PATH],
        cwd=ROOT,
        text=True,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def load_git(commit: str) -> dict[str, dict]:
    try:
        data = subprocess.check_output(
            ["/usr/bin/git", "show", f"{commit}:{GIT_PATH}"], cwd=ROOT
        )
    except subprocess.CalledProcessError:
        return {}
    by: dict[str, dict] = {}
    for line in data.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        by[row["instance_id"]] = row
    return by


def load_file(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    by: dict[str, dict] = {}
    for line in path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        by[row["instance_id"]] = row
    return by


def main() -> None:
    commits = git_commits()
    best_commit = None
    best_n = -1
    for c in commits:
        n = len(load_git(c))
        if n > best_n:
            best_n = n
            best_commit = c
    merged: dict[str, dict] = {}
    # oldest → newest so later commits override
    for c in reversed(commits):
        merged.update(load_git(c))
    merged.update(load_file(OUT))
    if OUT.is_file():
        backup_raw(OUT)
    with OUT.open("w") as handle:
        for row in merged.values():
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "best_commit": best_commit[:8] if best_commit else None,
                "best_commit_unique_ids": best_n,
                "merged_unique_ids": len(merged),
                "out": str(OUT.relative_to(ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
