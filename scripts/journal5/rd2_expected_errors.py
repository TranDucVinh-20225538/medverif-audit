#!/usr/bin/env python3
"""(RD2-1b) Expected number of natural errors in RD2 -- an ESTIMATE from RD error rates per dosing stratum (CPU, no API).

RD questions are tagged with the SAME pre-registered tagger as RD2 (rd2_questions.tag_question), joined with RD's
auto-classification (results/journal2/real_dose/extract_rows.jsonl) and the AI pre-check of the 47 auto unit-type rows
(qc/ai_precheck_real_dose_unit_errors.csv; AI-assisted, NOT human-verified).  Per stratum and answer condition:
  auto unit-type rate  = (unit_error + basis_error) / answers
  AI-true rate         = precheck true_unit_error / answers
  value-error rate     = value_error / answers
Expected RD2 counts = sum over strata of rate(stratum, condition) x RD2 questions(stratum) x generators.  Strata with
< 20 RD answers per condition borrow the pooled error-prone rate.  RD's two generators were API models (GPT-4o-mini,
Gemma-3-27B); open 7-32B models may err more or less, so treat the numbers as an order of magnitude.
Output: notes/rd2_expected_errors.json + .md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import QUESTIONS, RD1, RD1_LABELS, ROOT, STRATA, read_jsonl, write_jsonl  # noqa: E402,F401
from rd2_questions import tag_question  # noqa: E402

PRE = ROOT / "qc" / "ai_precheck_real_dose_unit_errors.csv"
OUT = ROOT / "notes" / "rd2_expected_errors"
MIN_N = 20


def wilson(k: int, n: int, z: float = 1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generators", type=int, default=6, help="number of RD2 generators (default 4 local + 2 OpenRouter)")
    ap.add_argument("--conditions", default="grounded,closed")
    args = ap.parse_args()
    labs = {l["drug"]: re.sub(r"\s+", " ", l["dosage_and_administration"]).strip() for l in read_jsonl(RD1_LABELS)}
    rdq = {q["qid"]: q for q in read_jsonl(RD1 / "questions.jsonl")}
    tags = {qid: tag_question(q, labs[q["drug"]]) for qid, q in rdq.items()}
    with PRE.open(encoding="utf-8-sig") as fh:
        pre = {r["instance_id"]: r["ai_label"] for r in csv.DictReader(l for l in fh if not l.startswith("#"))}
    cell = defaultdict(Counter)  # (stratum, cond) -> counts
    for r in read_jsonl(RD1 / "extract_rows.jsonl"):
        st = tags[r["qid"]]["stratum"]
        for s in (st, "ALL", "ERROR_PRONE" if st != "fixed" else "FIXED"):
            c = cell[(s, r["condition"])]
            c["answers"] += 1
            c[r["auto_class"]] += 1
            c["auto_unit_type"] += r["auto_class"] in ("unit_error", "basis_error")
            c["ai_true"] += pre.get(r["instance_id"]) == "true_unit_error"
    rd_q_by_stratum = Counter(t["stratum"] for t in tags.values())
    rd2 = read_jsonl(QUESTIONS)
    rd2_by = Counter(q["stratum"] for q in rd2)
    conds = [c for c in args.conditions.split(",") if c]
    est = {"auto_unit_type": 0.0, "ai_true": 0.0, "value_error": 0.0}
    lo = dict.fromkeys(est, 0.0)
    hi = dict.fromkeys(est, 0.0)
    per = {}
    for st in list(STRATA) + ["fixed"]:
        per[st] = {"rd2_questions": rd2_by.get(st, 0), "rd_questions": rd_q_by_stratum.get(st, 0)}
        for cond in conds:
            c = cell[(st, cond)]
            src = st
            if c["answers"] < MIN_N:
                src = "ERROR_PRONE" if st != "fixed" else "FIXED"
                c = cell[(src, cond)]
            n = rd2_by.get(st, 0) * args.generators
            rates = {k: (c[k] / c["answers"]) if c["answers"] else 0.0 for k in est}
            per[st][cond] = {"rd_answers": cell[(st, cond)]["answers"], "rate_source": src,
                             "rd_rates": {k: round(v, 4) for k, v in rates.items()},
                             "rd_counts": {k: cell[(st, cond)][k] for k in est},
                             "rd2_answers": n, "expected": {k: round(v * n, 1) for k, v in rates.items()}}
            for k in est:
                est[k] += rates[k] * n
                w = wilson(c[k], c["answers"])
                lo[k] += w[0] * n
                hi[k] += w[1] * n
    pooled = {cond: {k: cell[("ALL", cond)][k] for k in ("answers", "auto_unit_type", "ai_true", "value_error")} for cond in conds}
    res = {"generators": args.generators, "conditions": conds, "rd2_questions": len(rd2),
           "rd2_answers": len(rd2) * args.generators * len(conds),
           "expected_total": {k: round(v, 1) for k, v in est.items()},
           "expected_total_range_from_per_cell_wilson95": {k: [round(lo[k], 1), round(hi[k], 1)] for k in est},
           "rd_pooled": pooled, "per_stratum": per,
           "rd_stratum_counts": dict(rd_q_by_stratum),
           "note": "ESTIMATE ONLY: RD rates (2 API generators; AI pre-check not human-verified) x RD2 composition."}
    OUT.with_suffix(".json").write_text(json.dumps(res, indent=1) + "\n")
    lines = ["# RD2 expected natural errors (ESTIMATE, not a result)", "",
             "RD error rates per pre-registered dosing stratum (same tagger) x RD2 questions per stratum x %d generators x "
             "%d conditions = %d answers.  `auto unit-type` = rd_extract unit_error+basis_error; `AI-true` = AI pre-check "
             "true_unit_error (AI-assisted, not human-verified; 12/47 in RD).  Strata with < %d RD answers per condition use "
             "the pooled error-prone (or fixed) rate." % (args.generators, len(conds), res["rd2_answers"], MIN_N), "",
             "| stratum | RD q | RD2 q | cond | RD answers | RD auto unit-type | RD AI-true | RD value err | exp. auto unit-type | exp. AI-true | exp. value err |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for st, d in per.items():
        for cond in conds:
            x = d[cond]
            own = x["rate_source"] == st
            pc = lambda k: (" (%.1f%%)" % (100 * x["rd_rates"][k])) if own else ""  # noqa: E731
            lines.append("| %s | %d | %d | %s | %d | %d%s | %d%s | %d%s | %.1f | %.1f | %.1f |%s" % (
                st, d["rd_questions"], d["rd2_questions"], cond, x["rd_answers"], x["rd_counts"]["auto_unit_type"],
                pc("auto_unit_type"), x["rd_counts"]["ai_true"], pc("ai_true"), x["rd_counts"]["value_error"], pc("value_error"),
                x["expected"]["auto_unit_type"], x["expected"]["ai_true"], x["expected"]["value_error"],
                "" if own else " rate borrowed from pooled %s" % x["rate_source"]))
    rg = res["expected_total_range_from_per_cell_wilson95"]
    lines += ["", "**Expected totals (estimate):** auto-flagged unit/basis errors ≈ %.0f (range %.0f-%.0f), AI-pre-check-true "
              "unit/basis errors ≈ %.0f (range %.0f-%.0f), value errors ≈ %.0f (range %.0f-%.0f); RD had 47 / 12 / 93 in 1456 "
              "answers.  Ranges = sums of per-cell Wilson 95%% bounds (not a joint interval).  Caveats: RD's BSA cells are "
              "4/6 parser artifacts (`mg/m 2`), which RD2 repairs in the label text, so the auto unit-type estimate for BSA is "
              "inflated; RD's generators were API models; the AI pre-check is not human-verified." % (
                  est["auto_unit_type"], rg["auto_unit_type"][0], rg["auto_unit_type"][1], est["ai_true"], rg["ai_true"][0],
                  rg["ai_true"][1], est["value_error"], rg["value_error"][0], rg["value_error"][1]), ""]
    OUT.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: res[k] for k in ("rd2_questions", "rd2_answers", "expected_total",
                                          "expected_total_range_from_per_cell_wilson95", "rd_stratum_counts")}, indent=1))


if __name__ == "__main__":
    main()
