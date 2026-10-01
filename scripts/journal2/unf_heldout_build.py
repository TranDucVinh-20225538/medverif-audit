#!/usr/bin/env python3
"""(UNF-HO-1) HELD-OUT evaluation set for the unit normalizers, built from REAL dose strings (stdlib, deterministic).

Built AFTER the freeze of src/unit_norm_fix_v2.py (results/journal2/unf_v2_freeze.json, commit 81d078b); neither
normalizer is imported or run anywhere in the candidate / sampling / gold steps of this script (only `--stage build`
imports them at the very end, to record their outputs next to the already-fixed gold).

Sources (real text only; no invented spelling variants as the tested real strings):
  (a) rd_answer : dose mentions as actually written in the real-dose LLM answers
                  (results/journal2/real_dose/answers.jsonl; gpt-4o-mini & gemma-3-27b, grounded & closed-book), paired
                  with the FDA-label excerpt of that question (results/journal2/real_dose/questions.jsonl) as evidence.
  (b) label     : dose mentions as written in openFDA label text (data/real_labels/labels.jsonl = the label cache of
                  scripts/journal2/rd_fetch_labels.py; dosage_and_administration + dosage_forms_and_strengths).
Drugs used as bases in data/journal2/unf_adversarial.jsonl are excluded (ADV_DRUGS), as are the 10 RD questions it
used and any mention string identical to an adversarial surface / span.

Procedure (seed 20261002):
  1. candidates: a generic number+unit pattern written for this script (NOT the normalizers' regexes) finds mention
     candidates; non-dose contexts (creatinine clearance, serum levels, body weight, %) are dropped by context rules;
     for (a) the mention's leading numeral must also occur in the excerpt (string match), so a supported pair is
     possible.  Each candidate gets surface-feature tags (own tagger) and a primary category.
  2. sampling: per source and category, candidates are ordered by a seeded shuffle (max 1 per answer / 2 per label
     drug in rank order) and taken in rank order until the category quota is met, skipping candidates the adjudicator
     marked EXCLUDE (reason recorded) -> the gold table decides only validity/gold, never which normalizer wins.
  3. gold: scripts/journal2/unf_heldout_gold.py holds the MANUAL per-mention gold (canonical quantity written by the
     adjudicator from the text; for (a) also the label mention it is supported by, or NOT_SUPPORTED).  AI-adjudicated
     (Grok Bot agent), to be spot-checked by a human.
  4. pairs ("like the adversarial set"):
       rd_answer: S = the real answer as written vs the real excerpt (natural respelling/conversion when the surfaces
                  differ), U = the same answer with only the mention's numerator unit swapped (mg<->mcg, g->mg, mL->L,
                  units/mEq->mg; spelling style kept), anchor = the answer with the mention replaced by the label's own
                  surface.  Answers whose mention is not supported by the excerpt are parse-only items.
       label    : evidence = the real label sentence window; S = that sentence with the mention replaced by a correct
                  conversion in plain style (mass mg<->g/mcg, volume mL<->L; units/mEq/mmol: plain restatement), U = the
                  sentence with the label numeral and a swapped numerator unit, anchor = the sentence verbatim.
     Gold of S/U/anchor claims is derived from the mention gold by the stated conversion factor (exact Decimal).
Outputs: data/journal2/unf_heldout.jsonl, results/journal2/unf_heldout/{candidates.jsonl,build_manifest.json}
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
ANS = ROOT / "results/journal2/real_dose/answers.jsonl"
RDQ = ROOT / "results/journal2/real_dose/questions.jsonl"
LABELS = ROOT / "data/real_labels/labels.jsonl"
ADV = ROOT / "data/journal2/unf_adversarial.jsonl"
OUT = ROOT / "data/journal2/unf_heldout.jsonl"
RES = ROOT / "results/journal2/unf_heldout"
SEED = 20261002
D = Decimal

ADV_DRUGS = {"acyclovir", "adalimumab", "allopurinol", "atorvastatin", "azathioprine", "azithromycin", "baclofen",
             "cefazolin", "clarithromycin", "clonidine", "cyclosporine", "dexamethasone", "folic", "gabapentin", "glyburide",
             "levothyroxine", "methotrexate", "methylprednisolone", "mycophenolate", "naloxone", "octreotide", "penicillin",
             "phenytoin", "prednisone", "sitagliptin", "valacyclovir", "bupivacaine", "aspirin", "erythromycin",
             "etanercept", "tranexamic", "rifabutin", "meperidine", "nalbuphine", "desmopressin",
             "sodium"}  # "sodium" = levothyroxine sodium label

# ---------------------------------------------------------------- 1. candidates (own pattern, not the normalizers')
_N = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+"
_U = (r"(?:micrograms?|mcg|µg|μg|ug|milligrams?|mg|grams?|gm|g|nanograms?|ng|milliliters?|millilitres?|mL|ml|cc|"
      r"liters?|litres?|L|international units|units?|Units|UNITS|IU|U|mEq|mmol|million units)")
_DEN = (r"(?:\s*(?:/|per)\s*(?:kg|kilogram|m2|m 2|m²|m\^2|square meter|day|d|dose|min|minute|hour|hr|h|week|mL|L|"
        r"24 hours|24 h)\b)*(?:\s+(?:of\s+)?body\s*weight)?")
MENT = re.compile(rf"(?<![\w.,/])(?:{_N})(?:\s*(?:-|–|to)\s*(?:{_N}))?\s*-?{_U}(?![A-Za-z]){_DEN}")
NONDOSE = re.compile(r"(?:CrCl|creatinine|clearance|GFR|eGFR|serum|plasma|trough|peak|level|weigh|body weight of|"
                     r"concentrations? (?:of|above|below)|%|kg or more|kg and|less than \d+ kg)", re.I)
CATS = ["per_m2", "units", "meq", "micro", "thousands", "spelled", "rate", "per_kg_day", "per_kg", "range", "gram",
        "volume", "conc", "decimal", "plain"]


def feats(s: str) -> list:
    f = []
    if re.search(r"m2|m 2|m²|m\^2|square", s): f.append("per_m2")
    if re.search(r"\bunits?\b|Units|UNITS|\bIU\b|\bU\b", s): f.append("units")
    if re.search(r"mEq|mmol", s): f.append("meq")
    if re.search(r"mcg|µg|μg|\bug\b|microgram", s): f.append("micro")
    if re.search(r"\d,\d{3}", s): f.append("thousands")
    if re.search(r"milligram|microgram|kilogram|gram|liter|litre|per |body", s): f.append("spelled")
    if re.search(r"(?:/|per )\s*(?:min|minute|hour|hr|h)\b", s): f.append("rate")
    if re.search(r"kg|kilogram", s) and re.search(r"(?:/|per )\s*(?:day|d|24)", s): f.append("per_kg_day")
    if re.search(r"kg|kilogram", s): f.append("per_kg")
    if re.search(r"\d\s*(?:-|–|to)\s*[\d.]", s): f.append("range")
    if re.search(r"\b(?:g|gm|grams?)\b", s): f.append("gram")
    if re.search(r"\b(?:mL|ml|cc|L|liters?|litres?|milliliters?)\b", s) and not re.search(r"/\s*(?:mL|L)\b", s): f.append("volume")
    if re.search(r"/\s*(?:mL|L)\b", s): f.append("conc")
    if re.search(r"\d\.\d|(?<!\d)\.\d", s): f.append("decimal")
    return f or ["plain"]


def primary(fs: list) -> str:
    return next(c for c in CATS if c in fs or c == "plain")


def sent_window(text: str, a: int, b: int, maxc: int = 420) -> tuple:
    """Sentence containing [a,b) (split on '. ' / '; ' heuristics), widened to neighbours up to maxc chars."""
    starts = [0] + [m.end() for m in re.finditer(r"(?<=[.;])\s+(?=[A-Z(•])", text)]
    s0 = max(x for x in starts if x <= a)
    ends = [m.start() + 1 for m in re.finditer(r"[.;](?=\s+[A-Z(•]|\s*$)", text)] + [len(text)]
    e0 = min(x for x in ends if x >= b)
    if e0 - s0 > maxc:  # long run-on: clip around the mention
        s0, e0 = max(s0, a - maxc // 2), min(e0, b + maxc // 2)
        while s0 > 0 and text[s0 - 1] not in " ": s0 -= 1
        while e0 < len(text) and text[e0] not in " ": e0 += 1
    return s0, e0


def adv_strings() -> set:
    out = set()
    for r in (json.loads(l) for l in ADV.open(encoding="utf-8")):
        for k in ("surface", "core", "evidence_span"):
            if r.get(k):
                out.add(r[k].strip())
    return out


def candidates() -> list:
    advs = adv_strings()
    qs = {q["qid"]: q for q in (json.loads(l) for l in RDQ.open(encoding="utf-8"))}
    adv_qids = {r["base_id"] for r in (json.loads(l) for l in ADV.open(encoding="utf-8")) if r["base_id"].startswith("RD_")}
    out = []
    for a in (json.loads(l) for l in ANS.open(encoding="utf-8")):
        if a["drug"] in ADV_DRUGS or a["qid"] in adv_qids:
            continue
        txt, ex = a["answer"] or "", qs[a["qid"]]["excerpt"]
        exn = ex.replace(",", "")
        for m in MENT.finditer(txt):
            s = m.group(0).rstrip()
            if NONDOSE.search(txt[max(0, m.start() - 45):m.end() + 12]) or s in advs or re.search(r"mL/min|/\s*L\b", s):
                continue
            n0 = re.match(_N, s).group(0).replace(",", "")
            if not re.search(r"(?<![\d.])" + re.escape(n0) + r"(?![\d])", exn):
                continue
            fs = feats(s)
            out.append({"cid": "A:%s:%s:%s:%d" % (a["qid"], a["generator"], a["condition"], m.start()), "source": "rd_answer",
                        "drug": a["drug"], "qid": a["qid"], "generator": a["generator"], "mode": a["condition"],
                        "unit_id": "%s|%s|%s" % (a["qid"], a["generator"], a["condition"]), "text": txt, "start": m.start(),
                        "end": m.start() + len(s), "mention": s, "feats": fs, "cat": primary(fs)})
    # (a') closed-book answers WITHOUT the excerpt-numeral requirement: parse-only realism stratum
    for a in (json.loads(l) for l in ANS.open(encoding="utf-8")):
        if a["drug"] in ADV_DRUGS or a["qid"] in adv_qids or a["condition"] != "closed":
            continue
        txt = a["answer"] or ""
        for m in MENT.finditer(txt):
            s = m.group(0).rstrip()
            if NONDOSE.search(txt[max(0, m.start() - 45):m.end() + 12]) or re.search(r"mL/min|/\s*L\b", s):
                continue
            fs = feats(s)
            out.append({"cid": "F:%s:%s:%d" % (a["qid"], a["generator"], m.start()), "source": "rd_answer_free",
                        "drug": a["drug"], "qid": a["qid"], "generator": a["generator"], "mode": a["condition"],
                        "unit_id": a["drug"], "text": txt, "start": m.start(), "end": m.start() + len(s), "mention": s,
                        "feats": fs, "cat": "any"})
    for lab in (json.loads(l) for l in LABELS.open(encoding="utf-8")):
        if lab["drug"] in ADV_DRUGS:
            continue
        for field in ("dosage_and_administration", "dosage_forms_and_strengths"):
            txt = lab.get(field) or ""
            for m in MENT.finditer(txt):
                s = m.group(0).rstrip()
                if NONDOSE.search(txt[max(0, m.start() - 45):m.end() + 12]) or s in advs or re.search(r"mL/min", s):
                    continue
                w0, w1 = sent_window(txt, m.start(), m.start() + len(s))
                fs = feats(s)
                out.append({"cid": "L:%s:%s:%d" % (lab["drug"], "DA" if field.startswith("dosage_and") else "DF", m.start()), "source": "label", "drug": lab["drug"],
                            "field": field, "set_id": lab.get("set_id"), "unit_id": lab["drug"], "text": txt[w0:w1],
                            "start": m.start() - w0, "end": m.start() - w0 + len(s), "mention": s, "feats": fs, "cat": primary(fs)})
    return out


QUOTA = {"rd_answer": {"per_m2": 3, "units": 4, "meq": 4, "micro": 7, "thousands": 5, "spelled": 8, "rate": 3,
                       "per_kg_day": 4, "per_kg": 5, "range": 5, "gram": 4, "volume": 2, "conc": 0, "decimal": 3, "plain": 6},
         "label": {"per_m2": 6, "units": 7, "meq": 5, "micro": 10, "thousands": 6, "spelled": 8, "rate": 6, "per_kg_day": 6,
                   "per_kg": 9, "range": 10, "gram": 8, "volume": 5, "conc": 4, "decimal": 7, "plain": 7},
         "rd_answer_free": {"any": 30}}
PER_UNIT_CAP = {"rd_answer": 1, "label": 2, "rd_answer_free": 1}
SOURCES = ("rd_answer", "label", "rd_answer_free")


def ranked(cands: list) -> dict:
    """source -> cat -> candidates in seeded rank order (cap per answer / label drug applied in rank order)."""
    rng = random.Random(SEED)
    out = {}
    for src in SOURCES:
        pool = sorted([c for c in cands if c["source"] == src], key=lambda c: c["cid"])
        rng.shuffle(pool)
        by = defaultdict(list)
        for c in pool:
            by[c["cat"]].append(c)
        out[src] = by
    return out


def select(cands: list, gold: dict, excl: dict, peek: int = 0) -> tuple:
    """Take candidates in rank order per (source, cat) until quota met; skip EXCLUDE-marked; returns (taken, missing_gold)."""
    R = ranked(cands)
    taken, missing, used = [], [], Counter()
    for src in SOURCES:
        for cat in (CATS if src != "rd_answer_free" else ["any"]):
            k = 0
            for c in R[src].get(cat, []):
                if k >= QUOTA[src].get(cat, 0) + peek:
                    break
                if used[(src, c["unit_id"])] >= PER_UNIT_CAP[src]:
                    continue
                if c["cid"] in excl:
                    continue
                used[(src, c["unit_id"])] += 1
                if c["cid"] in gold:
                    if k < QUOTA[src].get(cat, 0):
                        taken.append(c)
                else:
                    missing.append(c)
                k += 1
    return taken, missing


# ---------------------------------------------------------------- 3. gold parsing (own tables, not the normalizers')
_GU = {"ng": ("mass", D("0.001")), "mcg": ("mass", D(1)), "mg": ("mass", D(1000)), "g": ("mass", D(1000000)),
       "mL": ("volume", D(1)), "L": ("volume", D(1000)), "units": ("units", D(1)), "mEq": ("meq", D(1)),
       "mmol": ("mmol", D(1))}
_GT = {"min": D(1440), "h": D(24), "day": D(1), "week": D(1) / D(7)}


def fmtd(v: Decimal) -> str:
    t = format(v.normalize(), "f")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return "0" if t in ("", "-0") else t


def parse_gold(g: str) -> dict:
    """'0.05-2 mcg/kg/min' -> {'key': 'mass|/kg|||/day', 'lo': '72', 'hi': '2880', 'unit': 'mcg', 'den': [...], ...}
    (key/base units in the format of the paper's canonical quantity: mass mcg, volume mL; time -> /day)."""
    num, unit = g.split(" ", 1)
    lo, _, hi = num.partition("-")
    parts = unit.split("/")
    kind, f = _GU[parts[0]]
    kg = m2 = conc = t = ""
    mult = f
    for p in parts[1:]:
        if p == "kg":
            kg = "/kg"
        elif p == "m2":
            m2 = "/m2"
        elif p in ("mL", "L"):
            conc = "/" + p
        elif p in _GT:
            t, mult = "/day", mult * _GT[p]
        elif p == "dose":
            t = "/dose"
        else:
            raise ValueError("bad gold denominator %r in %r" % (p, g))
    return {"key": "%s|%s|%s|%s|%s" % (kind, kg, m2, conc, t), "lo": fmtd(D(lo) * mult),
            "hi": fmtd(D(hi) * mult) if hi else None, "unit": parts[0], "den": parts[1:], "lo_raw": lo, "hi_raw": hi or None,
            "gold_str": g}


# derived claims: correct conversion (S, label source) and wrong-unit swap (U)
_CONV = {"mg": ("g", D("0.001")), "mcg": ("mg", D("0.001")), "g": ("mg", D(1000)), "L": ("mL", D(1000))}
_SWAP_UNIT = {"mg": "mcg", "mcg": "mg", "g": "mg", "mL": "L", "L": "mL", "units": "mg", "mEq": "mg", "mmol": "mg", "ng": "mg"}
_DEN_TXT = {"kg": "/kg", "m2": "/m2", "mL": "/mL", "L": "/L", "min": "/min", "h": "/h", "day": "/day", "week": "/week", "dose": "/dose"}


def render(lo: str, hi, unit: str, den: list) -> str:
    num = lo if not hi else "%s to %s" % (lo, hi)
    return "%s %s%s" % (num, unit, "".join(_DEN_TXT[d] for d in den))


def gold_str(lo: str, hi, unit: str, den: list) -> str:
    return "%s%s %s%s" % (lo, "-" + hi if hi else "", unit, "".join("/" + d for d in den))


def conversion(G: dict) -> tuple:
    """Correct conversion of the label quantity into plain text (S claim for label items) -> (text, gold string)."""
    u, den, lo, hi = G["unit"], G["den"], D(G["lo_raw"]), D(G["hi_raw"]) if G["hi_raw"] else None
    if u == "mg":
        nu, f = ("g", D("0.001")) if lo >= 100 else ("mcg", D(1000))
    elif u == "mL":
        if lo >= 100:
            nu, f = "L", D("0.001")
        else:
            return render(fmtd(lo), fmtd(hi) if hi else None, "cc", den), gold_str(fmtd(lo), fmtd(hi) if hi else None, "mL", den)
    elif u in _CONV:
        nu, f = _CONV[u]
    else:  # units / mEq / mmol: no mass conversion exists -> plain restatement with a standard alternative spelling
        alt = {"units": "IU", "mEq": "milliequivalents", "mmol": "millimoles"}[u]
        return render(fmtd(lo), fmtd(hi) if hi else None, alt, den), gold_str(fmtd(lo), fmtd(hi) if hi else None, u, den)
    nlo, nhi = fmtd(lo * f), (fmtd(hi * f) if hi else None)
    return render(nlo, nhi, nu, den), gold_str(nlo, nhi, nu, den)


def swap_plain(G: dict) -> tuple:
    """Wrong-unit swap with the label numeral(s), plain text (U claim for label items)."""
    u = _SWAP_UNIT[G["unit"]]
    lo, hi = fmtd(D(G["lo_raw"])), (fmtd(D(G["hi_raw"])) if G["hi_raw"] else None)
    return render(lo, hi, u, G["den"]), gold_str(lo, hi, u, G["den"])


_SWAP_TOKENS = [  # (surface unit token right after a number, replacement) -- spelling style kept
    (r"milligrams", "micrograms"), (r"milligram", "microgram"), (r"micrograms", "milligrams"), (r"microgram", "milligram"),
    (r"grams", "milligrams"), (r"gram", "milligram"), (r"mcg|µg|μg", "mg"), (r"mg", "mcg"), (r"g", "mg"),
    (r"mL", "L"), (r"units?", "mg"), (r"mEq", "mg")]


def swap_surface(m: str) -> str:
    """Swap the numerator unit after every number in a real mention ('40 mg per kg to 50 mg per kg' -> mcg both ends)."""
    alt = "|".join("(?:%s)" % p for p, _ in _SWAP_TOKENS)

    def rep(x):
        tok = x.group(2)
        for p, r in _SWAP_TOKENS:
            if re.fullmatch(p, tok):
                return x.group(1) + r
        return x.group(0)
    out = re.sub(r"(\d\s*)(%s)(?![A-Za-z])" % alt, rep, m)
    if out == m:
        raise ValueError("no unit swapped in %r" % m)
    return out


def find_cover(text: str, m: str, pos: int) -> int:
    """Start of the occurrence of m in text that covers char position pos."""
    for x in re.finditer(re.escape(m), text):
        if x.start() <= pos < x.end():
            return x.start()
    raise ValueError("mention %r does not cover position %d in %r" % (m, pos, text[:120]))


def find_occ(text: str, m: str, occ: int) -> int:
    hits = [x.start() for x in re.finditer(r"(?<![\d.,])" + re.escape(m) + r"(?![0-9A-Za-z])", text)]
    if len(hits) <= occ:
        raise ValueError("label mention %r (occ %d) not in excerpt" % (m, occ))
    return hits[occ]


def build_items(taken: list, gold: dict) -> list:
    qs = {q["qid"]: q for q in (json.loads(l) for l in RDQ.open(encoding="utf-8"))}
    items = []

    def add(**kw):
        items.append(kw)
    for c in taken:
        gd = gold[c["cid"]]
        G = parse_gold(gd["g"])
        txt = c["text"]
        a = find_cover(txt, gd["m"], c["start"])
        b = a + len(gd["m"])
        common = dict(cid=c["cid"], source=c["source"], drug=c["drug"], base_id=c["drug"], cat=c["cat"], feats=c["feats"],
                      mention=gd["m"], mention_gold=gd["g"], note=gd.get("note", ""), generator=c.get("generator"),
                      mode=c.get("mode"), qid=c.get("qid"), field=c.get("field"))
        if c["source"] in ("rd_answer", "rd_answer_free"):
            ex = qs[c["qid"]]["excerpt"]
            if c["source"] == "rd_answer" and gd.get("lab"):
                la = find_occ(ex, gd["lab"], gd.get("occ", 0))
                lg = parse_gold(gd.get("lg") or gd["g"])
                ev = dict(evidence=ex, evidence_span=gd["lab"], ev_start=la, ev_end=la + len(gd["lab"]), ev_gold=lg,
                          ev_real=True)
                add(family="S", label="SUPPORTED", claim=txt, surface_start=a, surface_end=b, gold=G, claim_real=True,
                    variant="as written (natural %s)" % ("respelling/conversion" if gd["m"] != gd["lab"] else "identical surface"),
                    **ev, **common)
                u = swap_surface(gd["m"])
                ug = parse_gold(gold_str(G["lo_raw"], G["hi_raw"], _SWAP_UNIT[G["unit"]], G["den"]))
                add(family="U", label="UNSUPPORTED", claim=txt[:a] + u + txt[b:], surface_start=a, surface_end=a + len(u),
                    gold=ug, claim_real=False, variant="unit swap %s -> %s" % (gd["m"], u), **ev, **common)
                add(family="anchor", label="SUPPORTED", claim=txt[:a] + gd["lab"] + txt[b:], surface_start=a,
                    surface_end=a + len(gd["lab"]), gold=lg, claim_real=False, variant="label surface", **ev, **common)
            else:
                add(family="parse_only", label="NA", claim=txt, surface_start=a, surface_end=b, gold=G, claim_real=True,
                    variant="as written", evidence=ex, evidence_span=None, ev_start=None, ev_end=None, ev_gold=None,
                    ev_real=False, **common)
        else:  # label
            ev = dict(evidence=txt, evidence_span=gd["m"], ev_start=a, ev_end=b, ev_gold=G, ev_real=True)
            s_txt, s_g = conversion(G)
            u_txt, u_g = swap_plain(G)
            add(family="S", label="SUPPORTED", claim=txt[:a] + s_txt + txt[b:], surface_start=a, surface_end=a + len(s_txt),
                gold=parse_gold(s_g), claim_real=False, variant="conversion %s -> %s" % (gd["m"], s_txt), **ev, **common)
            add(family="U", label="UNSUPPORTED", claim=txt[:a] + u_txt + txt[b:], surface_start=a, surface_end=a + len(u_txt),
                gold=parse_gold(u_g), claim_real=False, variant="unit swap %s -> %s" % (gd["m"], u_txt), **ev, **common)
            add(family="anchor", label="SUPPORTED", claim=txt, surface_start=a, surface_end=b, gold=G, claim_real=True,
                variant="label sentence verbatim", **ev, **common)
    for i, it in enumerate(items):
        it["instance_id"] = "UNFHO%04d__%s__%s" % (i, it["drug"], {"S": "S", "U": "U", "anchor": "A", "parse_only": "P"}[it["family"]])
        it["expected_verdict"] = {"SUPPORTED": "PASS", "UNSUPPORTED": "FAIL"}.get(it["label"])
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["candidates", "build"], default="build")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    import unf_heldout_gold as GOLD  # noqa: E402  (manual gold; no normalizer involved)
    cands = candidates()
    RES.mkdir(parents=True, exist_ok=True)
    with (RES / "candidates.jsonl").open("w", encoding="utf-8") as fh:
        for c in cands:
            fh.write(json.dumps({k: v for k, v in c.items() if k != "text"}, ensure_ascii=False) + "\n")
    taken, missing = select(cands, GOLD.GOLD, GOLD.EXCLUDE)
    if args.stage == "candidates" or missing:
        print(json.dumps({"candidates": len(cands), "taken": len(taken), "missing_gold": [m["cid"] for m in missing]}, indent=1))
        if missing:
            raise SystemExit("adjudicate the missing candidates in scripts/journal2/unf_heldout_gold.py first")
        return
    items = build_items(taken, GOLD.GOLD)
    # ---- only now: run the two normalizers next to the fixed gold (records outputs; gold is never changed here)
    sys.path.insert(0, str(ROOT / "src"))
    import unit_norm_fix as V1  # noqa: E402
    import unit_norm_fix_v2 as V2  # noqa: E402
    from unf_adv_build import pair_eval, parse_eval  # noqa: E402  (same scoring rules as the adversarial set)
    rows = []
    for it in items:
        g = {k: it["gold"][k] for k in ("key", "lo", "hi")}
        probe = {"claim": it["claim"], "surface_start": it["surface_start"], "surface_end": it["surface_end"],
                 "core_start": it["surface_start"], "core_end": it["surface_end"], "gold": g}
        r = dict(it, gold=g, gold_str=it["gold"]["gold_str"])
        if it["ev_gold"] is not None:
            r["ev_gold"] = {k: it["ev_gold"][k] for k in ("key", "lo", "hi")}
            r["ev_gold_str"] = it["ev_gold"]["gold_str"]
            eprobe = {"claim": it["evidence"], "surface_start": it["ev_start"], "surface_end": it["ev_end"],
                      "core_start": it["ev_start"], "core_end": it["ev_end"], "gold": r["ev_gold"]}
        for v, mod in (("v1", V1), ("v2", V2)):
            p = parse_eval(probe, mod)
            r[v + "_parse_ok"], r[v + "_parse_why"], r[v + "_spans"] = p["ok"], p["why"], p["spans"]
            if it["ev_gold"] is not None:
                pe = parse_eval(eprobe, mod)
                r[v + "_ev_parse_ok"], r[v + "_ev_parse_why"] = pe["ok"], pe["why"]
            if it["family"] in ("S", "U", "anchor"):
                q = pair_eval({"claim": it["claim"], "evidence": it["evidence"], "evidence_span": it["evidence_span"],
                               "label": it["label"]}, mod, p["ok"])
                r[v + "_pair_ok"] = q["ok"]
                r["claim_unf" + ("" if v == "v1" else "_v2")] = q["claim_norm"]
                r["evidence_unf" + ("" if v == "v1" else "_v2")] = q["evidence_norm"]
        r.update(type="DOSE", condition="UNFHO-" + it["family"], valid=True)
        rows.append(r)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    pairs = [r for r in rows if r["family"] in ("S", "U")]
    man = {"built_after_freeze": json.loads((ROOT / "results/journal2/unf_v2_freeze.json").read_text())["sha256"],
           "seed": SEED, "candidates": len(cands), "candidates_by_source": dict(Counter(c["source"] for c in cands)),
           "sampled_mentions": len(taken), "sampled_by_source": dict(Counter(c["source"] for c in taken)),
           "sampled_by_source_cat": {s: dict(Counter(c["cat"] for c in taken if c["source"] == s)) for s in SOURCES},
           "excluded_candidates": GOLD.EXCLUDE, "rows": len(rows), "rows_by_family": dict(Counter(r["family"] for r in rows)),
           "test_claims_S_U": len(pairs), "anchors": sum(1 for r in rows if r["family"] == "anchor"),
           "parse_only": sum(1 for r in rows if r["family"] == "parse_only"),
           "drugs": len({r["drug"] for r in rows}), "drugs_in_pairs": len({r["drug"] for r in pairs}),
           "rd_answer_not_supported": sorted(c["cid"] for c in taken if c["source"] == "rd_answer" and not GOLD.GOLD[c["cid"]].get("lab")),
           "unused_gold_entries": sorted(set(GOLD.GOLD) - {c["cid"] for c in taken})}
    (RES / "build_manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in man.items() if k not in ("excluded_candidates",)}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
