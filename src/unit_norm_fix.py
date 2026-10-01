"""UNF: rule-based dose-unit canonicalization of a (claim, evidence) pair before a checker sees it.

Journal-revision extension of M1 (`src/quantity_norm.py`; M1 is unchanged and still produces the
pre-registered M1-strong numbers).  Differences from M1:

* pair-aware common unit: every dose span in BOTH texts is rewritten to the unit the EVIDENCE uses
  most often for that quantity kind (tie -> first occurrence), so a correct conversion in the claim
  becomes surface-identical to the evidence (0.5 g vs "500 mg" -> "500 mg"), while a wrong unit swap
  becomes a numeral mismatch (500 g vs "500 mg" -> "500000 mg").  `mode="si"` instead maps
  everything to a fixed unit (mass -> mg, volume -> mL; M1-like).
* wider alias table: ng / mcg / µg / μg / ug / microgram(s) / mg / milligram(s) / g / gm / gram(s);
  mL / ml / milliliter(s) / millilitre(s) / cc / L / liter(s) / litre(s); IU / U / unit(s) /
  international units -> "units"; mEq / milliequivalent(s) -> "mEq"; mmol.
* denominators: /kg (per kg, per kilogram), /m2 (/m², /m^2, per square meter), concentration
  denominators (/mL, /L, /dL; alias only), and time suffixes (/min, /h, /day, /week, /dose; spelled
  "per day", "a day", "/d", "/24 h", "per hour", "/hr", "per minute", "per week", "per dose").
  Time suffixes are converted (min/h/day/week) only when the evidence uses another time unit for the
  same quantity kind AND the converted value is exact to 6 decimals; "/dose" is never converted.
* ranges ("1-2 g", "1 to 2 g") are converted as a whole; thousands separators are dropped.

What it cannot do (by design): units <-> mass (IU vs mg needs a drug-specific factor), per-dose vs
per-day (needs the dosing frequency), and any VALUE error (wrong numeral, faithful-but-wrong
evidence).  Stdlib only; deterministic.
"""

from __future__ import annotations

import re
from collections import Counter
from decimal import Decimal, InvalidOperation, getcontext
from typing import Dict, List, Optional, Tuple

getcontext().prec = 40

_NUM = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"

# numerator units: alias -> (kind, canonical spelling, factor to kind base)
#   mass base = mcg, volume base = mL; "units", "mEq", "mmol" are their own kinds (no conversion)
_NUMERATOR: Dict[str, Tuple[str, str, Decimal]] = {}
for _a in ("ng", "nanogram", "nanograms"):
    _NUMERATOR[_a] = ("mass", "ng", Decimal("0.001"))
for _a in ("mcg", "µg", "μg", "ug", "microgram", "micrograms"):
    _NUMERATOR[_a] = ("mass", "mcg", Decimal("1"))
for _a in ("mg", "milligram", "milligrams"):
    _NUMERATOR[_a] = ("mass", "mg", Decimal("1000"))
for _a in ("g", "gm", "gram", "grams"):
    _NUMERATOR[_a] = ("mass", "g", Decimal("1000000"))
for _a in ("mL", "ml", "milliliter", "milliliters", "millilitre", "millilitres", "cc"):
    _NUMERATOR[_a] = ("volume", "mL", Decimal("1"))
for _a in ("L", "liter", "liters", "litre", "litres"):
    _NUMERATOR[_a] = ("volume", "L", Decimal("1000"))
for _a in ("IU", "U", "unit", "units", "international units", "International Units"):
    _NUMERATOR[_a] = ("units", "units", Decimal("1"))
for _a in ("mEq", "meq", "milliequivalent", "milliequivalents"):
    _NUMERATOR[_a] = ("meq", "mEq", Decimal("1"))
for _a in ("mmol", "millimole", "millimoles"):
    _NUMERATOR[_a] = ("mmol", "mmol", Decimal("1"))

