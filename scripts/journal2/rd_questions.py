#!/usr/bin/env python3
"""(RD-1) Dosing questions grounded on real FDA label text (CPU, deterministic, no API).

For every label in data/real_labels/labels.jsonl, the dosage_and_administration text is split into
sentences; sentences with >=1 parseable dose span (src/unit_norm_fix.find_spans: value + unit) are
candidate TARGET sentences.  Up to --per-drug targets per drug are taken in text order, at least
--gap characters apart.  For each target:
  excerpt   = target sentence +/- neighbouring sentences (<= --window chars), the evidence a checker sees
  masked    = target sentence with every dose span replaced by "[DOSE]" (the question's context)
  question  = "According to the US prescribing information for <drug>, what dose goes in [DOSE] here:
               "<masked>"? State the dose with its unit."
Two answer conditions are generated later (rd_generate.py): `grounded` (excerpt in the prompt) and
`closed` (no excerpt; model answers from memory) -- both are checked against the same excerpt.

Output: results/journal2/real_dose/questions.jsonl
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr2_common import LABELS, RD, is_done, log, mark_done, read_jsonl, write_jsonl  # noqa: E402
from unit_norm_fix import find_spans  # noqa: E402

STAGE = "RD1_questions"
OUT = RD / "questions.jsonl"
_SENT = re.compile(r"(?<=[.;:])\s+(?=[A-Z0-9(•\u2022-])|\s+(?=\d{1,2}\.\d{1,2}\s+[A-Z])|\s*[•\u2022]\s*")


def sentences(text: str) -> list:
    out, pos = [], 0
    for m in _SENT.finditer(text):
        s = text[pos:m.start()].strip()
        if s:
            out.append((pos, s))
        pos = m.end()
    tail = text[pos:].strip()
    if tail:
        out.append((pos, tail))
    return out


def dose_kinds_ok(spans) -> bool:
    # concentration-only sentences ("10 mg/mL vial") are poor dosing targets
    return any(not s.conc for s in spans)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=str(LABELS))
    ap.add_argument("--per-drug", type=int, default=2)
    ap.add_argument("--gap", type=int, default=500)
    ap.add_argument("--window", type=int, default=900)
    ap.add_argument("--max-drugs", type=int, default=0)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    labels = read_jsonl(Path(args.labels))
    if args.max_drugs:
        labels = labels[: args.max_drugs]
    if not labels:
        raise SystemExit("no labels in %s (run scripts/journal2/rd_fetch_labels.py on a machine with internet)" % args.labels)
    qs = []
    for lab in labels:
        text = re.sub(r"\s+", " ", lab["dosage_and_administration"]).strip()
        sents = sentences(text)
        picked, last_end = 0, -10 ** 9
        for i, (off, s) in enumerate(sents):
            if picked >= args.per_drug:
                break
            sp = find_spans(s)
            if not sp or not dose_kinds_ok(sp) or len(s) < 25 or len(s) > 600 or off - last_end < args.gap:
                continue
            # window: grow left/right by whole sentences up to --window chars
            lo = hi = i
            cur = len(s)
            while True:
                grew = False
                if hi + 1 < len(sents) and cur + len(sents[hi + 1][1]) + 1 <= args.window:
                    hi += 1
                    cur += len(sents[hi][1]) + 1
                    grew = True
                if lo - 1 >= 0 and cur + len(sents[lo - 1][1]) + 1 <= args.window:
                    lo -= 1
                    cur += len(sents[lo][1]) + 1
                    grew = True
                if not grew:
                    break
            excerpt = " ".join(x[1] for x in sents[lo:hi + 1])
            # exactly one [DOSE] slot (the first non-concentration dose); other doses in the sentence are
            # hidden as [...] so the question has a single answer and no dose leaks into the prompt
            prim = next(d for d in sp if not d.conc)
            masked, last = [], 0
            for d in sp:
                masked.append(s[last:d.start])
                masked.append("[DOSE]" if d is prim else "[...]")
                last = d.end
            masked.append(s[last:])
            masked = "".join(masked)
            if len(masked) > 320:
                j = masked.find("[DOSE]")
                a = max(0, j - 150)
                masked = ("..." if a else "") + masked[a:a + 300] + "..."
            qid = "RD_%s_%d" % (re.sub(r"[^a-z0-9]+", "_", lab["drug"]), picked)
            qs.append({"qid": qid, "drug": lab["drug"], "set_id": lab.get("set_id"), "in_dose_bases": lab.get("in_dose_bases"),
                       "target_sentence": s, "target_spans": [d.text for d in sp], "primary_target": prim.text, "masked": masked, "excerpt": excerpt,
                       "question": 'According to the US prescribing information for %s, what dose goes in [DOSE] here: "%s"? '
                                   "State the dose with its unit." % (lab["drug"], masked)})
            picked += 1
            last_end = off + len(s)
    out = Path(args.out) if not args.dry_run else Path("/tmp/rd_questions_dryrun.jsonl")
    write_jsonl(out, qs)
    info = {"labels": len(labels), "questions": len(qs), "drugs_with_question": len({q["drug"] for q in qs}), "out": str(out)}
    if not args.dry_run:
        mark_done(STAGE, **info)
    log(STAGE, **info)


if __name__ == "__main__":
    main()
