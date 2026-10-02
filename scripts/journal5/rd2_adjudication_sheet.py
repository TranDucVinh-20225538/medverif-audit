#!/usr/bin/env python3
"""(RD2-6) Blind pharmacist adjudication sheet for RD2 (the pre-registered REFERENCE STANDARD).

Adjudication set (pre-registered, built BEFORE any checker/judge verdict is looked at; uses only the deterministic
extractor and the frozen basis check, never checker scores):
  A  every answer the RD extractor auto-classifies as unit_error, basis_error, value_error, time_ambiguous or
     unverifiable (rd_extract QC policy, as in RD's qc/real_dose_errors_check.csv);
  B  every answer flagged by the frozen basis check (full variant, fdb95de);
  C  seeded random controls (seed 20261002): max(150, 10%) of the remaining answers (auto correct /
     match_other_context and not flagged) -- lets missed errors and false alarms be estimated.
Rows are shuffled; the sheet shows NO auto class, NO basis-check flag, NO selection source and NO checker verdict.
The key (check_id -> sources, auto class, basis flag) goes to a separate file that the adjudicator must not open.

Outputs (results/journal5/rd2/qc/): rd2_adjudication_sheet.csv (for the pharmacist), rd2_adjudication_key.csv (analysis)
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import QUESTIONS, RD2, RD2_DIR, SEED, log, read_jsonl  # noqa: E402

QC = RD2_DIR / "qc"
A_CLASSES = ("unit_error", "basis_error", "value_error", "time_ambiguous", "unverifiable")
HUMAN_COLS = ["human_answer_dose_is_error (Y/N/unclear)",
              "human_error_type (unit/basis/value/time/other_population_or_indication/none)",
              "human_correct_dose_for_slot", "note", "adjudicator_initials"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls-min", type=int, default=150)
    ap.add_argument("--controls-frac", type=float, default=0.10)
    args = ap.parse_args()
    rows = {r["instance_id"]: r for r in read_jsonl(RD2 / "extract_rows.jsonl") if r["auto_class"] != "no_dose"}
    bc = {r["instance_id"]: r for r in read_jsonl(RD2_DIR / "basis_check" / "per_item.jsonl")}
    sec = {q["qid"]: q.get("section") or "" for q in read_jsonl(QUESTIONS)}
    if not rows or not bc:
        raise SystemExit("need extract_rows.jsonl (rd2_extract.py) and basis_check/per_item.jsonl (rd2_basis_check.py)")
    src = {}
    for iid, r in rows.items():
        s = []
        if r["auto_class"] in A_CLASSES:
            s.append("A_auto")
        if bc.get(iid, {}).get("flag_full"):
            s.append("B_basis_flag")
        if s:
            src[iid] = s
    rest = sorted(i for i in rows if i not in src)
    rng = random.Random(SEED)
    k = min(len(rest), max(args.controls_min, int(round(args.controls_frac * len(rest)))))
    for iid in rng.sample(rest, k):
        src[iid] = ["C_control"]
    order = sorted(src)
    rng.shuffle(order)
    QC.mkdir(parents=True, exist_ok=True)
    with (QC / "rd2_adjudication_sheet.csv").open("w", newline="", encoding="utf-8-sig") as fh, \
            (QC / "rd2_adjudication_key.csv").open("w", newline="", encoding="utf-8-sig") as fk:
        w, wk = csv.writer(fh), csv.writer(fk)
        w.writerow(["check_id", "drug", "population_tag", "label_section", "question", "answer", "label_target_sentence",
                    "label_excerpt", "dailymed_url"] + HUMAN_COLS)
        wk.writerow(["check_id", "instance_id", "sources", "auto_class", "auto_subtype", "basis_flag_full", "basis_flag_type_full",
                     "basis_flag_strict", "generator", "answer_condition", "stratum", "n_selected_controls", "n_rest"])
        for i, iid in enumerate(order):
            r, b = rows[iid], bc.get(iid, {})
            cid = "RD2Q%04d" % i
            w.writerow([cid, r["drug"], r.get("population") or "", sec.get(r["qid"], ""), r["question"], r["answer"], r["target_sentence"],
                        r["excerpt"], "https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=%s" % r.get("set_id")] +
                       [""] * len(HUMAN_COLS))
            wk.writerow([cid, iid, "+".join(src[iid]), r["auto_class"], r.get("subtype", ""), b.get("flag_full"),
                         b.get("flag_type_full", ""), b.get("flag_strict"), r["generator"], r["condition"], r.get("stratum"),
                         k, len(rest)])
    log("RD2_adjudication_sheet", rows=len(order), A=sum("A_auto" in s for s in src.values()),
        B=sum("B_basis_flag" in s for s in src.values()), C=k, rest=len(rest), out=str(QC))


if __name__ == "__main__":
    main()
