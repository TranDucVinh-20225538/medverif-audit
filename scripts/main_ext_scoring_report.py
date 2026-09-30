#!/usr/bin/env python3
"""main_ext card: analysis uses valid rows only (380 scored → 356 evaluable)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import is_pass, read_jsonl  # noqa: E402

INST = ROOT / "data/main_ext/instances_main_ext.jsonl"
RAW = ROOT / "results/raw/main_ext"
OUT = ROOT / "notes/main_ext_scoring_report.md"


def main() -> None:
    rows = [r for r in read_jsonl(INST) if r.get("valid", True)]
    n_scored_file = sum(1 for _ in INST.open())
    lines = [
        "# main_ext scoring (analysis cohort)",
        "",
        f"- Rows in jsonl: **{n_scored_file}**",
        f"- **Valid for analysis: {len(rows)}** (retro span guard; no rescore)",
        "",
    ]
    for sf in sorted(RAW.glob("*.jsonl")):
        scores = {s["instance_id"]: s for s in read_jsonl(sf)}
        ok = sum(1 for r in rows if is_pass(scores.get(r["instance_id"], {}), r))
        have = sum(1 for r in rows if r["instance_id"] in scores)
        lines.append(f"- **{sf.stem}**: PASS {ok}/{have} scored of {len(rows)} valid")
    OUT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"report": str(OUT), "valid": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
