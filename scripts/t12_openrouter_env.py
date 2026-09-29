"""OpenRouter as OpenAI-compatible API for T12 upstream frameworks."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def apply_openrouter_openai_env() -> dict:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY required")
    os.environ["OPENAI_API_KEY"] = key
    os.environ["OPENAI_BASE_URL"] = os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE)
    return {"openai_base_url": os.environ["OPENAI_BASE_URL"], "key_set": True}


def log_package_versions() -> dict:
    out: dict = {}
    for mod, attr in (
        ("ragas", "__version__"),
        ("deepeval", "__version__"),
        ("trulens_eval", "__version__"),
    ):
        try:
            m = __import__(mod)
            out[mod] = getattr(m, attr, "?")
        except Exception as exc:
            out[mod] = f"unavailable: {exc}"
    path = ROOT / "notes/t12_package_versions.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    return out
