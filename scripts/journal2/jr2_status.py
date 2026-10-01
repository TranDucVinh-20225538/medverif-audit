#!/usr/bin/env python3
"""Status note for journal chain 2 -> notes/journal_chain2_status.md (markers, row counts, real-dose spend)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr2_common import AT, JR2, MARKERS, RD, RD_CAP_USD, ROOT, rd_spent_usd, read_jsonl  # noqa: E402

NOTE = ROOT / "notes/journal_chain2_status.md"
UNF_CK = ("t6a_minicheck_roberta", "t6a_minicheck_deberta", "t6a_alignscore_base", "v2a_minicheck", "v3_alignscore")


def n(p: Path) -> int:
    return len(read_jsonl(p)) if p.is_file() else 0


def main() -> None:
    md = ["# Journal chain 2 status", "", "Generated %s by `scripts/journal2/jr2_status.py`." % time.strftime("%Y-%m-%d %H:%M %Z"), ""]
    jobs = JR2 / "chain_jobs.json"
    if jobs.is_file():
        md += ["Slurm jobs: `%s`" % jobs.read_text().strip(), ""]
    md += ["## Stage markers", "", "| stage | finished | info |", "|---|---|---|"]
    for m in sorted(MARKERS.glob("*.done")) if MARKERS.is_dir() else []:
        info = json.loads(m.read_text())
        md.append("| %s | %s | %s |" % (m.stem, info.get("finished", ""),
                                       ", ".join("%s=%s" % (k, v) for k, v in info.items() if k not in ("stage", "finished"))[:200]))
    md += ["", "## Real-world dose errors (RD)", "",
           "- questions %d, answers %d, instances %d" % (n(RD / "questions.jsonl"), n(RD / "answers.jsonl"), n(RD / "instances.jsonl")),
           "- scores: " + (", ".join("%s %d" % (p.stem, n(p)) for p in sorted((RD / "scores").glob("*.jsonl"))) or "none"),
           "- real-dose API spend $%.4f of cap $%.2f (chain 1 ledger untouched)" % (rd_spent_usd(), RD_CAP_USD),
           "- report: notes/real_dose_errors.md %s" % ("present" if (ROOT / "notes/real_dose_errors.md").is_file() else "MISSING"),
           "", "## Unit-normalization fix (UNF)", "", "| checker | orig rows | unf rows |", "|---|---|---|"]
    sd = JR2 / "unf" / "scores"
    for ck in UNF_CK:
        md.append("| %s | %d | %d |" % (ck, n(sd / "orig" / (ck + ".jsonl")), n(sd / "unf" / (ck + ".jsonl"))))
    md += ["", "- report: notes/unit_normalization_fix.md %s" % ("present" if (ROOT / "notes/unit_normalization_fix.md").is_file() else "MISSING"),
           "", "## Attribution (AT)", ""]
    for p in sorted(AT.glob("attr_*.jsonl")) if AT.is_dir() else []:
        md.append("- %s: %d items" % (p.name, n(p)))
    md += ["- report: notes/attribution_mechanism.md %s" % ("present" if (ROOT / "notes/attribution_mechanism.md").is_file() else "MISSING"), ""]
    NOTE.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("wrote", NOTE)


if __name__ == "__main__":
    main()
