#!/usr/bin/env python3
"""(RD2-1) Pre-registered RD2 dosing questions from FDA label text (CPU, deterministic, seed 20261002, no API).

Question construction is IDENTICAL to the original RD (scripts/journal2/rd_questions.py): the label's
dosage_and_administration text is split with rd_questions.sentences(); a TARGET sentence has >= 1 non-concentration dose
span (src/unit_norm_fix.find_spans; rd_questions.dose_kinds_ok), 25-600 chars; excerpt = target +/- whole neighbouring
sentences up to 900 chars; exactly one [DOSE] slot (the first non-concentration dose = primary_target), other doses
masked as [...]; same question template.  build_question() below is that code factored out; the unit test
(scripts/journal5/test_rd2.py) re-creates results/journal2/real_dose/questions.jsonl byte-for-byte from
data/real_labels/labels.jsonl with RD's selection policy to prove it.

What differs (documented in prereg/rd2_prereg.md): (0) the "mg/m 2" -> "mg/m2" superscript repair of the label text
(repair_m2 below; otherwise the BSA basis is invisible to find_spans), and WHICH sentences become questions:
  * labels: results/journal5/rd2/labels/labels.jsonl -- drug-disjoint from RD (rd2_common.label_overlaps_rd1), so no
    drug/population/indication combination of RD can recur; every candidate is re-checked here.
  * non-dose [DOSE] slots are not eligible (non_dose_target: renal-function thresholds in mL/min, diluent volumes).
  * every eligible sentence of a label is a candidate (RD: first 2 in text order).  Each is tagged with pre-registered
    dosing types (rd2_common.tag_dosing): bsa, weight_based, loading_maintenance, renal, pediatric, divided_daily
    (error-prone strata) or fixed.
  * per drug: up to --per-drug 3 targets, >= --gap 300 chars apart, distinct masked text, error-prone first and at most
    one per stratum in the first pass (diversity), ties broken by a seeded shuffle.
  * global: --n 480 questions = round-robin over the error-prone strata (seeded order) until n*(1-fixed_share), then
    fixed-dose controls (--fixed-share 0.15) so RD2 keeps a fixed-dose comparison stratum; error-prone fill if short.
Output: results/journal5/rd2/real_dose/questions.jsonl (+ questions_manifest.json); qid = RD2_<drug>_<k>.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import (ERROR_PRONE, QUESTIONS, RD2_LABELS, ROOT, SEED, STRATA, label_overlaps_rd1, last_heading, log,  # noqa: E402
                        rd1_exclusion, read_jsonl, sha256_file, tag_dosing, write_jsonl)
from rd_questions import dose_kinds_ok, sentences  # noqa: E402  (original RD code, unchanged)
from unit_norm_fix import find_spans  # noqa: E402

TEMPLATE = ('According to the US prescribing information for %s, what dose goes in [DOSE] here: "%s"? '
            "State the dose with its unit.")


# openFDA flattens the superscript of m<sup>2</sup> to "m 2"; UNF v1 find_spans then reads "75 mg/m 2" as "75 mg" (the
# BSA basis is lost -- the source of RD's per_m2 parser artifacts).  RD2 repairs exactly this pattern in the label text
# before sentence splitting (documented deviation; RD labels/questions are untouched).
M2_REPAIR = re.compile(r"(\b(?:mg|mcg|micrograms?|g|grams?|units?|IU|mEq|mmol|mL)\s*/\s*)m\s+2\b")


def repair_m2(text: str) -> str:
    return M2_REPAIR.sub(lambda m: m.group(1) + "m2", text)


def label_sentences(lab: dict, repair: bool = False):
    text = re.sub(r"\s+", " ", lab["dosage_and_administration"]).strip()
    if repair:
        text = repair_m2(text)
    return text, sentences(text)


def eligible(s: str):
    """rd_questions eligibility: dose spans, not concentration-only, 25-600 chars.  Returns spans or None."""
    sp = find_spans(s)
    if not sp or not dose_kinds_ok(sp) or len(s) < 25 or len(s) > 600:
        return None
    return sp


def build_question(lab: dict, sents: list, i: int, sp: list, qid: str, window: int = 900) -> dict:
    """Exactly the per-target body of scripts/journal2/rd_questions.main (window growth, masking, template)."""
    off, s = sents[i]
    lo = hi = i
    cur = len(s)
    while True:
        grew = False
        if hi + 1 < len(sents) and cur + len(sents[hi + 1][1]) + 1 <= window:
            hi += 1
            cur += len(sents[hi][1]) + 1
            grew = True
        if lo - 1 >= 0 and cur + len(sents[lo - 1][1]) + 1 <= window:
            lo -= 1
            cur += len(sents[lo][1]) + 1
            grew = True
        if not grew:
            break
    excerpt = " ".join(x[1] for x in sents[lo:hi + 1])
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
    return {"qid": qid, "drug": lab["drug"], "set_id": lab.get("set_id"), "in_dose_bases": lab.get("in_dose_bases"),
            "target_sentence": s, "target_spans": [d.text for d in sp], "primary_target": prim.text, "masked": masked,
            "excerpt": excerpt, "question": TEMPLATE % (lab["drug"], masked)}


def rd_policy_questions(labels: list, per_drug: int = 2, gap: int = 500, window: int = 900) -> list:
    """RD's own selection (first per_drug eligible sentences in text order, gap apart) -- used by the reproduction test
    and to tag RD questions with the same dosing-type tagger for the expected-error estimate."""
    qs = []
    for lab in labels:
        text, sents = label_sentences(lab)
        picked, last_end = 0, -10 ** 9
        for i, (off, s) in enumerate(sents):
            if picked >= per_drug:
                break
            sp = eligible(s)
            if sp is None or off - last_end < gap:
                continue
            qid = "RD_%s_%d" % (re.sub(r"[^a-z0-9]+", "_", lab["drug"]), picked)
            qs.append(build_question(lab, sents, i, sp, qid, window))
            picked += 1
            last_end = off + len(s)
    return qs


def tag_question(q: dict, label_text: str) -> dict:
    """Dosing-type tags for a built question (needs the normalised label text for the preceding context)."""
    pos = label_text.find(q["target_sentence"])
    before = repair_m2(label_text[max(0, pos - 4000):pos]) if pos >= 0 else ""
    s = repair_m2(q["target_sentence"])  # no-op for RD2 (already repaired); lets RD questions be tagged identically
    sp = find_spans(s)
    prim = next(d for d in sp if not d.conc)
    t = tag_dosing(s, before, sp, prim)
    t["section"] = last_heading(before)
    return t


_RENAL_THRESH = re.compile(r"(clearance|CrCl|CLcr|GFR|eGFR)\W[^.]{0,40}$", re.I)
_DILUENT = re.compile(r"\b(dilut\w*|reconstitut\w*|admix\w*|add(?:ed)? to|mix(?:ed)? with|flush\w*)\b", re.I)


def non_dose_target(s: str, sp: list) -> str:
    """RD2-only eligibility filter: the [DOSE] slot must be a dose, not a renal-function threshold ('creatinine clearance
    [DOSE] mL/min') or a diluent/reconstitution volume ('dilute to [DOSE] mL').  '' = keep."""
    prim = next(d for d in sp if not d.conc)
    if prim.kind == "volume" and (prim.time in ("/min", "/h") or "min" in prim.text) and _RENAL_THRESH.search(s[:prim.start]):
        return "renal_threshold"
    if prim.kind == "volume" and _DILUENT.search(s):
        return "diluent_volume"
    return ""


def candidates(lab: dict, stats: Counter = None) -> list:
    text, sents = label_sentences(lab, repair=True)
    out = []
    for i, (off, s) in enumerate(sents):
        sp = eligible(s)
        if sp is None:
            continue
        nd = non_dose_target(s, sp)
        if nd:
            if stats is not None:
                stats[nd] += 1
            continue
        q = build_question(lab, sents, i, sp, qid="")
        q.update(tag_question(q, text))
        q["_off"], q["_end"] = off, off + len(s)
        out.append(q)
    return out


def pick_per_drug(cands: list, per_drug: int, gap: int, rng: random.Random) -> list:
    order = list(cands)
    rng.shuffle(order)
    order.sort(key=lambda q: (q["stratum"] == "fixed", -len(q["dosing_types"])))  # stable: shuffle breaks ties
    picked = []

    def ok(q):
        return all(abs(q["_off"] - p["_off"]) >= gap and q["masked"] != p["masked"] and
                   q["target_sentence"] != p["target_sentence"] for p in picked)
    seen_strata = set()
    for q in order:  # pass 1: one per stratum
        if len(picked) >= per_drug:
            break
        if q["stratum"] not in seen_strata and ok(q):
            picked.append(q)
            seen_strata.add(q["stratum"])
    for q in order:  # pass 2: fill
        if len(picked) >= per_drug:
            break
        if q not in picked and ok(q):
            picked.append(q)
    return picked


def select(labels: list, n: int, per_drug: int, gap: int, fixed_share: float, seed: int) -> tuple:
    excl = rd1_exclusion()
    rng = random.Random(seed)
    pool, dropped, nd = [], Counter(), Counter()
    for lab in sorted(labels, key=lambda l: l["drug"]):
        why = label_overlaps_rd1(lab, excl)
        if why:
            dropped[why.split(":")[0]] += 1
            continue
        cs = [c for c in candidates(lab, nd) if c["target_sentence"] not in excl["target_sentences"]]
        drng = random.Random("%d|%s" % (seed, lab["drug"]))
        pool.extend(pick_per_drug(cs, per_drug, gap, drng))
    ep = defaultdict(list)
    fixed = []
    for q in pool:
        (fixed if q["stratum"] == "fixed" else ep[q["stratum"]]).append(q)
    for k in sorted(ep):
        rng.shuffle(ep[k])
    rng.shuffle(fixed)
    n_ep = int(round(n * (1 - fixed_share)))
    chosen = []
    strata = [s for s in STRATA if ep.get(s)]
    while len(chosen) < n_ep and any(ep[s] for s in strata):
        for s in strata:
            if ep[s] and len(chosen) < n_ep:
                chosen.append(ep[s].pop(0))
    chosen.extend(fixed[: n - len(chosen)])
    rest = [q for s in strata for q in ep[s]]  # fill with error-prone if fixed ran short
    chosen.extend(rest[: max(0, n - len(chosen))])
    # deterministic output order + qids
    chosen.sort(key=lambda q: (q["drug"], q["_off"]))
    k = Counter()
    out = []
    for q in chosen:
        slug = re.sub(r"[^a-z0-9]+", "_", q["drug"])
        q = {kk: v for kk, v in q.items() if not kk.startswith("_")}
        q["qid"] = "RD2_%s_%d" % (slug, k[slug])
        k[slug] += 1
        q["rd2_error_prone"] = q["stratum"] in ERROR_PRONE
        out.append(q)
    info = {"labels": len(labels), "labels_dropped_overlap": dict(dropped), "non_dose_targets_dropped": dict(nd), "pool_after_per_drug": len(pool),
            "pool_by_stratum": dict(Counter(q["stratum"] for q in pool))}
    return out, info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=str(RD2_LABELS))
    ap.add_argument("--n", type=int, default=480)
    ap.add_argument("--per-drug", type=int, default=3)
    ap.add_argument("--gap", type=int, default=300)
    ap.add_argument("--fixed-share", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=str(QUESTIONS))
    args = ap.parse_args()
    labels = read_jsonl(args.labels)
    if not labels:
        raise SystemExit("no labels in %s (run scripts/journal5/rd2_fetch_labels.py)" % args.labels)
    qs, info = select(labels, args.n, args.per_drug, args.gap, args.fixed_share, args.seed)
    out = Path(args.out)
    write_jsonl(out, qs)
    import json
    rel = lambda p: str(Path(p).resolve().relative_to(ROOT)) if str(Path(p).resolve()).startswith(str(ROOT)) else str(p)  # noqa: E731
    man = dict(info, questions=len(qs), drugs=len({q["drug"] for q in qs}), out=rel(out), sha256=sha256_file(out),
               labels_file=rel(args.labels), labels_sha256=sha256_file(args.labels),
               params={"n": args.n, "per_drug": args.per_drug, "gap": args.gap, "fixed_share": args.fixed_share,
                       "seed": args.seed, "window": 900},
               by_stratum=dict(Counter(q["stratum"] for q in qs)),
               by_dosing_type_multilabel=dict(Counter(t for q in qs for t in q["dosing_types"])),
               by_primary_basis=dict(Counter(q["primary_basis"] for q in qs)),
               by_population=dict(Counter(q["population"] for q in qs)),
               mixed_basis_sentences=sum(q["mixed_basis_sentence"] for q in qs))
    out.with_name("questions_manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    log("RD2_questions", **man)


if __name__ == "__main__":
    main()
