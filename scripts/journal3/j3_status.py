#!/usr/bin/env python3
"""Chain-3 status note (CPU): markers, score-file coverage, model download status -> notes/journal3_chain_status.md."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from j3_common import FT_SCORES, J3, JUDGE_SCORES, MARKERS, NOTES, done_ids, pack_rows  # noqa: E402
from j3_models import FT, FT_PACKS, JUDGE_PACKS, JUDGES, ft_name  # noqa: E402


def main() -> None:
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M UTC+7")
    jobs = json.loads((J3 / "chain_jobs.json").read_text()) if (J3 / "chain_jobs.json").is_file() else {}
    models = json.loads((J3 / "models.json").read_text()) if (J3 / "models.json").is_file() else {}
    L = ["# Journal chain 3 — status", "", "Generated %s. Slurm jobs: %s" % (now, json.dumps(jobs) if jobs else "n/a"), "",
         "## FT scoring (rows scored / expected)", "", "| run | marker | " + " | ".join("%s_%s" % pv for pv in FT_PACKS) + " |",
         "|" + "---|" * (2 + len(FT_PACKS))]
    exp = {pv: len(pack_rows(*pv)) for pv in FT_PACKS}
    for m, t in FT:
        n = ft_name(m, t)
        mk = MARKERS / ("J3_FT_%s.done" % n)
        L.append("| %s | %s | %s |" % (n, ("skipped" if mk.is_file() and "skipped" in mk.read_text() else "done") if mk.is_file() else "-",
                                       " | ".join("%d/%d" % (len(done_ids(FT_SCORES / ("%s__%s_%s.jsonl" % (n, p, v)))), exp[(p, v)]) for p, v in FT_PACKS)))
    L += ["", "## LLM judges", "", "| slug | HF id | download | marker | " + " | ".join(JUDGE_PACKS) + " |", "|" + "---|" * (4 + len(JUDGE_PACKS))]
    jexp = {p: len(pack_rows(p)) for p in JUDGE_PACKS}
    for s, hf, *_ in JUDGES:
        mk = MARKERS / ("J3_JG_%s.done" % s)
        mtxt = mk.read_text() if mk.is_file() else ""
        mrec = models.get(s) or {}
        L.append("| %s | %s | %s | %s | %s |" % (s, hf, mrec.get("status", "-") + ((" (" + mrec.get("reason", "")[:120] + ")") if mrec.get("reason") else ""),
                                                ("skipped" if "skipped" in mtxt else "done") if mtxt else "-",
                                                " | ".join("%d/%d" % (len(done_ids(JUDGE_SCORES / ("%s__%s.jsonl" % (s, p)))), jexp[p]) for p in JUDGE_PACKS)))
    L += ["", "Rerun a failed task: `sbatch --array=<i> jobs/journal3/jr3_FT.sbatch` or `jobs/journal3/jr3_JG.sbatch` (resumes by "
          "instance_id), then `sbatch jobs/journal3/jr3_final.sbatch`. `MEDVERIF_J3_FORCE=<stage>|all` ignores a marker."]
    out = NOTES / "journal3_chain_status.md"
    out.write_text("\n".join(L) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
