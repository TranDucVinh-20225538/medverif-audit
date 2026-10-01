#!/usr/bin/env python3
"""Write notes/journal_chain_status.md: which stages finished (markers), spend vs cap, job ids, outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import CAP_USD, JR, MARKERS, NOTES, spent_usd  # noqa: E402

EXPECTED = ["A_threshold", "B1_questions", "B2_retrieve", "B3a_generate", "B3b_instances", "B4_judges", "B4_small",
            "B4_bespoke", "C1_ft_data"] + ["C2_train_%s_r%s" % (m, r) for m in ("alignscore_large", "minicheck_ft5")
                                            for r in ("0.5", "1", "2")] + \
           ["C3_eval_%s_%s" % (m, t) for m in ("alignscore_large", "minicheck_ft5") for t in ("base", "r0.5", "r1", "r2")]


def main() -> None:
    jobs = JR / "chain_jobs.json"
    md = ["# Journal chain status", "", "API spend (sum of api_cost_usd under results/journal): **$%.4f** of $%.2f cap" % (spent_usd(), CAP_USD), ""]
    if jobs.is_file():
        md += ["Slurm jobs: `%s`" % json.dumps(json.loads(jobs.read_text())), ""]
    md += ["| stage | status | info |", "|---|---|---|"]
    for s in EXPECTED:
        p = MARKERS / (s + ".done")
        if p.is_file():
            info = json.loads(p.read_text())
            short = {k: v for k, v in info.items() if k not in ("stage",)}
            st = "skipped" if "skipped" in info else "done"
            md.append("| %s | %s | `%s` |" % (s, st, json.dumps(short, default=str)[:300]))
        else:
            md.append("| %s | **missing** | rerun the stage's sbatch (resumable) |" % s)
    md += ["", "Reports: `notes/threshold_robustness.md`, `notes/journal_rag_expansion.md`, `notes/journal_second_finetune.md`; "
           "human check: `qc/jr_rag_human_check.csv`."]
    (NOTES / "journal_chain_status.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
