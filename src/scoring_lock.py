"""Non-blocking flock on (verifier, output JSONL path) for all scoring runners."""

from __future__ import annotations

import fcntl
import hashlib
import os
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = ROOT / ".cache" / "score_locks"
# node30: shared GPU scoring lock (keep both paths when merging branches)
GPU_GLOBAL_LOCK = ROOT / "jobs" / "locks" / "gpu0_scoring.lock"


def lock_file(verifier: str, out: Path) -> Path:
    out = out.resolve()
    try:
        rel = str(out.relative_to(ROOT))
    except ValueError:
        rel = str(out)
    key = hashlib.sha256(f"{verifier}\0{rel}".encode()).hexdigest()[:32]
    return LOCK_DIR / f"{verifier}__{key}.lock"


@contextmanager
def _flock_path(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+")
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


@contextmanager
def exclusive_score_lock(verifier: str, out: Path):
    """Yield True if lock acquired; False if another process holds it.

    HPC: per-(verifier,out) lock under `.cache/score_locks/`.
    node30: optional global `jobs/locks/gpu0_scoring.lock` (both held when present).
    """
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lf = lock_file(verifier, out)
    use_global = os.environ.get("MEDVERIF_GPU_GLOBAL_SCORE_LOCK", "1").lower() not in (
        "0",
        "false",
        "no",
    )
    global_handle = None
    if use_global:
        with _flock_path(GPU_GLOBAL_LOCK) as global_ok:
            if not global_ok:
                yield False
                return
            with _flock_path(lf) as local_ok:
                yield local_ok
        return
    with _flock_path(lf) as local_ok:
        yield local_ok
