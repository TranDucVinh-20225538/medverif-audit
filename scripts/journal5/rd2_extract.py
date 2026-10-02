#!/usr/bin/env python3
"""(RD2-3) Extraction + auto-classification of RD2 answers with the ORIGINAL RD code (CPU, deterministic, no API).

classify() is imported unchanged from scripts/journal2/rd_extract.py (dose spans via src/unit_norm_fix.find_spans,
canonical quantities, primary-target-first comparison; classes correct / match_other_context / unit_error /
basis_error / value_error / time_ambiguous / unverifiable / no_dose).  Instances are written in EXACTLY the schema of
results/journal2/real_dose/instances.jsonl (same keys and value conventions: claim = answer, evidence = label excerpt,
condition = "RD-<auto_class>", expected_verdict PASS/FAIL/NA, no_dose rows dropped), so every journal-2/3/4 scorer and
judge runs on them unchanged; extra keys (stratum, dosing_types, primary_basis, population, rd2=true) are additive.
`source` = "journal5_rd2" (RD: "journal2_real_dose").

Before running, the frozen files (prereg/rd2_freeze.json: questions sha256 + code sha256 incl. rd_extract.py and
unit_norm_fix.py) are verified; a mismatch stops the run.

Outputs (results/journal5/rd2/real_dose/): instances.jsonl, extract_rows.jsonl, extract_manifest.json
Usage:  python scripts/journal5/rd2_extract.py [--answers A.jsonl] [--outdir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import ANSWERS, QUESTIONS, RD2, assert_frozen, is_done, log, mark_done, read_jsonl, sha256_file, write_jsonl  # noqa: E402
from rd_extract import ERRORS, classify  # noqa: E402  (original RD code, unchanged)

STAGE = "RD2_extract"
EXTRA = ("stratum", "dosing_types", "primary_basis", "population")


def build(questions: list, answers: list):
    qs = {q["qid"]: q for q in questions}
    seen, inst, rows, stats = set(), [], [], Counter()
    for a in answers:
        if not a.get("answer"):
            continue
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
                         set_id=q.get("set_id"), in_dose_bases=q.get("in_dose_bases"), **{x: q.get(x) for x in EXTRA}))
        if c["auto_class"] == "no_dose":
            continue
        inst.append(dict({"instance_id": iid, "base_id": q["drug"], "type": "DOSE", "subset": "real_dose",
                          "condition": "RD-" + c["auto_class"], "magnitude": c.get("subtype") or "none",
                          "claim": a["answer"], "evidence": q["excerpt"], "claim_span": c.get("primary"),
                          "evidence_span": c.get("matched"), "expected_verdict": "PASS" if c["auto_class"] == "correct" else
                          ("FAIL" if c["auto_class"] in ERRORS else "NA"), "valid": True, "generator": a["generator"],
                          "answer_condition": a["condition"], "qid": a["qid"], "drug": q["drug"], "auto_class": c["auto_class"],
                          "auto_subtype": c.get("subtype"), "source": "journal5_rd2"},
                         rd2=True, **{x: q.get(x) for x in EXTRA}))
    return inst, rows, stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(QUESTIONS))
    ap.add_argument("--answers", default=str(ANSWERS))
    ap.add_argument("--outdir", default=str(RD2))
    ap.add_argument("--force", action="store_true", help="re-extract even if the marker exists (extraction is deterministic)")
    args = ap.parse_args()
    if is_done(STAGE) and not args.force and Path(args.outdir) == RD2:
        log(STAGE, skipped="marker present")
        return
    assert_frozen(require_questions=Path(args.questions) == QUESTIONS)
    questions = read_jsonl(args.questions)
    answers = read_jsonl(args.answers)
    if not answers:
        raise SystemExit("no answers in %s (run scripts/journal5/rd2_generate.py)" % args.answers)
    inst, rows, stats = build(questions, answers)
    outd = Path(args.outdir)
    write_jsonl(outd / "instances.jsonl", inst)
    write_jsonl(outd / "extract_rows.jsonl", rows)
    man = {"answers": len(rows), "instances": len(inst),
           "by_condition_class": {"%s|%s" % k: v for k, v in sorted(stats.items())},
           "by_generator_class": {"%s|%s" % k: v for k, v in sorted(Counter((r["generator"], r["auto_class"]) for r in rows).items())},
           "by_stratum_class": {"%s|%s" % k: v for k, v in sorted(Counter((r["stratum"], r["auto_class"]) for r in rows).items())},
           "subtypes": dict(Counter("%s|%s" % (r["auto_class"], r.get("subtype")) for r in rows if r["auto_class"] in ERRORS)),
           "auto_unit_type": sum(r["auto_class"] in ("unit_error", "basis_error") for r in rows),
           "questions_sha256": sha256_file(args.questions), "answers_sha256": sha256_file(args.answers),
           "classifier": "scripts/journal2/rd_extract.classify (unchanged)"}
    (outd / "extract_manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    if outd == RD2:
        mark_done(STAGE, answers=len(rows), instances=len(inst), auto_unit_type=man["auto_unit_type"])
    log(STAGE, **{k: v for k, v in man.items() if k not in ("by_generator_class", "by_stratum_class")})


if __name__ == "__main__":
    main()
