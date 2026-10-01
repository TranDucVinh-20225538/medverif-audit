#!/usr/bin/env python3
"""(RD-3) Flag naturally occurring dose errors in generator answers (rule-based, CPU, no API).

Dose mentions (value + unit, ranges, /kg, /m2, time suffixes) are extracted with
src/unit_norm_fix.find_spans and normalised with canonical_quantity (mass -> mcg, volume -> mL,
time -> /day where exact; units/mEq/mmol kept).  The answer's FIRST dose mention (primary) is
compared with the dose mentions of the label TARGET sentence the question was built from:

  correct              same canonical quantity as a target dose (range containment allowed);
                       `correct_converted` = same quantity, different surface unit (natural conversion)
  match_other_context  matches a dose elsewhere in the excerpt, not the target  (excluded)
  unit_error           a target dose has the same numeral(s) but a different unit / basis
                       (subtypes: unit_swap mg<->mcg etc., per_kg, per_m2, unit_kind IU<->mg, time_basis)
  basis_error          no shared numeral; the answer uses another dose basis (/kg, /m2) than the target
  value_error          same unit and basis as a target dose, different number
                       (subtypes: decimal_shift = power-of-10 ratio, other)
  time_ambiguous       per-day vs no time unit (e.g. "1 g/day" vs "500 mg twice daily"; excluded)
  unverifiable         answer quantity kind absent from the target sentence (excluded)
  no_dose              answer states no dose (excluded)
Primary error set = unit_error + basis_error + value_error ("unit-type" = unit_error + basis_error).

Outputs: results/journal2/real_dose/instances.jsonl (claim = answer, evidence = label excerpt; every
answer with a dose), results/journal2/real_dose/extract_manifest.json,
qc/real_dose_errors_check.csv (NEW: every flagged error + time_ambiguous/unverifiable + seeded
controls, blind to checker verdicts, for human verification).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr2_common import RD, RD_QC, ROOT, is_done, log, mark_done, read_jsonl, write_jsonl  # noqa: E402
from unit_norm_fix import canonical_quantity, find_spans  # noqa: E402

STAGE = "RD3_extract"
QC = RD_QC
ERRORS = ("unit_error", "basis_error", "value_error")
SEED = 20261001


def canon(s):
    c = canonical_quantity(s.text)
    if c is None:
        return None
    key, lo, hi = c
    return key, lo, (hi if hi is not None else lo)


def same_q(a, b) -> bool:
    if a is None or b is None or a[0] != b[0]:
        return False
    (alo, ahi), (blo, bhi) = (a[1], a[2]), (b[1], b[2])
    if alo == blo and ahi == bhi:
        return True
    return (blo <= alo <= bhi and blo <= ahi <= bhi) or (alo <= blo <= ahi and alo <= bhi <= ahi)


def nums(s) -> tuple:
    return tuple(x for x in (s.n1, s.n2) if x is not None)


def pow10(r: Decimal) -> bool:
    if r <= 0:
        return False
    for k in range(-6, 7):
        if r == Decimal(10) ** k and k != 0:
            return True
    return False


def classify(answer: str, target: str, excerpt: str, primary: str = None) -> dict:
    a_sp = find_spans(answer)
    if not a_sp:
        return {"auto_class": "no_dose", "subtype": "", "answer_spans": []}
    p = a_sp[0]
    pc = canon(p)
    t_sp = find_spans(target)
    if primary:  # single [DOSE] slot: only the primary target counts as correct; check it first for errors too
        pr = [t for t in t_sp if t.text == primary]
        t_sp = pr + [t for t in t_sp if t.text != primary]
    e_sp = find_spans(excerpt)
    base = {"answer_spans": [s.text for s in a_sp], "primary": p.text, "target_spans": [s.text for s in t_sp],
            "n_answer_spans": len(a_sp)}
    any_unmatched = any(not any(same_q(canon(s), canon(t)) for t in e_sp) for s in a_sp)
    base["any_answer_span_unmatched_in_excerpt"] = any_unmatched
    for t in (t_sp[:1] if primary else t_sp):
        if same_q(pc, canon(t)):
            sub = "correct_converted" if (p.unit != t.unit or p.time != t.time) else "exact"
            return dict(base, auto_class="correct", subtype=sub, matched=t.text)
    for t in e_sp:
        if same_q(pc, canon(t)):
            return dict(base, auto_class="match_other_context", subtype="", matched=t.text)
    pn = nums(p)
    for t in t_sp:  # same numeral(s), different unit / basis
        if nums(t) == pn:
            if p.kind != t.kind:
                sub = "unit_kind"
            elif (p.kg, p.m2, p.conc) != (t.kg, t.m2, t.conc):
                sub = "per_kg" if p.kg != t.kg else ("per_m2" if p.m2 != t.m2 else "concentration")
            elif p.unit != t.unit:
                sub = "unit_swap"
            elif p.time != t.time:
                if not p.time or not t.time:
                    return dict(base, auto_class="time_ambiguous", subtype="time_missing_one_side", matched=t.text)
                sub = "time_basis"
            else:
                continue
            return dict(base, auto_class="unit_error", subtype=sub, matched=t.text)
    same_key = [t for t in t_sp if canon(t) and pc and canon(t)[0] == pc[0]]
    if same_key:
        t = same_key[0]
        r = (pc[1] / canon(t)[1]) if canon(t)[1] else Decimal(0)
        return dict(base, auto_class="value_error", subtype="decimal_shift" if pow10(r) else "other", matched=t.text,
                    ratio=float(r) if r else None)
    same_kind_den = [t for t in t_sp if t.kind == p.kind and (t.kg, t.m2, t.conc) == (p.kg, p.m2, p.conc)]
    if same_kind_den and (not p.time or not same_kind_den[0].time):
        return dict(base, auto_class="time_ambiguous", subtype="time_missing_one_side", matched=same_kind_den[0].text)
    if same_kind_den:  # both have different explicit time units, not exactly convertible
        return dict(base, auto_class="value_error", subtype="other_time", matched=same_kind_den[0].text)
    same_kind = [t for t in t_sp if t.kind == p.kind]
    if same_kind:
        return dict(base, auto_class="basis_error", subtype="per_kg" if p.kg != same_kind[0].kg else
                    ("per_m2" if p.m2 != same_kind[0].m2 else "concentration"), matched=same_kind[0].text)
    return dict(base, auto_class="unverifiable", subtype="kind_absent", matched="")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", type=int, default=40, help="seeded 'correct' controls in the QC sheet")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    qs = {q["qid"]: q for q in read_jsonl(RD / "questions.jsonl")}
    answers = [a for a in read_jsonl(RD / "answers.jsonl") if a.get("answer")]
    seen, inst, rows, stats = set(), [], [], Counter()
    for a in answers:
        k = (a["qid"], a["generator"], a["condition"])
        if k in seen or a["qid"] not in qs:
            continue
        seen.add(k)
        q = qs[a["qid"]]
        c = classify(a["answer"], q["target_sentence"], q["excerpt"], q.get("primary_target"))
        stats[(a["condition"], c["auto_class"])] += 1
        iid = "%s__%s__%s" % k
        rows.append(dict(c, instance_id=iid, qid=a["qid"], drug=q["drug"], generator=a["generator"], condition=a["condition"],
                         answer=a["answer"], question=q["question"], target_sentence=q["target_sentence"], excerpt=q["excerpt"],
                         set_id=q.get("set_id"), in_dose_bases=q.get("in_dose_bases")))
        if c["auto_class"] == "no_dose":
            continue
        inst.append({"instance_id": iid, "base_id": q["drug"], "type": "DOSE", "subset": "real_dose",
                     "condition": "RD-" + c["auto_class"], "magnitude": c.get("subtype") or "none",
                     "claim": a["answer"], "evidence": q["excerpt"], "claim_span": c.get("primary"),
                     "evidence_span": c.get("matched"), "expected_verdict": "PASS" if c["auto_class"] == "correct" else
                     ("FAIL" if c["auto_class"] in ERRORS else "NA"), "valid": True, "generator": a["generator"],
                     "answer_condition": a["condition"], "qid": a["qid"], "drug": q["drug"], "auto_class": c["auto_class"],
                     "auto_subtype": c.get("subtype"), "source": "journal2_real_dose"})
    out_inst = RD / "instances.jsonl" if not args.dry_run else Path("/tmp/rd_instances_dryrun.jsonl")
    write_jsonl(out_inst, inst)
    write_jsonl((RD / "extract_rows.jsonl") if not args.dry_run else Path("/tmp/rd_extract_rows_dryrun.jsonl"), rows)
    # QC sheet: all flagged + ambiguous/unverifiable + seeded controls (correct, other-context)
    rng = random.Random(SEED)
    flagged = [r for r in rows if r["auto_class"] in ERRORS + ("time_ambiguous", "unverifiable")]
    correct = sorted([r for r in rows if r["auto_class"] == "correct"], key=lambda r: r["instance_id"])
    other = sorted([r for r in rows if r["auto_class"] == "match_other_context"], key=lambda r: r["instance_id"])
    sheet = flagged + rng.sample(correct, min(args.controls, len(correct))) + rng.sample(other, min(args.controls // 2, len(other)))
    rng.shuffle(sheet)
    qc = QC if not args.dry_run else Path("/tmp/real_dose_errors_check_dryrun.csv")
    qc.parent.mkdir(parents=True, exist_ok=True)
    with qc.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["check_id", "instance_id", "drug", "generator", "answer_condition", "question", "answer", "answer_dose_spans",
                    "auto_primary_dose", "auto_class", "auto_subtype", "auto_matched_label_dose", "label_target_sentence",
                    "label_target_doses", "label_excerpt", "dailymed_url",
                    "human_answer_dose_is_error (Y/N/unclear)", "human_error_type (unit/basis/value/context/none)", "note"])
        for i, r in enumerate(sheet):
            w.writerow(["RDQ%04d" % i, r["instance_id"], r["drug"], r["generator"], r["condition"], r["question"], r["answer"],
                        "; ".join(r.get("answer_spans") or []), r.get("primary", ""), r["auto_class"], r.get("subtype", ""),
                        r.get("matched", ""), r["target_sentence"], "; ".join(r.get("target_spans") or []), r["excerpt"],
                        "https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=%s" % r.get("set_id"), "", "", ""])
    man = {"answers": len(rows), "instances": len(inst), "by_condition_class": {"%s|%s" % k: v for k, v in sorted(stats.items())},
           "subtypes": dict(Counter("%s|%s" % (r["auto_class"], r.get("subtype")) for r in rows if r["auto_class"] in ERRORS)),
           "qc_rows": len(sheet), "qc_file": str(qc.relative_to(ROOT)) if str(qc).startswith(str(ROOT)) else str(qc)}
    if not args.dry_run:
        (RD / "extract_manifest.json").write_text(json.dumps(man, indent=1) + "\n")
        mark_done(STAGE, **{k: v for k, v in man.items() if k != "by_condition_class"})
    log(STAGE, **man)


if __name__ == "__main__":
    main()
