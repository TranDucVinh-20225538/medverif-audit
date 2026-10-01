#!/usr/bin/env python3
"""(J4-BC) Deterministic rule-based DOSE BASIS CHECK: does the answer's dose basis disagree with the evidence?

Motivation: the small fact-checkers are "unit-blind" on real drug-dose answers; the real errors in the RD set
(results/journal2/real_dose/instances.jsonl) include dropped weight bases (label "0.7 mg per kg" -> answer "0.7 mg",
losartan; tacrolimus "0.2 mg/kg/day" -> "0.2 mg"), kg -> lb swaps (ethambutol "15 mg/kg" -> "15 mg/lb") and time-basis
swaps (clonidine patch "0.1 mg/day" -> "0.1 mg/week").  This module flags such disagreements from the (claim=answer,
evidence=label excerpt) pair ONLY -- the same two texts a checker sees; it never uses the gold target span/sentence.

DESIGN PROVENANCE: written AFTER inspecting the 47 auto-flagged unit-type rows and the 12 AI-precheck "true" unit errors
(qc/ai_precheck_real_dose_unit_errors.csv = dev set), BEFORE running it on the full 1451-answer RD set.  Frozen in git
(see notes/journal4_basis_check.md); evaluation lives in scripts/journal4/basis_check_eval.py.

Parsing reuses the repo's unit normalizer: UNF v2 surface pre-pass (src/unit_norm_fix_v2.prenormalize: "/m 2"->"/m2",
"mg/kg daily"->"mg/kg/day", unit spellings, number words, ...) followed by UNF v1 span extraction
(src/unit_norm_fix.find_spans: number/range + mass|volume|units|mEq|mmol unit + /kg, /m2, concentration, time).  Small
local extensions on top of the v1 span (documented, applied to the text right after the span):
  E1  "/lb", "per lb", "per pound"                      -> body basis /lb   (v1 has no /lb)
  E2  "<n> mcg of ivermectin per kg"                     -> body basis /kg   ("of" + <=3 words + "per kg")
  E3  "<n> mcg per minute per kilogram"                  -> body basis /kg   (kg after the time suffix)
  E4  "<n> mg once daily|daily|a day|per day|every day"  -> time /day ; "once weekly|weekly|once a week|per week" -> /week
      ("twice daily", "every 12 hours" etc. are dosing FREQUENCIES and are NOT a basis)
Per-dose context tags (from the ~35 chars before / ~25 after the span):
  bound     "maximum", "max", "(not) exceed", "up to", "no more than", "greater/less/lower/higher than", "above", "below"
  strength  absolute dose directly followed by tablet(s)/capsule(s)/vial(s)/patch/... (product strength)
  conc      v1 concentration denominator (/mL, /L, /dL): never compared (trough levels, mg/mL strengths)

Canonical value: Fraction(numeral) * mass->mcg / volume->mL factor; time /min,/h,/day,/week converted to per day when
both sides carry one; /dose and "no time" are kept.  MATCH(a, e): same quantity kind, same body basis (kg<->lb
converted with 5% tolerance: 15 mg/kg ~ 7 mg/lb), times equal / convertible / missing on one side, and value
equality or range containment (as scripts/journal2/rd_extract.same_q).

RULES, per answer dose a (concentration spans skipped):
  0. a MATCHes any evidence dose                                         -> consistent (never flagged).
  R1 (paired, "number neighbourhood"): candidates = evidence doses sharing at least one surface numeral with a.
     Each candidate e is typed:
       basis_dropped   e has /kg|/m2|/lb, a has no body basis               (losartan, tacrolimus, buspirone)
       basis_changed   e and a have different body bases                    (ethambutol kg -> lb)
       unit_kind       mass vs units/mEq/mmol, same numeral                  (glyburide 20 units -> 20 mg)
       unit_scale      same kind, different mass/volume unit (mg/mcg/g, mL/L), not equal after conversion
       time_basis      both carry an explicit, different, non-equivalent time among /min,/h,/day,/week (/day vs /week)
       time_ambiguous  /dose vs /day etc. (needs the dosing frequency; not flagged, counts as compatible)
       basis_ok        same kind/basis/unit, time equal or missing on one side (numeric difference only)
       basis_added     a has a body basis the evidence mention lacks (not flagged: e.g. a table header unit)
       other_kind      e.g. mg vs mL (not compared)
     FLAG if >=1 candidate is of a flaggable type and NO candidate is basis_ok / basis_added / time_ambiguous
     (benefit of doubt).
     Additionally (mass-unit mis-conversion, different numerals): flag unit_scale if some evidence dose with the same
     body/time basis and a DIFFERENT unit is exactly 1000^k (k != 0) times a (e.g. label 500 mcg, answer 0.5 g).
  R2 (unpaired, "basis neighbourhood"): if R1 found no candidate with a compatible basis and a is not a bound:
     comparable = evidence doses of a's kind, excluding bounds, strengths and concentrations; restricted to those with
     a's exact time basis if any exist, else to time-compatible ones.  FLAG basis_dropped_unpaired /
     basis_changed_unpaired if comparable is non-empty, EVERY comparable dose has a body basis (/kg, /m2, /lb) and a's
     body basis is none of them (cyclophosphamide 500 mg vs only "mg per kg" doses; filgrastim 300 mcg vs 5 mcg/kg).
  GUARDS (both rules): an absolute answer dose is NOT flagged if the answer itself states a weight W (e.g. "70 kg",
     "154 lb") and a per-weight dose d such that a = d*W (+-10%), i.e. the absolute dose is a worked example.
     R2 only: absolute answer doses are not R2-flagged if the answer also gives a body-based dose that MATCHes the
     evidence (the answer kept the basis).
Variants: "full" = R1 + R2 (primary), "strict" = R1 only (pre-specified secondary).
Item status: no_dose (no non-concentration dose in the answer) | flag | pass (>=1 answer dose matched, or had a
basis_ok R1 candidate, or an R2-comparable set containing a's basis) | abstain (doses present but nothing comparable).

What it cannot do: value errors with the right basis, per-dose vs per-day when one side has no explicit time,
population/indication mismatches with the same basis, units<->mass factors, numbers in tables without units.

Python >= 3.8, stdlib only.  `python scripts/journal4/basis_check.py --selftest` runs the examples below.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import unit_norm_fix as V1  # noqa: E402
import unit_norm_fix_v2 as V2  # noqa: E402

RULE_VERSION = "basis-check-1"
BODY = ("/kg", "/m2", "/lb")
LB_PER_KG = Fraction(220462, 100000)
LB_TOL = Fraction(5, 100)
WEIGHT_TOL = Fraction(10, 100)
FLAG_TYPES_R1 = ("basis_dropped", "basis_changed", "unit_kind", "unit_scale", "time_basis")
PRIORITY = {"basis_dropped": 0, "basis_changed": 1, "unit_kind": 2, "unit_scale": 3, "time_basis": 4}
KIND_SWAP = {"mass", "units", "meq", "mmol"}
COMPATIBLE = ("basis_ok", "basis_added", "time_ambiguous")
TIME_PER_DAY = {"/min": Fraction(1440), "/h": Fraction(24), "/day": Fraction(1), "/week": Fraction(1, 7)}

# extensions (matched against the text right after the v1 span)
_LB_RE = re.compile(r"^\s*(?:/|per)\s*(?:lbs?|pounds?)(?![A-Za-z])", re.I)
_SPLIT_KG_RE = re.compile(r"^\s+of\s+(?:[A-Za-z][\w\-]*\s+){1,3}?per\s+(?:kg|kilograms?)(?![A-Za-z])", re.I)
_TRAIL_KG_RE = re.compile(r"^\s*(?:/|per)\s*(?:kg|kilograms?)(?![A-Za-z])", re.I)
_TRAIL_DAY_RE = re.compile(r"^\s*(?:once\s+)?(?:daily|a\s+day|per\s+day|every\s+day|each\s+day)(?![A-Za-z])", re.I)
_TRAIL_WEEK_RE = re.compile(r"^\s*(?:once\s+)?(?:weekly|a\s+week|per\s+week|every\s+week|each\s+week)(?![A-Za-z])", re.I)
_BOUND_RE = re.compile(r"(maxim|\bmax\b|exceed|\bup\s+to\b|no\s+more\s+than|not\s+more\s+than|greater\s+than|less\s+than|"
                       r"lower\s+than|higher\s+than|in\s+excess\s+of|\babove\b|\bbelow\b)", re.I)
_STRENGTH_RE = re.compile(r"^\s*(?:-\s*)?(?:tablets?|capsules?|caps\b|tabs?\b|vials?|patch(?:es)?|suppositor|strengths?|"
                          r"single-dose|prefilled|pens?\b|film-coated|chewable|ampul)", re.I)
_WEIGHT_RE = re.compile(r"(?<![\w.,/])(\d+(?:\.\d+)?)\s*(?:-\s*)?(kg|kilograms?|lbs?|pounds?)(?![A-Za-z])", re.I)


class Dose:
    """One dose mention: surface text + parsed quantity, body basis, time basis and context tags."""
    __slots__ = ("text", "start", "end", "kind", "unit", "factor", "lo", "hi", "nums", "body", "time", "conc",
                 "bound", "strength", "ext")

    def __init__(self, s, text: str):
        self.start, self.end = s.start, s.end
        self.kind, self.unit, self.factor = s.kind, s.unit, Fraction(str(s.factor))
        self.nums = tuple(x for x in (s.n1, s.n2) if x is not None)
        self.lo = Fraction(str(s.n1))
        self.hi = Fraction(str(s.n2)) if s.n2 is not None else self.lo
        if self.hi < self.lo:
            self.lo, self.hi = self.hi, self.lo
        self.body = "/kg" if s.kg else ("/m2" if s.m2 else "")
        self.time = s.time
        self.conc = bool(s.conc)
        self.ext = []  # extensions applied
        tail = text[s.end:s.end + 60]
        if not self.body:
            m = _LB_RE.match(tail) or None
            if m:
                self.body, self.ext = "/lb", self.ext + ["E1_lb"]
            else:
                m = _SPLIT_KG_RE.match(tail) or (_TRAIL_KG_RE.match(tail) if self.time else None)
                if m:
                    self.body, self.ext = "/kg", self.ext + (["E3_kg_after_time"] if self.time and _TRAIL_KG_RE.match(tail)
                                                              else ["E2_split_kg"])
            if m:
                self.end += m.end()
                tail = text[self.end:self.end + 60]
                if not self.time:  # "15 mg/lb/day" etc.
                    mt = re.match(r"^\s*(?:/|per)\s*(day|week|hour|h|min|minute)(?![A-Za-z])", tail, re.I)
                    if mt:
                        self.time = {"day": "/day", "week": "/week", "hour": "/h", "h": "/h", "min": "/min",
                                     "minute": "/min"}[mt.group(1).lower()]
                        self.end += mt.end()
                        tail = text[self.end:self.end + 60]
        if not self.time:
            if _TRAIL_DAY_RE.match(tail):
                self.time, self.ext = "/day", self.ext + ["E4_day"]
            elif _TRAIL_WEEK_RE.match(tail):
                self.time, self.ext = "/week", self.ext + ["E4_week"]
        self.text = text[self.start:self.end]
        head = text[max(0, self.start - 35):self.start]
        hb = list(_BOUND_RE.finditer(head))
        self.bound = bool(hb) and not re.search(r"\d", head[hb[-1].end():])
        self.strength = (not self.body and not self.time and bool(_STRENGTH_RE.match(text[self.end:self.end + 25])))

    # canonical numerator value (mcg / mL / native) of the range ends
    def base(self) -> Tuple[Fraction, Fraction]:
        return self.lo * self.factor, self.hi * self.factor

    def as_dict(self) -> dict:
        return {"text": self.text, "kind": self.kind, "unit": self.unit, "body": self.body, "time": self.time,
                "conc": self.conc, "bound": self.bound, "strength": self.strength, "ext": self.ext}


def extract_doses(text: str) -> Tuple[str, List[Dose]]:
    """(UNF-v2-prenormalized text, dose mentions)."""
    t = V2.prenormalize(text or "")
    return t, [Dose(s, t) for s in V1.find_spans(t)]


def _values(d: Dose, other: Dose) -> Tuple[Fraction, Fraction, Optional[str]]:
    """Range of d in a unit comparable to `other`: time converted to /day when both have a convertible time."""
    lo, hi = d.base()
    if d.time in TIME_PER_DAY and other.time in TIME_PER_DAY:
        f = TIME_PER_DAY[d.time]
        return lo * f, hi * f, "/day"
    return lo, hi, d.time


def _times_compatible(a: Dose, e: Dose) -> bool:
    if not a.time or not e.time or a.time == e.time:
        return True
    return a.time in TIME_PER_DAY and e.time in TIME_PER_DAY


def _ranges_match(alo, ahi, elo, ehi, tol: Fraction = Fraction(0)) -> bool:
    def eq(x, y):
        return x == y if not tol else abs(x - y) <= tol * max(abs(x), abs(y))
    if eq(alo, elo) and eq(ahi, ehi):
        return True
    return (elo <= alo <= ehi and elo <= ahi <= ehi) or (alo <= elo <= ahi and alo <= ehi <= ahi)


def match(a: Dose, e: Dose) -> bool:
    if a.conc or e.conc or a.kind != e.kind or not _times_compatible(a, e):
        return False
    alo, ahi, _ = _values(a, e)
    elo, ehi, _ = _values(e, a)
    if a.body == e.body:
        return _ranges_match(alo, ahi, elo, ehi)
    if {a.body, e.body} == {"/kg", "/lb"}:  # convert the /lb side to /kg
        if a.body == "/lb":
            alo, ahi = alo * LB_PER_KG, ahi * LB_PER_KG
        else:
            elo, ehi = elo * LB_PER_KG, ehi * LB_PER_KG
        return _ranges_match(alo, ahi, elo, ehi, LB_TOL)
    return False


def pair_type(a: Dose, e: Dose) -> str:
    """Type of the basis relation between an answer dose and an evidence dose sharing a numeral (R1)."""
    if a.kind != e.kind:
        return "unit_kind" if {a.kind, e.kind} <= KIND_SWAP else "other_kind"
    if e.body and a.body != e.body:
        return "basis_dropped" if not a.body else "basis_changed"
    if a.body and not e.body:
        return "basis_added"
    if a.unit != e.unit:
        alo, ahi, _ = _values(a, e)
        elo, ehi, _ = _values(e, a)
        if _ranges_match(alo, ahi, elo, ehi):
            return "basis_ok"
        return "unit_scale"
    if a.time and e.time and a.time != e.time:
        alo, ahi, _ = _values(a, e)
        elo, ehi, _ = _values(e, a)
        if not (a.time in TIME_PER_DAY and e.time in TIME_PER_DAY):
            return "time_ambiguous"  # /dose vs /day|/week...: depends on the dosing frequency -> not judged
        if _ranges_match(alo, ahi, elo, ehi):
            return "basis_ok"
        return "time_basis"
    return "basis_ok"


def _is_pow1000(r: Fraction) -> bool:
    for k in (-3, -2, -1, 1, 2, 3):
        if r == Fraction(1000) ** k:
            return True
    return False


def answer_weights(text: str) -> List[Tuple[Fraction, str]]:
    """Body weights stated in a (prenormalized) answer: [(value, 'kg'|'lb')]; '/kg' denominators are skipped."""
    out = []
    for m in _WEIGHT_RE.finditer(text):
        head = text[max(0, m.start() - 5):m.start()]
        if re.search(r"(/|per)\s*$", head, re.I):
            continue
        u = m.group(2).lower()
        out.append((Fraction(m.group(1)), "kg" if u.startswith("k") else "lb"))
    return out


def weight_explained(a: Dose, answer_doses: List[Dose], weights: List[Tuple[Fraction, str]]) -> bool:
    """Absolute answer dose a == (per-weight answer dose) x (weight stated in the answer), +-10%."""
    if a.body:
        return False
    alo, ahi = a.base()
    for d in answer_doses:
        if d.body not in ("/kg", "/lb") or d.kind != a.kind or d.conc:
            continue
        dlo, dhi = d.base()
        for w, wu in weights:
            wk = w if (wu == "kg") == (d.body == "/kg") else (w / LB_PER_KG if wu == "lb" else w * LB_PER_KG)
            if dlo * wk * (1 - WEIGHT_TOL) <= alo and ahi <= dhi * wk * (1 + WEIGHT_TOL):
                return True
    return False


def check_pair(claim: str, evidence: str) -> dict:
    """Run the basis check on one (answer, evidence) pair.  Returns status per variant + per-dose details."""
    ct, cds = extract_doses(claim)
    et, eds = extract_doses(evidence)
    cds = [d for d in cds if not d.conc]
    eds_all = [d for d in eds if not d.conc]
    res = {"rule_version": RULE_VERSION, "n_answer_doses": len(cds), "n_evidence_doses": len(eds_all), "doses": []}
    if not cds:
        res.update(status_full="no_dose", status_strict="no_dose", flag_full=False, flag_strict=False,
                   flag_type_full="", flag_type_strict="")
        return res
    weights = answer_weights(ct)
    body_kept = any(d.body in BODY and any(match(d, e) for e in eds_all) for d in cds)
    any_checked = False
    r1_flags, r2_flags = [], []
    for a in cds:
        info = {"answer_dose": a.as_dict(), "matched": "", "r1": [], "r1_flag": "", "r2_flag": "", "r2_comparable": [],
                "checked": False, "note": ""}
        res["doses"].append(info)
        m = next((e for e in eds_all if match(a, e)), None)
        if m is not None:
            info.update(matched=m.text, checked=True)
            any_checked = True
            continue
        explained = weight_explained(a, cds, weights)
        if explained:
            info["note"] = "absolute dose = per-weight answer dose x stated weight"
        # R1: same-numeral candidates
        cands = [e for e in eds_all if set(a.nums) & set(e.nums)]
        types = [(pair_type(a, e), e) for e in cands]
        info["r1"] = [{"evidence_dose": e.text, "type": t} for t, e in types]
        compatible = any(t in COMPATIBLE for t, _ in types)
        if compatible:
            info["checked"] = True
            any_checked = True
        flaggable = sorted([(PRIORITY[t], t, e) for t, e in types if t in FLAG_TYPES_R1], key=lambda x: x[0])
        if flaggable and not compatible and not (explained and flaggable[0][1] == "basis_dropped"):
            info["r1_flag"] = flaggable[0][1]
            info["r1_flag_evidence"] = flaggable[0][2].text
        if not info["r1_flag"] and not compatible and a.kind in ("mass", "volume"):
            for e in eds_all:  # mis-conversion: exactly 1000^k apart, different unit, same body/time basis
                if e.kind == a.kind and e.unit != a.unit and e.body == a.body and _times_compatible(a, e):
                    alo, ahi, _ = _values(a, e)
                    elo, ehi, _ = _values(e, a)
                    if elo and ehi and alo / elo == ahi / ehi and _is_pow1000(alo / elo):
                        info["r1_flag"], info["r1_flag_evidence"] = "unit_scale", e.text
                        break
        if info["r1_flag"]:
            info["checked"] = True
            any_checked = True
            r1_flags.append(info["r1_flag"])
            continue
        if compatible:
            continue
        # R2: unpaired basis neighbourhood
        comp = [e for e in eds_all if e.kind == a.kind and not e.bound and not e.strength]
        exact = [e for e in comp if e.time == a.time]
        comp = exact or [e for e in comp if _times_compatible(a, e)]
        info["r2_comparable"] = [e.text for e in comp]
        if not comp:
            continue
        bases = {e.body for e in comp}
        if a.body in bases:
            info["checked"] = True
            any_checked = True
            continue
        if all(b in BODY for b in bases):
            if a.bound:
                info["note"] = (info["note"] + "; " if info["note"] else "") + "answer dose is a bound: R2 skipped"
            elif not a.body and (explained or body_kept):
                info["note"] = (info["note"] + "; " if info["note"] else "") + "answer keeps the body basis elsewhere: R2 skipped"
            else:
                info["r2_flag"] = "basis_dropped_unpaired" if not a.body else "basis_changed_unpaired"
                info["checked"] = True
                any_checked = True
                r2_flags.append(info["r2_flag"])
    first = lambda fl: sorted(fl, key=lambda t: PRIORITY.get(t, 9))[0] if fl else ""  # noqa: E731
    res["flag_strict"] = bool(r1_flags)
    res["flag_full"] = bool(r1_flags or r2_flags)
    res["flag_type_strict"] = first(r1_flags)
    res["flag_type_full"] = first(r1_flags) or (r2_flags[0] if r2_flags else "")
    checked_strict = any(d["matched"] or any(x["type"] in COMPATIBLE for x in d["r1"]) or d["r1_flag"]
                         or (d["checked"] and not d["r2_flag"]) for d in res["doses"])
    res["status_full"] = "flag" if res["flag_full"] else ("pass" if any_checked else "abstain")
    res["status_strict"] = "flag" if res["flag_strict"] else ("pass" if checked_strict else "abstain")
    return res


# ---------------------------------------------------------------- self-test (examples from the docstring)
SELFTEST = [
    # (name, claim, evidence, expected flag_full, expected flag_type_full)
    ("losartan dropped /kg", "According to the label excerpt, the dose is 0.7 mg once daily (up to 50 mg) for pediatric patients.",
     "Usual adult dose: 50 mg once daily. Usual pediatric starting dose: 0.7 mg per kg once daily (up to 50 mg).", True, "basis_dropped"),
    ("tacrolimus dropped /kg/day", "The initial oral dosage is 0.2 mg capsules, divided in two doses every 12 hours.",
     "Kidney Transplant With azathioprine 0.2 mg/kg/day capsules, divided in two doses, every 12 hours. With MMF 0.1 mg/kg/day.",
     True, "basis_dropped"),
    ("ethambutol kg -> lb", "The dose is 15 mg/lb of body weight, as a single oral dose once every 24 hours.",
     "decrease the dose to 15 mg/kg (7 mg/lb) of body weight, and administer as a single oral dose once every 24 hours.",
     True, "basis_changed"),
    ("clonidine day -> week", "starting with clonidine transdermal system 0.1 mg/week.",
     "starting with clonidine transdermal system 0.1 mg/day. An increase in dosage above 0.3 mg/day is not useful.", True, "time_basis"),
    ("correct mg/kg", "The pediatric starting dose is 0.7 mg/kg once daily, up to 50 mg.",
     "Usual pediatric starting dose: 0.7 mg per kg once daily (up to 50 mg).", False, ""),
    ("mg/kg + absolute for stated weight", "The dose is 15 mg/kg, i.e. 1050 mg for a 70 kg adult, once daily.",
     "decrease the dose to 15 mg/kg (7 mg/lb) of body weight once every 24 hours.", False, ""),
    ("correct lb equivalent", "The dose is 7 mg/lb of body weight.", "the dose is 15 mg/kg (7 mg/lb) of body weight.", False, ""),
    ("correct week equivalent", "The patch delivers 0.7 mg/week.", "clonidine transdermal system 0.1 mg/day.", False, ""),
    ("correct unit conversion", "The dose is 0.5 g twice daily.", "Give 500 mg twice daily.", False, ""),
    ("unit swap mg -> mcg", "The dose is 500 mcg twice daily.", "Give 500 mg twice daily.", True, "unit_scale"),
    ("mis-conversion 500 mcg -> 0.5 g", "The dose is 0.5 g daily.", "The dose is 500 mcg daily.", True, "unit_scale"),
    ("unit kind units -> mg", "The dose is 20 mg.", "If the insulin dose is less than 20 units daily, use glyburide 2.5 to 5 mg.",
     True, "unit_kind"),
    ("unpaired dropped /kg", "The dose is 500 mg to 1,000 mg every 7 to 10 days.",
     "Other regimens include 10 mg per kg to 15 mg per kg given every 7 to 10 days or 3 mg per kg to 5 mg per kg twice weekly.",
     True, "basis_dropped_unpaired"),
    ("value error same basis (not a basis error)", "The dose is 300 mg/m2.", "100 mg/m 2 orally every 8 hours (maximum 800 mg/day)",
     False, ""),
    ("answer adds basis (table header unit)", "The loading dose is 10-15 mcg/kg.", "10-15 mcg = microgram", False, ""),
    ("cap matched exactly", "The dose is 300 mg daily.", "5 mg/kg up to 300 mg daily in a single dose", False, ""),
    ("per-dose vs per-day not judged", "Typical daily dose is 300-600 mg, so 150-300 mg per dose.",
     "Recommended dose is 150 mg/day to 600 mg/day; begin at 300 mg/day in 2 divided doses.", False, ""),
    ("no dose", "Take as directed by your physician.", "Give 500 mg twice daily.", False, ""),
]


def selftest() -> None:
    bad = 0
    for name, c, e, want, wtype in SELFTEST:
        r = check_pair(c, e)
        ok = r["flag_full"] == want and r["flag_type_full"] == wtype
        bad += not ok
        print("%-4s %-45s flag=%-5s type=%-24s status=%s" % ("ok" if ok else "FAIL", name, r["flag_full"], r["flag_type_full"],
                                                               r["status_full"]))
    if bad:
        raise SystemExit("%d self-test case(s) failed" % bad)
    print("basis_check selftest OK (%d cases)" % len(SELFTEST))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--claim")
    ap.add_argument("--evidence")
    args = ap.parse_args()
    if args.selftest or not (args.claim and args.evidence):
        selftest()
        return
    print(json.dumps(check_pair(args.claim, args.evidence), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
