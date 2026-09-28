#!/usr/bin/env python3
"""OpenRouter account balance: GET /api/v1/credits (total_credits - total_usage)."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://openrouter.ai/api/v1/credits"
OUT = ROOT / "notes" / "openrouter_account.json"


def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return key


def fetch_account_credits() -> dict:
    req = urllib.request.Request(
        URL,
        headers={"Authorization": f"Bearer {_api_key()}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data") or payload
    total = data.get("total_credits")
    usage = data.get("total_usage")
    balance = None
    if total is not None and usage is not None:
        balance = float(total) - float(usage)
    out = {
        "total_credits": total,
        "total_usage": usage,
        "account_balance_usd": balance,
        "raw_keys": sorted(data.keys()) if isinstance(data, dict) else [],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    return out


def main() -> None:
    info = fetch_account_credits()
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
