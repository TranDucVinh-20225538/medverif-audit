#!/usr/bin/env python3
"""Write notes/expand_status.md (~1h report)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--statpearls", default="unknown")
    args = parser.parse_args()
    exp = ROOT / "data" / "expand"
    stats = {}
    if (exp / "extract_stats.json").is_file():
        stats = json.loads((exp / "extract_stats.json").read_text())
    v3 = ROOT / "data" / "v3"
    unit_n = 0
    unit_b = 0
    def read_jsonl(path: Path) -> list:
        rows = []
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    if (v3 / "instances_main.jsonl").is_file():
        rows = read_jsonl(v3 / "instances_main.jsonl")
        unit = [
            r
            for r in rows
            if r.get("valid")
            and r.get("type") == "DOSE"
            and r.get("condition") == "INV-claim"
            and r.get("magnitude") == "unit_conversion"
        ]
        unit_n = len(unit)
        unit_b = len({r["base_id"] for r in unit})

    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        "# Expansion status (expanded set)",
        "",
        f"Updated: {ts}",
        "",
        "## StatPearls",
        f"- Pipeline stage: **{args.statpearls}**",
        f"- Tar: `{ROOT / '.cache/statpearls/statpearls_NBK430685.tar.gz'}`",
        f"- Chunks: `{ROOT / '.cache/statpearls/chunk'}`",
        "",
        "## Candidate counts (unused sentences vs v2)",
        f"- Pool DOSE: **{stats.get('pool_DOSE', '—')}**",
        f"- Pool POLARITY: **{stats.get('pool_POLARITY', '—')}**",
        f"- Selected (cap 400/type): **{stats.get('selected', '—')}**",
        f"- Used v2 sentence keys excluded: {stats.get('used_v2_keys', '—')}",
        "",
        "## Natural INV-unit (all DOSE main, rule-based)",
        f"- Valid unit INV instances: **{unit_n}**",
        f"- Bases with unit INV: **{unit_b}**",
        "",
        "## Review packs",
        "- `qc/expand_pol_flips.csv`",
        "- `qc/expand_dose_sample.csv` (25% DOSE bases, seed 2026)",
        "- `qc/expand_unit_natural.csv`",
        "",
        "## Scoring",
        "- Pending: `data/expand/instances_score_pending.jsonl` (after Stage-1 bases built)",
        "- Budget guard: expansion API spend stop at **$30** (`notes/expand_budget.json`)",
    ]
    out = ROOT / "notes" / "expand_status.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(out)


if __name__ == "__main__":
    main()
