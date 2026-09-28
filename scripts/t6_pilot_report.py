#!/usr/bin/env python3
"""Summarize T6-B pilot spend and parse rates."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw" / "t6b" / "pilot"
OUT = ROOT / "notes" / "t6b_pilot_report.md"


def main() -> None:
    lines = ["# T6-B pilot report", ""]
    total = 0.0
    for path in sorted(RAW.glob("*.jsonl")):
        n = parse = 0
        spend = 0.0
        for line in path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            n += 1
            spend += float(row.get("api_cost_usd") or 0)
            if row.get("verdict") == "PARSE_FAIL":
                parse += 1
        total += spend
        lines.append(f"- **{path.stem}**: n={n}, parse_fail={parse}, spend=${spend:.4f}")
    credit = {}
    cp = ROOT / "notes" / "openrouter_credit.json"
    if cp.is_file():
        credit = json.loads(cp.read_text())
    lines += ["", f"- Pilot total spend: **${total:.4f}**", f"- OR remaining: **{credit.get('limit_remaining', '—')}**", ""]
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