KIND_DEFAULT = {"mass": "mg", "volume": "mL", "units": "units", "meq": "mEq", "mmol": "mmol"}
KIND_UNITS = {"mass": {"ng": Decimal("0.001"), "mcg": Decimal("1"), "mg": Decimal("1000"), "g": Decimal("1000000")},
              "volume": {"mL": Decimal("1"), "L": Decimal("1000")}}

_num_alts = sorted(_NUMERATOR, key=len, reverse=True)
_NUM_UNIT = "|".join(re.escape(a) for a in _num_alts)

# denominators (order matters: body-size, then concentration volume, then time)
_PER = r"(?:\s*/\s*|\s+per\s+)"
_KG = rf"(?P<kg>{_PER}(?:kg|kilogram)(?:\s+(?:of\s+)?body\s*weight)?)"
_M2 = rf"(?P<m2>{_PER}(?:m2|m²|m\^2|square\s+met(?:er|re)))"
_CONC = rf"(?P<conc>\s*/\s*(?:mL|ml|dL|dl|L)(?![A-Za-z]))"
_TIME = (r"(?P<time>\s*/\s*(?:24\s*h(?:ours?|rs?)?|day|d|hour|hr|h|minute|min|week|wk|dose)(?![A-Za-z])"
         r"|\s+per\s+(?:24\s*hours|day|hour|minute|week|dose)|\s+a\s+day)")
_TIME_CANON = {"24h": "/day", "24hours": "/day", "24hrs": "/day", "24hr": "/day", "day": "/day", "d": "/day",
               "aday": "/day", "hour": "/h", "hr": "/h", "h": "/h", "minute": "/min", "min": "/min",
               "week": "/week", "wk": "/week", "dose": "/dose"}
_TIME_PER_MIN = {"/min": Decimal("1"), "/h": Decimal("60"), "/day": Decimal("1440"), "/week": Decimal("10080")}

DOSE_SPAN_RE = re.compile(
    rf"(?<![\w.,/])(?P<n1>{_NUM})(?:\s*(?P<rsep>-|–|—|to)\s*(?P<n2>{_NUM}))?\s*"
    rf"(?P<unit>{_NUM_UNIT})(?![\w\-/])"
    rf"(?:{_KG})?(?:{_M2})?(?:{_CONC})?(?:{_TIME})?",
)
# "U" / "L" / "g" alone are case-sensitive single letters; "(?![\w\-/])" above stops "5 L-arginine",
# "1 G protein" (capital G is not an alias) and "2 g/dose" is caught by the time group.
# NOTE: the negative lookahead blocks a following "/"; denominators are matched by re-trying with
# the unit followed by a denominator (second pattern below).
DOSE_SPAN_RE_DEN = re.compile(
    rf"(?<![\w.,/])(?P<n1>{_NUM})(?:\s*(?P<rsep>-|–|—|to)\s*(?P<n2>{_NUM}))?\s*"
    rf"(?P<unit>{_NUM_UNIT})(?=\s*/|\s+per\s|\s+a\s+day)"
    rf"(?:{_KG})?(?:{_M2})?(?:{_CONC})?(?:{_TIME})?(?![\w])",
)


def _dec(s: str) -> Decimal:
    return Decimal(s.replace(",", ""))


def fmt(v: Decimal) -> str:
    q = v.normalize()
    t = format(q, "f")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return "0" if t in ("", "-0") else t


