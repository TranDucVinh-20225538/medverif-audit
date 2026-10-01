#!/usr/bin/env python3
"""(UNF-ADV-1) Adversarial unit-spelling test set for the unit-normalization fix (stdlib, deterministic, no models).

Each item = (claim, evidence) where the evidence is an EXISTING base: a C0 row of the UNF cohort
(data/journal2/unf/cohort_orig.jsonl, i.e. the paper's main DOSE bases) or, for quantity kinds the cohort lacks
(mg/m2, units, mg/kg/day, plain ranges), an FDA-label excerpt from the real-dose questions
(results/journal2/real_dose/questions.jsonl) with a template claim.  The claim's dose span (C0: claim_span) is
replaced by a real-world surface variant of
  SUPPORTED   the same quantity (respelling or correct conversion)            -> expected PASS
  UNSUPPORTED a wrong-unit swap (same numeral style, other unit/basis)       -> expected FAIL
Families: micro (mcg/µg/μg/ug/microgram(s)/micro-gram), milligram, gram, per_kg, per_kg_day, per_m2, units (IU),
volume (mL/ml/cc/L), spacing, number_format (0.5/.5/1,000/1 000/0,5), range, fraction, words, uppercase,
punctuation, basis_drop (unsupported only).  Every base also gets an `anchor` row (base claim, original spelling,
expected PASS) so checker metrics can be made anchor(C0)-conditional.

Gold = canonical quantity in the format of unit_norm_fix.canonical_quantity: key "kind|/kg|/m2|conc|time"
(time -> /day), value in kind base units (mass mcg, volume mL, units), computed HERE from the structured recipe,
independently of the normalizer.

Output: data/journal2/unf_adversarial.jsonl (one row per item with orig, UNF-v1 and UNF-v2(post-hoc) texts),
        results/journal2/unf_adv/build_manifest.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import unit_norm_fix as V1  # noqa: E402
import unit_norm_fix_v2 as V2  # noqa: E402

COHORT = ROOT / "data/journal2/unf/cohort_orig.jsonl"
RDQ = ROOT / "results/journal2/real_dose/questions.jsonl"
OUT = ROOT / "data/journal2/unf_adversarial.jsonl"
RES = ROOT / "results/journal2/unf_adv"
D = Decimal
FACT = {"mcg": D(1), "mg": D(1000), "g": D(1000000), "mL": D(1), "L": D(1000), "units": D(1)}
KIND = {"mcg": "mass", "mg": "mass", "g": "mass", "mL": "volume", "L": "volume", "units": "units"}

# ---- bases: id -> (source, evidence span text, unit, lo, hi, kg, m2, day)
C0_BASES = {
    "D0015": ("mg", "0.1"), "D0030": ("mg", "2"), "D0052": ("mg", "1"), "D0082": ("mg", "1.8"), "D0133": ("mg", "0.4"),
    "D0139": ("mg", "0.3"), "D0140": ("mg", "0.025"), "D0112": ("mg", "4"), "D0126": ("mg", "5"), "D0088": ("mg", "2"),
    "D0003": ("mg", "40"), "D0004": ("mg", "200"), "D0013": ("mg", "250"), "D0016": ("mg", "500"), "D0032": ("mg", "500"),
    "D0017": ("mg", "150"), "D0025": ("mg", "300"), "D0038": ("mg", "600"), "D0099": ("mg", "1200"), "D0071": ("mg", "81"),
    "D0058": ("mg", "10"), "D0117": ("mg", "20"), "D0120": ("mg", "25"), "D0122": ("mg", "15"), "D0005": ("mg", "50"),
    "D0048": ("mg", "100"), "D0148": ("mg", "250"), "D0036": ("mg", "500"),
    "D0031": ("mcg", "1"), "D0044": ("mcg", "50"), "D0053": ("mcg", "50"), "D0118": ("mcg", "250"), "D0141": ("mcg", "20"),
    "D0062": ("mcg", "200"),
    "D0009": ("g", "2"), "D0063": ("g", "1"), "D0119": ("g", "1"),
    "D0002": ("mg/kg", "1"), "D0007": ("mg/kg", "25"), "D0033": ("mg/kg", "5"), "D0039": ("mg/kg", "8"),
    "D0040": ("mg/kg", "20"), "D0049": ("mg/kg", "0.1"), "D0051": ("mg/kg", "15"), "D0083": ("mg/kg", "0.5"),
    "D0102": ("mg/kg", "2"), "D0155": ("mg/kg", "3"),
    "D0147": ("mg/kg/day", "1"), "D0175": ("mg/kg/day", "90"),
    "D0008": ("mL", "0.5"), "D0022": ("mL", "3"), "D0115": ("mL", "30"), "D0116": ("mL", "50"), "D0150": ("mL", "2"),
}
RD_BASES = {  # qid -> (evidence span as it appears in the label, unit spec, lo, hi)
    "RD_methotrexate_0": ("10 mg/m2", "mg/m2", "10", None), "RD_mycophenolate_1": ("600 mg/m2", "mg/m2", "600", None),
    "RD_glyburide_1": ("20 units", "units", "20", None), "RD_penicillin_0": ("200,000 to 400,000 units", "units", "200000", "400000"),
    "RD_cyclosporine_0": ("3 mg/kg/day", "mg/kg/day", "3", None), "RD_azithromycin_1": ("5 mg/kg/day", "mg/kg/day", "5", None),
    "RD_clarithromycin_0": ("15 mg/kg/day", "mg/kg/day", "15", None),
    "RD_atorvastatin_0": ("10 to 20 mg", "mg", "10", "20"), "RD_azathioprine_1": ("50 to 100 mg", "mg", "50", "100"),
    "RD_baclofen_0": ("40 to 80 mg", "mg", "40", "80"),
}


def spec(u: str):
    """'mg/kg/day' -> (numerator unit, kg, m2, day)."""
    parts = u.split("/")
    return parts[0], "kg" in parts[1:], "m2" in parts[1:], "day" in parts[1:]


def gold(unit: str, lo, hi=None, kg=False, m2=False, day=False) -> dict:
    f = FACT[unit]
    key = "%s|%s|%s||%s" % (KIND[unit], "/kg" if kg else "", "/m2" if m2 else "", "/day" if day else "")
    return {"key": key, "lo": V1.fmt(D(str(lo)) * f), "hi": V1.fmt(D(str(hi)) * f) if hi is not None else None}


def N(x) -> str:
    return V1.fmt(D(str(x)))


def commas(x) -> str:
    v = D(str(x))
    return "{:,}".format(int(v)) if v == v.to_integral() else "{:,}".format(v)


def load_bases() -> dict:
    rows = {r["base_id"]: r for r in (json.loads(l) for l in COHORT.open(encoding="utf-8")) if r["condition"] == "C0"}
    qs = {q["qid"]: q for q in (json.loads(l) for l in RDQ.open(encoding="utf-8"))}
    bases = {}
    for bid, (u, v) in C0_BASES.items():
        r = rows[bid]
        num, kg, m2, day = spec(u)
        assert r["claim_span"] in r["claim"] and r["evidence_span"] in r["evidence"], bid
        assert V1.canonical_quantity(r["evidence_span"])[1] == D(v) * FACT[num], (bid, r["evidence_span"])
        bases[bid] = {"base_id": bid, "source": "unf_cohort_C0", "claim": r["claim"], "claim_span": r["claim_span"],
                      "evidence": r["evidence"], "evidence_span": r["evidence_span"], "unit": num, "lo": v, "hi": None,
                      "kg": kg, "m2": m2, "day": day, "orig_instance_id": r["instance_id"]}
    for qid, (span, u, lo, hi) in RD_BASES.items():
        q = qs[qid]
        assert span in q["excerpt"], (qid, span)
        num, kg, m2, day = spec(u)
        claim = "The recommended dose of %s is %s." % (q["drug"], span)
        bases[qid] = {"base_id": qid, "source": "real_dose_label_excerpt(template claim)", "claim": claim, "claim_span": span,
                      "evidence": q["excerpt"], "evidence_span": span, "unit": num, "lo": lo, "hi": hi, "kg": kg, "m2": m2,
                      "day": day, "orig_instance_id": None}
    # sanity filter: the base's own claim span (canonical spelling, in its sentence context) must be parsed by v1 to
    # the gold quantity, so every variant failure is attributable to the variant, not to the base sentence
    # (drops e.g. claims where "per day" or "80 to" around the span changes the quantity).
    dropped = {}
    for bid, b in list(bases.items()):
        probe = {"claim": b["claim"], "core_start": b["claim"].index(b["claim_span"]),
                 "core_end": b["claim"].index(b["claim_span"]) + len(b["claim_span"]),
                 "gold": gold(b["unit"], b["lo"], b["hi"], b["kg"], b["m2"], b["day"])}
        r = parse_eval(probe, V1)
        if not r["ok"]:
            dropped[bid] = r["why"]
            del bases[bid]
    load_bases.dropped = dropped
    return bases


class Gen:
    def __init__(self, bases):
        self.b, self.items, self.cyc = bases, [], Counter()

    def pick(self, pool: list, k: int = 1) -> list:
        """deterministic round-robin over a pool so many bases are used."""
        out = []
        for _ in range(k):
            key = tuple(pool)
            out.append(pool[self.cyc[key] % len(pool)])
            self.cyc[key] += 1
        return out

    def add(self, fam, vid, bid, label, core, g, pre="", suf="", note=""):
        b = self.b[bid]
        surface = pre + core + suf
        i = b["claim"].index(b["claim_span"])
        claim = b["claim"][:i] + surface + b["claim"][i + len(b["claim_span"]):]
        cs = i + len(pre)
        self.items.append({"surface_start": i, "surface_end": i + len(surface), "family": fam, "variant": vid, "base_id": bid, "label": label,
                           "expected_verdict": "PASS" if label == "SUPPORTED" else "FAIL", "claim": claim,
                           "evidence": b["evidence"], "surface": surface, "core": core, "core_start": cs,
                           "core_end": cs + len(core), "gold": g, "evidence_span": b["evidence_span"], "note": note,
                           "base_source": b["source"]})

    def pair(self, fam, vid, bid, s_core, s_gold, u_core, u_gold, pre="", suf="", note=""):
        self.add(fam, vid, bid, "SUPPORTED", s_core, s_gold, pre, suf, note)
        self.add(fam, vid, bid, "UNSUPPORTED", u_core, u_gold, pre, suf, note)


def build(bases) -> list:
    G = Gen(bases)
    B = bases
    _pick = G.pick
    G.pick = lambda pool, k=1: _pick([b for b in pool if b in B], k)  # noqa: E731  (filtered pools)
    mg_small = ["D0015", "D0030", "D0052", "D0082", "D0133", "D0139", "D0140", "D0112", "D0126", "D0088"]
    mg_mid = ["D0003", "D0004", "D0013", "D0016", "D0017", "D0025", "D0038", "D0071", "D0058", "D0117", "D0120", "D0122",
              "D0005", "D0048"]
    mg_k = ["D0004", "D0013", "D0016", "D0025", "D0038", "D0099", "D0148", "D0036", "D0032", "D0017"]  # >=100 mg
    mcg_b = ["D0031", "D0044", "D0053", "D0118", "D0141", "D0062"]
    kg_b = ["D0002", "D0007", "D0033", "D0039", "D0040", "D0049", "D0051", "D0083", "D0102", "D0155"]
    kgd_b = ["D0147", "D0175", "RD_cyclosporine_0", "RD_azithromycin_1", "RD_clarithromycin_0"]
    m2_b = ["RD_methotrexate_0", "RD_mycophenolate_1"]
    ml_b = ["D0008", "D0022", "D0115", "D0116", "D0150"]
    rng_b = ["RD_atorvastatin_0", "RD_azathioprine_1", "RD_baclofen_0"]
    v = lambda bid: D(B[bid]["lo"])  # noqa: E731
    # micro: mg base -> converted to mcg (S) vs same numeral in mcg (U, 1000x low)
    for alias in ["mcg", "µg", "μg", "ug", "microgram", "micrograms", "micro-gram", "micro-grams", "mcgs", "MCG", "Mcg"]:
        (bid,) = G.pick(mg_small)
        G.pair("micro", alias, bid, "%s %s" % (N(v(bid) * 1000), alias), gold("mcg", v(bid) * 1000),
               "%s %s" % (N(v(bid)), alias), gold("mcg", v(bid)), note="mg evidence, mcg claim")
    # micro respelling: mcg base, same numeral, other micro spelling (S) vs milligram counterpart (U)
    for alias, swap in [("µg", "mg"), ("μg", "mg"), ("ug", "mg"), ("micrograms", "milligrams"), ("micro-gram", "milli-gram"),
                        ("mcg", "mg")]:
        (bid,) = G.pick(mcg_b)
        G.pair("micro", "respell:" + alias, bid, "%s %s" % (N(v(bid)), alias), gold("mcg", v(bid)),
               "%s %s" % (N(v(bid)), swap), gold("mg", v(bid)), note="mcg evidence")
    # milligram spellings (S) vs gram counterpart (U)
    for alias, swap in [("milligram", "gram"), ("milligrams", "grams"), ("mgs", "gms"), ("MG", "MCG"), ("Mg", "Mcg"),
                        ("milligramme", "gramme"), ("milli-grams", "micro-grams"), ("mg", "g")]:
        (bid,) = G.pick(mg_mid)
        G.pair("milligram", alias, bid, "%s %s" % (N(v(bid)), alias), gold("mg", v(bid)), "%s %s" % (N(v(bid)), swap),
               gold({"gram": "g", "grams": "g", "gms": "g", "MCG": "mcg", "Mcg": "mcg", "gramme": "g", "micro-grams": "mcg",
                     "g": "g"}[swap], v(bid)))
    # gram spellings: mg base >= 100 -> converted to g (S) vs same numeral in g (U, 1000x high)
    for alias in ["g", "gm", "gram", "grams", "gms", "Grams", "G"]:
        (bid,) = G.pick(mg_k)
        G.pair("gram", alias, bid, "%s %s" % (N(v(bid) / 1000), alias), gold("g", v(bid) / 1000), "%s %s" % (N(v(bid)), alias),
               gold("g", v(bid)), note="capital G is excluded by design in v1" if alias == "G" else "")
    for bid in ["D0009", "D0063"]:  # g base -> mg conversion
        G.pair("gram", "g->mg", bid, "%s mg" % N(v(bid) * 1000), gold("mg", v(bid) * 1000), "%s mg" % N(v(bid)), gold("mg", v(bid)))
    # per kg forms: S same quantity, U the same form with mcg (1000x low)
    for form in ["mg/kg", "mg per kg", "mg/kg body weight", "mg per kilogram", "mg/kg of body weight", "mg per kg body weight",
                 "mg kg-1", "mg·kg⁻¹", "mg/Kg", "mg/KG"]:
        (bid,) = G.pick(kg_b)
        G.pair("per_kg", form, bid, "%s %s" % (N(v(bid)), form), gold("mg", v(bid), kg=True),
               "%s %s" % (N(v(bid)), form.replace("mg", "mcg", 1)), gold("mcg", v(bid), kg=True))
    (bid,) = G.pick(kg_b)
    G.pair("per_kg", "mcg/kg conversion", bid, "%s mcg/kg" % N(v(bid) * 1000), gold("mcg", v(bid) * 1000, kg=True),
           "%s mcg/kg" % N(v(bid)), gold("mcg", v(bid), kg=True))
    # per kg per day forms
    for form in ["mg/kg/day", "mg/kg per day", "mg per kg per day", "mg/kg/d", "mg/kg/24 h", "mg/kg/24 hours", "mg/kg daily",
                 "mg/kg a day"]:
        (bid,) = G.pick(kgd_b)
        G.pair("per_kg_day", form, bid, "%s %s" % (N(v(bid)), form), gold("mg", v(bid), kg=True, day=True),
               "%s %s" % (N(v(bid)), form.replace("mg", "g", 1)), gold("g", v(bid), kg=True, day=True))
    # per m2 forms
    for form in ["mg/m2", "mg/m²", "mg/m^2", "mg per square meter", "mg per square metre", "mg/m 2", "mg per m2", "mg/sq m",
                 "mg/M2", "mg m-2"]:
        (bid,) = G.pick(m2_b)
        G.pair("per_m2", form, bid, "%s %s" % (N(v(bid)), form), gold("mg", v(bid), m2=True),
               "%s %s" % (N(v(bid)), form.replace("mg", "g", 1)), gold("g", v(bid), m2=True))
    # units / IU (S) vs unit-kind swap to mass (U)
    for form, swap in [("units", "mg"), ("IU", "mg"), ("international units", "milligrams"), ("International Units", "mg"),
                       ("U", "mcg"), ("Units", "mg"), ("UNITS", "MG"), ("I.U.", "mg"), ("unit", "mg")]:
        bid = "RD_glyburide_1" if form != "unit" else "RD_glyburide_1"
        G.pair("units", form, bid, "%s %s" % (N(v(bid)), form), gold("units", v(bid)), "%s %s" % (N(v(bid)), swap),
               gold({"mg": "mg", "milligrams": "mg", "mcg": "mcg", "MG": "mg"}[swap], v(bid)),
               note="U swap = units->mass (no factor exists; must not match)")
    bid = "RD_penicillin_0"
    for form in ["units", "IU", "International Units"]:
        G.pair("units", "range:" + form, bid, "200,000 to 400,000 %s" % form, gold("units", 200000, 400000),
               "200,000 to 400,000 mg" if form != "IU" else "200,000 to 400,000 mcg",
               gold("mg" if form != "IU" else "mcg", 200000, 400000))
    # volume
    for form, swap in [("mL", "L"), ("ml", "l"), ("cc", "L"), ("ML", "L"), ("mls", "liters"), ("milliliters", "liters"),
                       ("millilitres", "litres"), ("c.c.", "L")]:
        (bid,) = G.pick(ml_b)
        G.pair("volume", form, bid, "%s %s" % (N(v(bid)), form), gold("mL", v(bid)), "%s %s" % (N(v(bid)), swap), gold("L", v(bid)))
    for bid, form in [("D0115", "L"), ("D0116", "liters"), ("D0022", "litre")]:
        G.pair("volume", "mL->" + form, bid, "%s %s" % (N(v(bid) / 1000), form), gold("L", v(bid) / 1000),
               "%s %s" % (N(v(bid)), form), gold("L", v(bid)))
    # spacing
    for name, sep in [("no space", ""), ("hyphen", "-"), ("double space", "  "), ("nbsp", "\u00a0"), ("thin space", "\u2009"),
                      ("narrow nbsp", "\u202f")]:
        (bid,) = G.pick(mg_mid)
        G.pair("spacing", name, bid, "%s%smg" % (N(v(bid)), sep), gold("mg", v(bid)), "%s%sg" % (N(v(bid)), sep), gold("g", v(bid)))
    # number formats
    (b1,) = G.pick(mg_small[1:2] + ["D0052", "D0126", "D0112"])  # >= 1 mg -> 1,000+ mcg
    G.pair("number_format", "comma thousands", b1, "%s mcg" % commas(v(b1) * 1000), gold("mcg", v(b1) * 1000),
           "%s mg" % commas(v(b1) * 1000), gold("mg", v(b1) * 1000))
    for name, sep in [("space thousands", " "), ("thin-space thousands", "\u2009"), ("nbsp thousands", "\u00a0")]:
        (bid,) = G.pick(["D0052", "D0126", "D0112", "D0030"])
        s = commas(v(bid) * 1000).replace(",", sep)
        G.pair("number_format", name, bid, "%s mcg" % s, gold("mcg", v(bid) * 1000), "%s mg" % s, gold("mg", v(bid) * 1000))
    G.pair("number_format", "comma thousands mg", "D0099", "1,200 mg", gold("mg", 1200), "1,200 g", gold("g", 1200))
    for name, bid in [("leading-dot decimal", "D0016"), ("leading-dot decimal", "D0013")]:
        s = N(v(bid) / 1000)[1:]  # ".5"
        G.pair("number_format", name, bid, "%s g" % s, gold("g", v(bid) / 1000), "%s mg" % s, gold("mg", v(bid) / 1000))
    for name, bid in [("decimal comma (EU)", "D0016"), ("decimal comma (EU)", "D0148")]:
        s = N(v(bid) / 1000).replace(".", ",")
        G.pair("number_format", name, bid, "%s g" % s, gold("g", v(bid) / 1000), "%s mg" % s, gold("mg", v(bid) / 1000))
    G.pair("number_format", "trailing zeros", "D0058", "10.0 mg", gold("mg", 10), "10.0 mcg", gold("mcg", 10))
    G.pair("number_format", "leading zero conv", "D0140", "25 mcg", gold("mcg", 25), "0.025 mcg", gold("mcg", "0.025"))
    # ranges (label ranges)
    for name, fmt_ in [("hyphen", "{a}-{b} {u}"), ("to", "{a} to {b} {u}"), ("en dash", "{a}–{b} {u}"), ("spaced hyphen", "{a} - {b} {u}"),
                       ("unit both ends", "{a} {u} to {b} {u}"), ("unit both ends hyphen", "{a} {u} - {b} {u}"),
                       ("between/and", "between {a} and {b} {u}"), ("-to-", "{a}-to-{b} {u}"), ("en dash no space", "{a}–{b}{u}"),
                       ("from/to", "{a} to {b} {u}")]:
        (bid,) = G.pick(rng_b)
        a, b = B[bid]["lo"], B[bid]["hi"]
        pre = {"from/to": "from ", "between/and": "between "}.get(name, "")
        fmt_ = fmt_.replace("between ", "")
        G.pair("range", name, bid, fmt_.format(a=a, b=b, u="mg"), gold("mg", a, b), fmt_.format(a=a, b=b, u="mcg"), gold("mcg", a, b),
               pre=pre)
    (bid,) = G.pick(rng_b)
    a, b = D(B[bid]["lo"]), D(B[bid]["hi"])
    G.pair("range", "converted to g", bid, "%s to %s g" % (N(a / 1000), N(b / 1000)), gold("g", a / 1000, b / 1000),
           "%s to %s g" % (N(a), N(b)), gold("g", a, b))
    # fractions
    for name, s_core, s_g, u_core, u_g, bid in [
            ("unicode ½", "½ g", gold("g", "0.5"), "½ mg", gold("mg", "0.5"), "D0016"),
            ("ascii 1/2", "1/2 g", gold("g", "0.5"), "1/2 mg", gold("mg", "0.5"), "D0032"),
            ("unicode ¼", "¼ g", gold("g", "0.25"), "¼ mg", gold("mg", "0.25"), "D0013"),
            ("ascii 1/4", "1/4 gram", gold("g", "0.25"), "1/4 milligram", gold("mg", "0.25"), "D0148"),
            ("½ per kg", "½ mg/kg", gold("mg", "0.5", kg=True), "½ mcg/kg", gold("mcg", "0.5", kg=True), "D0083"),
            ("½ mL", "½ mL", gold("mL", "0.5"), "½ L", gold("L", "0.5"), "D0008"),
            ("mixed 1 1/2", "1 1/2 mg", gold("mg", "1.5"), "1 1/2 g", gold("g", "1.5"), "D0082"),  # 1.8 base: S is a VALUE error
    ]:
        if bid == "D0082":
            continue  # no 1.5 base: skip (would be a value error, not a spelling test)
        G.pair("fraction", name, bid, s_core, s_g, u_core, u_g)
    # number words
    for s_core, s_g, u_core, u_g, bid in [
            ("five milligrams", gold("mg", 5), "five micrograms", gold("mcg", 5), "D0126"),
            ("five mg", gold("mg", 5), "five g", gold("g", 5), "D0126"),
            ("ten milligrams", gold("mg", 10), "ten grams", gold("g", 10), "D0058"),
            ("fifty milligrams", gold("mg", 50), "fifty micrograms", gold("mcg", 50), "D0005"),
            ("fifteen mg", gold("mg", 15), "fifteen mcg", gold("mcg", 15), "D0122"),
            ("twenty-five milligrams", gold("mg", 25), "twenty-five grams", gold("g", 25), "D0120"),
            ("two milligrams", gold("mg", 2), "two micrograms", gold("mcg", 2), "D0030"),
            ("one gram", gold("g", 1), "one milligram", gold("mg", 1), "D0063"),
            ("five hundred milligrams", gold("mg", 500), "five hundred micrograms", gold("mcg", 500), "D0016"),
            ("half a gram", gold("g", "0.5"), "half a milligram", gold("mg", "0.5"), "D0032"),
            ("one milligram per kilogram", gold("mg", 1, kg=True), "one microgram per kilogram", gold("mcg", 1, kg=True), "D0002"),
            ("Two Grams", gold("g", 2), "Two Milligrams", gold("mg", 2), "D0009")]:
        G.pair("words", s_core, bid, s_core, s_g, u_core, u_g)
    # uppercase
    for s_core_f, s_u, u_core_f, u_u, pool in [("{} MG", "mg", "{} G", "g", mg_mid), ("{}MG", "mg", "{}MCG", "mcg", mg_mid),
                                              ("{} MCG", "mcg", "{} MG", "mg", mcg_b), ("{} ML", "mL", "{} L", "L", ml_b),
                                              ("{} MG/KG", "mg", "{} MCG/KG", "mcg", kg_b), ("{} UNITS", "units", "{} MG", "mg", ["RD_glyburide_1"])]:
        (bid,) = G.pick(pool)
        kg = B[bid]["kg"]
        G.pair("uppercase", s_core_f.format("N"), bid, s_core_f.format(N(v(bid))), gold(s_u, v(bid), kg=kg),
               u_core_f.format(N(v(bid))), gold(u_u, v(bid), kg=kg))
    # trailing / surrounding punctuation (core = quantity only)
    for name, pre, suf in [("period", "", "."), ("comma", "", ","), ("paren close", "(", ")"), ("semicolon", "", ";"),
                           ("colon", "", ":"), ("quote", "\"", "\""), ("bracket", "[", "]"), ("period nospace", "", ".")]:
        (bid,) = G.pick(mg_mid)
        joiner = "" if name == "period nospace" else " "
        G.pair("punctuation", name, bid, "%s%smg" % (N(v(bid)), joiner), gold("mg", v(bid)), "%s%sg" % (N(v(bid)), joiner),
               gold("g", v(bid)), pre=pre, suf=suf)
    # basis dropped (unsupported only): per-kg / per-m2 / per-day basis removed
    for bid in ["D0039", "D0051", "D0155", "RD_methotrexate_0", "RD_mycophenolate_1", "RD_cyclosporine_0"]:
        G.add("basis_drop", "dropped basis", bid, "UNSUPPORTED", "%s mg" % N(v(bid)), gold("mg", v(bid)),
              note="per-kg/m2 basis removed (RD unit_error per_kg/per_m2 analogue)")
    # anchors
    used = sorted({it["base_id"] for it in G.items})
    for bid in used:
        b = B[bid]
        G.add("anchor", "anchor", bid, "SUPPORTED", b["claim_span"], gold(b["unit"], b["lo"], b["hi"], b["kg"], b["m2"], b["day"]))
    for i, it in enumerate(G.items):
        it["instance_id"] = "UNFADV%04d__%s__%s" % (i, it["base_id"], "S" if it["label"] == "SUPPORTED" else "U")
    return G.items


# ---------------- normalizer evaluation (shared with unf_adv_report.py)
def _gq(g):
    return (g["key"], D(g["lo"]), D(g["hi"]) if g["hi"] is not None else D(g["lo"]))


def parse_eval(it: dict, mod) -> dict:
    """Does `mod` extract exactly ONE dose span inside the variant region whose canonical quantity equals the gold?
    Region = the inserted surface (incl. any "from"/"between"/bracket wrapper).  For v2 the claim is first rewritten
    by its pre-pass; the region is then located as text minus the (rewritten) unchanged base prefix/suffix."""
    claim = it["claim"]
    s0 = it.get("surface_start", it["core_start"])
    s1 = it.get("surface_end", it["core_end"])
    pre_t, suf_t = claim[:s0], claim[s1:]
    if mod is V1:
        text = claim
        a, b = s0, s1
    else:
        text = V2.prenormalize(claim)
        p2, q2 = V2.prenormalize(pre_t), V2.prenormalize(suf_t)
        a = len(p2) if text.startswith(p2) else s0
        b = len(text) - len(q2) if text.endswith(q2) else len(text)
    spans = V1.find_spans(text)
    ov = [sp for sp in spans if not (sp.end <= a or sp.start >= b)]
    got = []
    for sp in ov:
        c = V1.canonical_quantity(sp.text)
        got.append({"text": sp.text, "key": c[0], "lo": V1.fmt(c[1]), "hi": V1.fmt(c[2]) if c[2] is not None else None}
                   if c else {"text": sp.text})
    ok, why = False, ""
    if not ov:
        why = "no span"
    elif len(ov) > 1:
        why = "split into %d spans" % len(ov)
    else:
        c = V1.canonical_quantity(ov[0].text)
        gq = _gq(it["gold"])
        cq = (c[0], c[1], c[2] if c[2] is not None else c[1]) if c else None
        if cq is None:
            why = "unparsed"
        elif cq[0] != gq[0]:
            why = "wrong key %s (gold %s) from %r" % (cq[0], gq[0], ov[0].text)
        elif cq[1] != gq[1] or cq[2] != gq[2]:
            why = "wrong value %s-%s (gold %s-%s) from %r" % (V1.fmt(cq[1]), V1.fmt(cq[2]), V1.fmt(gq[1]), V1.fmt(gq[2]), ov[0].text)
        else:
            ok = True
    return {"ok": ok, "why": why, "spans": got}


def _contains(hay: str, needle: str) -> bool:
    return re.search(r"(?<![\d.,])" + re.escape(needle) + r"(?![\d\w])", hay) is not None


def pair_eval(it: dict, mod, parse_ok: bool) -> dict:
    """End-to-end UNF effect.  SUPPORTED: the normalized claim contains the normalized evidence span (surface identity,
    UNF's mechanism).  UNSUPPORTED: the swap was parsed correctly AND the normalized claim does not contain it."""
    c2, e2, _ = mod.apply_unf_pair(it["claim"], it["evidence"])
    ev_norm, _, _ = mod.apply_unf_pair(it["evidence_span"], it["evidence"])
    hit = _contains(c2, ev_norm)
    ok = hit if it["label"] == "SUPPORTED" else (parse_ok and not hit)
    return {"ok": ok, "evidence_span_norm": ev_norm, "claim_norm": c2, "evidence_norm": e2}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    bases = load_bases()
    items = build(bases)
    rows = []
    for it in items:
        p1, p2 = parse_eval(it, V1), parse_eval(it, V2)
        q1, q2 = pair_eval(it, V1, p1["ok"]), pair_eval(it, V2, p2["ok"])
        rows.append(dict(it, type="DOSE", condition="UNFADV-" + it["family"], valid=True,
                         claim_unf=q1["claim_norm"], evidence_unf=q1["evidence_norm"],
                         claim_unf_v2=q2["claim_norm"], evidence_unf_v2=q2["evidence_norm"],
                         v1_parse_ok=p1["ok"], v1_parse_why=p1["why"], v1_spans=p1["spans"], v1_pair_ok=q1["ok"],
                         v2_parse_ok=p2["ok"], v2_parse_why=p2["why"], v2_pair_ok=q2["ok"]))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    test = [r for r in rows if r["family"] != "anchor"]
    man = {"items": len(test), "anchors": len(rows) - len(test), "bases": len({r["base_id"] for r in rows}),
           "by_label": dict(Counter(r["label"] for r in test)), "by_family": dict(Counter(r["family"] for r in test)),
           "base_sources": dict(Counter(r["base_source"] for r in rows if r["family"] == "anchor")),
           "v1_parse_acc": round(sum(r["v1_parse_ok"] for r in test) / len(test), 4),
           "v2_parse_acc_posthoc": round(sum(r["v2_parse_ok"] for r in test) / len(test), 4),
           "anchor_v1_parse_ok": sum(r["v1_parse_ok"] for r in rows if r["family"] == "anchor"),
           "bases_dropped_by_sanity_filter": getattr(load_bases, "dropped", {})}
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "build_manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(man, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
