"""Register vLLM engines for SIGTERM/SIGUSR1 shutdown (SLURM --signal=B:USR1@300)."""

from __future__ import annotations

import multiprocessing
import os
import signal
import sys

_engines: list[object] = []
_installed = False


def _shutdown_engine(llm: object) -> None:
    try:
        if hasattr(llm, "llm_engine") and getattr(llm, "llm_engine", None) is not None:
            llm.llm_engine.shutdown()
        elif hasattr(llm, "shutdown"):
            llm.shutdown()
    except Exception as exc:
        print(f"vllm_graceful: engine shutdown error {exc!r}", flush=True)


def shutdown_all() -> None:
    while _engines:
        llm = _engines.pop()
        _shutdown_engine(llm)
    for child in multiprocessing.active_children():
        child.terminate()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def register(llm: object) -> object:
    if llm not in _engines:
        _engines.append(llm)
    return llm


def _handler(signum: int, _frame) -> None:
    print(f"vllm_graceful: caught signal {signum}", flush=True)
    shutdown_all()
    sys.exit(128 + signum)


def install() -> None:
    global _installed
    if _installed or os.environ.get("MEDVERIF_VLLM_GRACEFUL", "1") == "0":
        return
    signal.signal(signal.SIGTERM, _handler)
    signal.signal(signal.SIGUSR1, _handler)
    _installed = True


install()
