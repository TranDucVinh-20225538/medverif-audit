"""Non-blocking flock on (verifier, output JSONL path) for all scoring runners."""

from __future__ import annotations

import fcntl
import hashlib
import os
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = ROOT / ".cache" / "score_locks"


def lock_file(verifier: str, out: Path) -> Path:
    out = out.resolve()
    try:
        rel = str(out.relative_to(ROOT))
    except ValueError:
        rel = str(out)
    key = hashlib.sha256(f"{verifier}\0{rel}".encode()).hexdigest()[:32]
    return LOCK_DIR / f"{verifier}__{key}.lock"


@contextmanager
def exclusive_score_lock(verifier: str, out: Path):
    """Yield True if lock acquired; False if another process holds it."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lf = lock_file(verifier, out)
    handle = open(lf, "a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        yield False
        return
    handle.seek(0)
    handle.truncate()
    handle.write(f"pid={os.getpid()}\n")
    handle.flush()
    try:
        yield True
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
