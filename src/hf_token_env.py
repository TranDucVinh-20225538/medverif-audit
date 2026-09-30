"""Sanitize Hugging Face hub tokens in the environment (strip whitespace/newlines)."""

from __future__ import annotations

import os

_HF_KEYS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HF_HUB_TOKEN")


def sanitize_hf_token_env() -> None:
    for key in _HF_KEYS:
        val = os.environ.get(key)
        if val is not None and val != (clean := str(val).strip()):
            os.environ[key] = clean
    token_path = os.path.expanduser("~/.cache/huggingface/token")
    if os.path.isfile(token_path):
        raw = open(token_path, encoding="utf-8").read()
        clean = raw.strip()
        if clean and clean != raw:
            with open(token_path, "w", encoding="utf-8") as handle:
                handle.write(clean + "\n")
        if clean:
            os.environ.setdefault("HF_TOKEN", clean)
            os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", clean)
