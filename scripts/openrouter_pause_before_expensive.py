#!/usr/bin/env python3
"""Exit 0 if OK to run expensive OR verifiers; exit 3 to pause (balance below floor)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def balance_usd() -> float | None:
    manual = ROOT / "notes/openrouter_wallet_manual.json"
    if manual.is_file():
        try:
            return float(json.loads(manual.read_text()).get("balance_usd"))
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    env = os.environ.get("MEDVERIF_OR_BALANCE_USD", "").strip()
    if env:
        return float(env)
    from openrouter_budget import fetch_credit

    info = fetch_credit()
    rem = info.get("limit_remaining")
    return float(rem) if rem is not None else None


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--min-usd", type=float, default=3.0)
    args = p.parse_args()
    bal = balance_usd()
    if bal is None:
        print(json.dumps({"pause": False, "reason": "balance_unknown"}))
        return
    if bal < args.min_usd:
        print(
            json.dumps(
                {
                    "pause": True,
                    "balance_usd": bal,
                    "min_usd": args.min_usd,
                    "message": "Pause before v5/v6; set notes/openrouter_wallet_manual.json or MEDVERIF_OR_BALANCE_USD",
                },
                indent=2,
            )
        )
        raise SystemExit(3)
    print(json.dumps({"pause": False, "balance_usd": bal, "min_usd": args.min_usd}, indent=2))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    main()