class Span:
    __slots__ = ("start", "end", "text", "n1", "n2", "rsep", "kind", "unit", "factor", "kg", "m2", "conc", "time")

    def __init__(self, m: re.Match):
        self.start, self.end, self.text = m.start(), m.end(), m.group(0)
        self.n1 = _dec(m.group("n1"))
        self.n2 = _dec(m.group("n2")) if m.group("n2") else None
        self.rsep = m.group("rsep")
        alias = m.group("unit")
        self.kind, self.unit, self.factor = _NUMERATOR[alias]
        self.kg = "/kg" if m.group("kg") else ""
        self.m2 = "/m2" if m.group("m2") else ""
        c = m.group("conc")
        self.conc = ("/" + c.split("/")[-1].strip().replace("ml", "mL").replace("dl", "dL")) if c else ""
        t = m.group("time")
        if t:
            key = re.sub(r"[\s/]|per", "", t.lower()).replace("hours", "hour").replace("hrs", "hr")
            key = {"24hour": "24h"}.get(key, key)
            self.time = _TIME_CANON.get(key, _TIME_CANON.get(key.rstrip("s"), ""))
        else:
            self.time = ""

    @property
    def key(self) -> Tuple[str, str, str, str]:
        """Quantity kind for anchoring the numerator unit (time is anchored separately)."""
        return (self.kind, self.kg, self.m2, self.conc)

    @property
    def tkey(self) -> Tuple[str, str, str, str, str]:
        return (self.kind, self.kg, self.m2, self.conc, "t")


def find_spans(text: str) -> List[Span]:
    out: List[Span] = []
    taken = []
    for rx in (DOSE_SPAN_RE_DEN, DOSE_SPAN_RE):
        for m in rx.finditer(text or ""):
            if any(not (m.end() <= a or m.start() >= b) for a, b in taken):
                continue
            try:
                s = Span(m)
            except (InvalidOperation, KeyError):
                continue
            out.append(s)
            taken.append((m.start(), m.end()))
    return sorted(out, key=lambda s: s.start)


def _anchor(spans: List[Span]) -> Tuple[Dict[tuple, str], Dict[tuple, str]]:
    units: Dict[tuple, Counter] = {}
    first: Dict[tuple, Dict[str, int]] = {}
    times: Dict[tuple, Counter] = {}
    tfirst: Dict[tuple, Dict[str, int]] = {}
    for i, s in enumerate(spans):
        units.setdefault(s.key, Counter())[s.unit] += 1
        first.setdefault(s.key, {}).setdefault(s.unit, i)
        if s.time and s.time != "/dose":
            times.setdefault(s.tkey, Counter())[s.time] += 1
            tfirst.setdefault(s.tkey, {}).setdefault(s.time, i)
    ua = {k: sorted(c, key=lambda u: (-c[u], first[k][u]))[0] for k, c in units.items()}
    ta = {k: sorted(c, key=lambda u: (-c[u], tfirst[k][u]))[0] for k, c in times.items()}
    return ua, ta


def _exact(v: Decimal, places: int = 6) -> bool:
    return v == v.quantize(Decimal(1).scaleb(-places)) if v == v else False


def _render(s: Span, unit: str, time: str) -> Tuple[str, bool]:
    """Return (text, converted_exactly)."""
    f_new = KIND_UNITS.get(s.kind, {}).get(unit)
    if f_new is None:
        unit, f_new = s.unit, s.factor
    mult = s.factor / f_new
    tmult = Decimal(1)
    t_out = s.time
    if time and s.time and s.time != "/dose" and time != s.time:
        tmult = _TIME_PER_MIN[time] / _TIME_PER_MIN[s.time]
        t_out = time
    vals = [s.n1] + ([s.n2] if s.n2 is not None else [])
    new = [v * mult * tmult for v in vals]
    if not all(_exact(v) for v in new):  # inexact time conversion -> keep the time unit
        t_out = s.time
        new = [v * mult for v in vals]
        if not all(_exact(v) for v in new):
            return s.text, False
    num = fmt(new[0]) if len(new) == 1 else "%s to %s" % (fmt(new[0]), fmt(new[1]))
    return "%s %s%s%s%s%s" % (num, unit, s.kg, s.m2, s.conc, t_out), True


def _rewrite(text: str, spans: List[Span], ua: Dict[tuple, str], ta: Dict[tuple, str], mode: str, log: list,
             side: str) -> str:
    out, last = [], 0
    for s in spans:
        if mode == "si":
            unit = KIND_DEFAULT.get(s.kind, s.unit)
            time = ""
        else:
            unit = ua.get(s.key) or KIND_DEFAULT.get(s.kind, s.unit)
            time = ta.get(s.tkey, "")
        new, ok = _render(s, unit, time)
        out.append(text[last:s.start])
        out.append(new)
        last = s.end
        if new != s.text:
            log.append({"side": side, "from": s.text, "to": new})
    out.append(text[last:])
    return "".join(out)


