"""Non-blocking flock on (verifier, output JSONL path) for all scoring runners."""

from __future__ import annotations

import fcntl
import hashlib
import os
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = ROOT / ".cache" / "score_locks"
# Legacy single-GPU lock (only when MEDVERIF_GPU_GLOBAL_SCORE_LOCK=legacy)
GPU_GLOBAL_LOCK = ROOT / "jobs" / "locks" / "gpu0_scoring.lock"


def pack_slug_from_out(out: Path) -> str:
    out = out.resolve()
    try:
        rel = out.relative_to(ROOT / "results" / "raw")
        return rel.parts[0] if rel.parts else "root"
    except ValueError:
        return "external"


def score_global_lock_path(verifier: str, out: Path) -> Path:
    """One concurrent scorer per (verifier, pack), not one lock per verifier."""
    pack = pack_slug_from_out(out)
    key = f"{verifier}__{pack}".replace("/", "_")
    return ROOT / "jobs" / "locks" / f"score_{key}.lock"


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
    mode = os.environ.get("MEDVERIF_GPU_GLOBAL_SCORE_LOCK", "pack").lower()
    if mode in ("0", "false", "no", "off"):
        with _flock_path(lf) as local_ok:
            yield local_ok
        return
    if mode in ("1", "true", "yes", "legacy"):
        with _flock_path(GPU_GLOBAL_LOCK) as global_ok:
            if not global_ok:
                yield False
                return
            with _flock_path(lf) as local_ok:
                yield local_ok
        return
    # default "pack": per (verifier, results/raw/{pack}) — parallel packs OK
    glp = score_global_lock_path(verifier, out)
    with _flock_path(glp) as global_ok:
        if not global_ok:
            yield False
            return
        with _flock_path(lf) as local_ok:
            yield local_ok
