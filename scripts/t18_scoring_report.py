#!/usr/bin/env python3
"""T18 card: value/unit_swap/unit_spell vs medical + T14 unit_spell reference."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import is_pass, read_jsonl  # noqa: E402

INST = ROOT / "data/t18/instances_t18.jsonl"
RAW = ROOT / "results/raw/t18"
OUT = ROOT / "notes/t18_report.md"


def family(row: dict) -> str:
    if row.get("t18_inv_appendix"):
        return "inv_appendix"
    if row.get("t18_family"):
        return str(row["t18_family"])
    mag = row.get("magnitude") or ""
    cond = row.get("condition") or ""
    if mag in ("x2", "div2"):
        return f"value_{mag}"
    if cond == "T18-unit_spell":
        return "unit_spell"
    return cond or mag or "other"


def main() -> None:
    rows = [r for r in read_jsonl(INST) if r.get("valid", True) and not r.get("t18_inv_appendix")]
    by_fam: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_fam[family(r)].append(r)
    score_files = sorted(RAW.glob("*.jsonl")) if RAW.is_dir() else []
    lines = ["# T18 Wikipedia scoring (non-medical)", "", f"- Scoring instances: **{len(rows)}**", ""]
    for sf in score_files:
        scores = {s["instance_id"]: s for s in read_jsonl(sf)}
        slug = sf.stem
        lines.append(f"## {slug}")
        for fam, insts in sorted(by_fam.items()):
            if fam == "inv_appendix":
                continue
            n = len(insts)
            if not n:
                continue
            ok = sum(1 for r in insts if is_pass(scores.get(r["instance_id"], {}), r))
            lines.append(f"- **{fam}**: PASS {ok}/{n} ({100*ok/n:.1f}%)")
        lines.append("")
    lines.append("Compare: `results/tables/t14_c0_conditional_pass.md` (unit_spell).")
    OUT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"report": str(OUT), "families": {k: len(v) for k, v in by_fam.items()}}, indent=2))


if __name__ == "__main__":
    main()
