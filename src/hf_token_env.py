"""Sanitize Hugging Face hub tokens in the environment (strip whitespace/newlines)."""

from __future__ import annotations

import os

_HF_KEYS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HF_HUB_TOKEN")


def sanitize_hf_token_env() -> None:
    for key in _HF_KEYS:
        val = os.environ.get(key)
        if val is not None and val != (clean := str(val).strip()):
            os.environ[key] = clean
