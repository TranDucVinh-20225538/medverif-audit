"""Safe JSONL writes: backup, atomic replace, shrink guard for tracked data/scores."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE_PATH = ROOT / "notes" / "allow_data_shrink.json"
GUARD_PREFIXES = ("data/", "results/raw/")


def _line_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    n = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            n += chunk.count(b"\n")
    return n


def shrink_allowed(rel: str) -> bool:
    if not OVERRIDE_PATH.exists():
        return False
    try:
        data = json.loads(OVERRIDE_PATH.read_text())
    except json.JSONDecodeError:
        return False
    allowed = data.get("paths") or data.get("allow") or []
    return rel in allowed or data.get("allow_all") is True


def backup_file(path: Path) -> Path | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    ts = time.strftime("%Y%m%dT%H%M%S")
    dest = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, dest)
    return dest


def write_jsonl_atomic(
    path: Path,
    rows: list[dict],
    *,
    allow_shrink: bool | None = None,
) -> dict:
    """Write rows via temp file + os.replace; optional shrink guard vs existing file."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        rel = str(path.relative_to(ROOT))
    except ValueError:
        rel = str(path)

    old_n = _line_count(path)
    new_n = len(rows)
    guard = rel.replace("\\", "/").startswith(GUARD_PREFIXES)
    if allow_shrink is None:
        allow_shrink = shrink_allowed(rel)

    if guard and old_n > 0 and new_n < old_n and not allow_shrink:
        raise RuntimeError(
            f"refusing to shrink {rel}: {old_n} -> {new_n} lines "
            f"(add path to {OVERRIDE_PATH.relative_to(ROOT)} or pass allow_shrink=True)"
        )

    bak = backup_file(path) if old_n > 0 else None
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with tmp.open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)

    return {"path": rel, "old_lines": old_n, "new_lines": new_n, "backup": str(bak) if bak else None}
