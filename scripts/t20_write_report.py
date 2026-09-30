#!/usr/bin/env python3
"""T20 appendix report from match JSON + PI diff-unit labels."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCH_JSON = ROOT / "notes/t20_match_retrieval.json"
PI_LABELS = ROOT / "qc/t20_diff_unit_labels.csv"
OUT = ROOT / "notes/t20_report.md"


import sys

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from t20_surface_diff import pair_key_from_row  # noqa: E402


def load_pi_unique() -> list[dict]:
    if not PI_LABELS.is_file():
        return []
    rows: list[dict] = []
    seen: set[tuple] = set()
    with PI_LABELS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            k = pair_key_from_row(row)
            if k in seen:
                continue
            seen.add(k)
            rows.append(row)
    return rows


def main() -> None:
    summary = json.loads(MATCH_JSON.read_text())["summary"]
    pi_unique = load_pi_unique()
    pi_y = [r for r in pi_unique if (r.get("same_quantity_same_context") or "").strip().upper() == "Y"]
    cats = Counter(summary.get("unique_diff_categories") or {})
    scale_confirmed = int(summary.get("scale_conversion_confirmed_pi_y") or 0)

    lines = [
        "# T20 appendix — openFDA label vs textbook dose surfaces",
        "",
        "Descriptive check only (not a headline prevalence claim). M1 canonical matching + PI review of unit-surface differences.",
        "",
        "## Cohort",
        "",
        f"- Drugs in list: **{summary['drugs_in_list']}**",
        f"- Cached FDA labels: **{summary['drugs_with_cached_label']}**",
        f"- **Unique** M1-matched dose pairs (deduped by drug + sentences + spans): **{summary['unique_matched_pairs']}** "
        f"(pre-fix matcher counted **363** duplicate cross-product rows)",
        f"- Unique pairs with differing unit surface: **{summary['unique_diff_pairs']}**",
        "",
        "## PI review (`qc/t20_diff_unit_labels.csv`)",
        "",
        f"- Review rows in file: **{summary.get('pi_label_rows', 33)}** (matcher emitted duplicates before dedupe fix)",
        f"- **Unique** surface-difference pairs reviewed: **{len(pi_unique)}**",
        f"- PI **same quantity + same context (Y)**: **{len(pi_y)} / {len(pi_unique)}**",
        f"- Of those Y, **true scale conversion** (mg↔g, µg↔mg style): **{scale_confirmed}** "
        "(valacyclovir 2 g↔2 grams and dexamethasone 1 mg↔1.0 mg are spelling/formatting; "
        "cosyntropin 250 µg↔0.25 mg is scale conversion)",
        "",
        "## Surface-difference categories (unique diff pairs, rule-based)",
        "",
    ]
    for cat in ("scale_conversion", "spelling", "symbol", "formatting", "other"):
        if cats.get(cat):
            lines.append(f"- **{cat}**: {cats[cat]}")
    lines.extend(
        [
            "",
            "## BM25 retrieval simulation",
            "",
            "Prior aggregate **9.4%** query hit rate was on undeduplicated matcher output and is **withdrawn**. "
            "No recomputed rate on PI-confirmed pairs (n=3 contexts).",
            f"- Raw query count (drug×base dose claims): **{summary.get('bm25_queries', '—')}** (diagnostic only)",
            "",
            "Details: `notes/t20_match_retrieval.json` · Review export: `qc/t20_diff_unit_review.csv`",
        ]
    )
    OUT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"report": str(OUT), "pi_unique": len(pi_unique), "pi_y": len(pi_y)}, indent=2))


if __name__ == "__main__":
    main()
