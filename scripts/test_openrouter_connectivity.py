#!/usr/bin/env python3
"""One-shot connectivity test (no secrets printed)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm_client import chat


def main() -> None:
    r = chat(
        model="microsoft/phi-4",
        messages=[{"role": "user", "content": "Say OK"}],
        max_tokens=5,
        temperature=0.0,
        provider=os.environ.get("MEDVERIF_OPENROUTER_PROVIDER") or None,
        allow_fallbacks=False,
    )
    print(json.dumps({
        "ok": True,
        "text": r.text.strip()[:80],
        "model": r.model,
        "provider": r.provider,
        "request_id": r.request_id,
        "tokens": r.total_tokens,
    }))


if __name__ == "__main__":
    main()
