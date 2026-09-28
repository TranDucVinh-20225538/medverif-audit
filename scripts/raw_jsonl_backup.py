"""Backup raw JSONL before destructive rewrites."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "results" / "raw" / "_backup"


def backup_raw(scores_path: Path) -> Path | None:
    """Copy scores_path to results/raw/_backup/<stem>.<UTC-timestamp>.jsonl."""
    scores_path = scores_path.resolve()
    if not scores_path.is_file():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = BACKUP_DIR / f"{scores_path.stem}.{ts}.jsonl"
    shutil.copy2(scores_path, dest)
    return dest
