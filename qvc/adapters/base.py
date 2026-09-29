"""Load normalized verdicts from medverif-style score JSONL."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScoredRowAdapter:
    instance_id: str
    verdict: str
    score: float | None = None
    api_model: str | None = None


def verdicts_from_jsonl(path: str | Path) -> dict[str, str]:
    out: dict[str, str] = {}
    p = Path(path)
    if not p.is_file():
        return out
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        v = row.get("verdict")
        if v and v != "PARSE_FAIL":
            out[row["instance_id"]] = v
    return out