def apply_unf_pair(claim: str, evidence: str, mode: str = "evidence") -> Tuple[str, str, dict]:
    """Canonicalize both texts. mode: 'evidence' (evidence-anchored common unit, default) or 'si'."""
    cs, es = find_spans(claim or ""), find_spans(evidence or "")
    ua, ta = _anchor(es)
    # claim kinds absent from the evidence fall back to the kind default (mass->mg, volume->mL)
    log: list = []
    c2 = _rewrite(claim or "", cs, ua, ta, mode, log, "claim")
    e2 = _rewrite(evidence or "", es, ua, ta, mode, log, "evidence")
    info = {"mode": mode, "n_claim_spans": len(cs), "n_evid_spans": len(es), "edits": log,
            "anchor_units": {"|".join(k): v for k, v in ua.items()}, "anchor_time": {"|".join(k): v for k, v in ta.items()}}
    return c2, e2, info


def canonical_quantity(span_text: str) -> Optional[Tuple[str, Decimal, Optional[Decimal]]]:
    """('mass|/kg||/day', base_value_low, base_value_high) for one dose span, or None.
    Base = mcg (mass) / mL (volume) / the unit itself; time normalised to /day when exact."""
    sp = find_spans(span_text)
    if not sp:
        return None
    s = sp[0]
    t = s.time
    mult = s.factor
    if t and t != "/dose":
        mult = mult * _TIME_PER_MIN["/day"] / _TIME_PER_MIN[t]
        t = "/day"
    return ("%s|%s|%s|%s|%s" % (s.kind, s.kg, s.m2, s.conc, t), s.n1 * mult, (s.n2 * mult) if s.n2 is not None else None)


def _selftest() -> None:
    cases = [
        ("The dose is 0.5 g.", "Give 500 mg twice daily.", "The dose is 500 mg.", None),
        ("The dose is 500 g.", "Give 500 mg twice daily.", "The dose is 500000 mg.", None),
        ("Use 1,000 mcg daily.", "Give 1 mg IM.", "Use 1 mg daily.", None),
        ("10 mcg/kg/min", "0.6 mg/kg/h infusion", "0.6 mg/kg/h", None),
        ("Give 1 to 2 g IV.", "dose 1000-2000 mg", "Give 1000 to 2000 mg IV.", "dose 1000 to 2000 mg"),
        ("5 L of fluid", "5000 mL", "5000 mL of fluid", None),
        ("10 IU of insulin", "10 units", "10 units of insulin", None),
        ("2 g IV q8h", "cefazolin (2 g IV q8h) ... vancomycin (1 g IV q12h)", "2 g IV q8h", None),
        ("2 mg IV q8h", "cefazolin (2 g IV q8h)", "0.002 g IV q8h", None),
        ("a 1 G protein", "1 g", "a 1 G protein", None),
        ("L-arginine 5 L-x", "", "L-arginine 5 L-x", None),
        ("7.5 mg per week", "1 mg/day", "7.5 mg/week", None),  # 7.5/7 inexact -> time kept
        ("1.4 mg per kg per day", "0.2 mg/kg/day", "1.4 mg/kg/day", None),
        ("40 milligrams a day", "20 mg per dose", "40 mg/day", "20 mg/dose"),
    ]
    for c, e, want_c, want_e in cases:
        c2, e2, _ = apply_unf_pair(c, e)
        assert c2 == want_c, (c, e, c2, want_c)
        if want_e is not None:
            assert e2 == want_e, (c, e, e2, want_e)
    assert canonical_quantity("0.5 g")[1] == canonical_quantity("500 mg")[1]
    assert canonical_quantity("10 mcg/kg/min")[0] == "mass|/kg|||/day"
    print("unit_norm_fix selftest OK (%d cases)" % len(cases))


if __name__ == "__main__":
    _selftest()
