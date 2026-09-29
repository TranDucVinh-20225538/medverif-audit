#!/usr/bin/env python3
"""OpenRouter credit check; stop on 402 or balance below floor."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY_URL = "https://openrouter.ai/api/v1/auth/key"
NOTES = ROOT / "notes" / "openrouter_credit.json"


class BudgetStop(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return key


def fetch_credit() -> dict:
    req = urllib.request.Request(
        KEY_URL,
        headers={"Authorization": f"Bearer {_api_key()}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data") or payload
    limit = data.get("limit")
    usage = data.get("usage")
    remaining = None
    if limit is not None and usage is not None:
        try:
            remaining = float(limit) - float(usage)
        except (TypeError, ValueError):
            remaining = None
    if remaining is None and data.get("limit_remaining") is not None:
        remaining = float(data["limit_remaining"])
    out = {
        "limit": limit,
        "usage": usage,
        "limit_remaining": remaining,
        "label": data.get("label"),
        "is_free_tier": data.get("is_free_tier"),
        "raw_keys": sorted(data.keys()),
    }
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    NOTES.write_text(json.dumps(out, indent=2) + "\n")
    return out


def min_credit_floor() -> float:
    return float(os.environ.get("MEDVERIF_OR_MIN_CREDIT", "2"))


def assert_credit_ok() -> dict:
    info = fetch_credit()
    rem = info.get("limit_remaining")
    floor = min_credit_floor()
    if rem is not None and rem < floor:
        raise BudgetStop(f"OpenRouter credit {rem:.4f} below floor ${floor}")
    return info


def check_http_budget(exc: urllib.error.HTTPError) -> None:
    if exc.code == 402:
        raise BudgetStop("OpenRouter HTTP 402 (payment required)") from exc


if __name__ == "__main__":
    print(json.dumps(assert_credit_ok(), indent=2))
