"""Shared JSONL helpers for verifier runs. Resume by instance id."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    found = set()
    for row in read_jsonl(path):
        if "instance_id" in row:
            found.add(row["instance_id"])
    return found


def append_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
