"""UNF v2 -- POST-HOC surface pre-pass in front of UNF v1 (src/unit_norm_fix.py). NOT the pre-specified fix.

Written AFTER inspecting the v1 failures on the adversarial unit-spelling set (data/journal2/unf_adversarial.jsonl,
scripts/journal2/unf_adv_build.py), so its accuracy on that set is optimistic by construction (tuned on the test
set).  Main/paper UNF numbers always use v1 unchanged; v2 is reported separately and labelled post-hoc.

v2 = rewrite surface variants into spellings v1 already parses, then call v1 (apply_unf_pair / find_spans /
canonical_quantity) on the rewritten text:
  * unicode: NBSP / thin / narrow spaces -> space; en/em dash or "-to-" between numbers -> range
  * case + plural/hyphen spellings of units after a number: MG, Mg, MCG, mcgs, micro-gram(s), milli-gram(s),
    milligramme(s), mgs, gms, mls, ML, c.c., Units/UNITS, I.U., IU's, Kg/KG, "l" (litre) -> v1 aliases
    (capital "G" alone stays unparsed, as in v1, to protect "G protein")
  * "5-mg" -> "5 mg"; "/m 2", "/sq m", "/M2", "m-2", "kg-1", "·kg⁻¹" -> "/m2", "/kg"; "mg/kg daily" -> "mg/kg/day"
  * numbers: thousands groups separated by thin/narrow/no-break space joined; European decimal comma (0,5 / 2,5
    i.e. NOT a 3-digit group) -> point; unicode and ASCII fractions (½, 2½, 1/2, 2 1/2) -> decimals;
    number words (one..ninety-nine, hundred, thousand, "half a", "one-half", "and a half") before a unit
  * ranges with the unit on both ends ("5 mg to 10 mg", "5 mg - 10 mg") and "between 5 and 10 mg" -> "5 to 10 mg"
Plain-space thousands ("1 000 mg") are deliberately NOT joined: "take 2 500 mg tablets" is ambiguous.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Tuple

import unit_norm_fix as V1

_UNIT_WORD = (r"(?:mcg|µg|μg|ug|micrograms?|mg|milligrams?|g|gm|grams?|ng|mL|ml|cc|L|liters?|litres?|milliliters?|"
              r"millilitres?|IU|U|units?|international units|International Units|mEq|mmol)")

_SPELL = [  # (pattern after a number, replacement) -- applied case-sensitively in order
    (r"micro-?grams?|mcgs|MCG|Mcg|μG|µG|UG", "mcg"),
    (r"milli-?grams?|milligrammes?|mgs|MG|Mg", "mg"),
    (r"gms|grammes?|Grams?", "g"),
    (r"milli-?lit(?:er|re)s?|mls|ML|Ml|c\.c\.|CC", "mL"),
    (r"Lit(?:er|re)s?|l(?![A-Za-z])", "L"),
    (r"UNITS|Units|I\.U\.|IU's|IUs|iu", "units"),
    (r"MEQ|MEq|meq", "mEq"),
]
_NUMRE = r"(?:\d+(?:\.\d+)?|\.\d+)"
_ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_FRAC = {"½": "0.5", "¼": "0.25", "¾": "0.75", "⅓": None, "⅛": "0.125"}


def _words_to_num(ws: str):
    ws = ws.lower().replace("-", " ").split()
    total, cur, seen = 0, 0, False
    for w in ws:
        if w in ("and", "a"):
            continue
        if w in _ONES:
            cur += _ONES[w]
        elif w in _TENS:
            cur += _TENS[w]
        elif w == "hundred":
            cur = (cur or 1) * 100
        elif w == "thousand":
            total += (cur or 1) * 1000
            cur = 0
        else:
            return None
        seen = True
    return (total + cur) if seen else None


_NUMWORD = r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|" \
           r"seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)"
_WORDSEQ = re.compile(rf"(?<![A-Za-z])((?:{_NUMWORD})(?:(?:\s+|-)(?:and\s+)?(?:{_NUMWORD}))*)"
                      rf"(\s+and\s+a\s+half)?(?=\s+{_UNIT_WORD}(?![A-Za-z]))", re.I)
_HALF = re.compile(rf"(?<![A-Za-z])(?:half\s+an?|one[- ]half(?:\s+of\s+an?|\s+an?)?|a\s+half)(?=\s+{_UNIT_WORD}(?![A-Za-z]))", re.I)


def prenormalize(text: str) -> str:
    t = text or ""
    t = re.sub(r"[\u00a0\u2009\u202f\u2007]", lambda m: "\u2009", t)  # unify special spaces (joined below)
    t = re.sub(r"(?<!\d)(\d{1,3})((?:\u2009\d{3})+)(?!\d)", lambda m: m.group(1) + m.group(2).replace("\u2009", ""), t)
    t = t.replace("\u2009", " ")
    # unicode / ASCII fractions
    t = re.sub(r"(\d+)\s*([½¼¾⅛])", lambda m: str(Decimal(m.group(1)) + Decimal(_FRAC[m.group(2)])) if _FRAC[m.group(2)] else m.group(0), t)
    t = re.sub(r"[½¼¾⅛]", lambda m: _FRAC[m.group(0)] or m.group(0), t)
    t = re.sub(rf"(?<![\d/.])(\d+)\s+(\d)/(\d)(?=\s*{_UNIT_WORD}(?![A-Za-z]))",
               lambda m: V1.fmt(Decimal(m.group(1)) + Decimal(m.group(2)) / Decimal(m.group(3))), t)
    t = re.sub(rf"(?<![\d/.])(\d)/(\d)(?=\s*{_UNIT_WORD}(?![A-Za-z]))",
               lambda m: V1.fmt(Decimal(m.group(1)) / Decimal(m.group(2))), t)
    # European decimal comma (not a thousands group)
    t = re.sub(r"(?<![\d,.])(\d+),(\d{1,2})(?!\d)(?=\s*[A-Za-zµμ])", r"\1.\2", t)
    # number words
    t = _HALF.sub("0.5", t)

    def _w(m):
        n = _words_to_num(m.group(1))
        if n is None:
            return m.group(0)
        return V1.fmt(Decimal(n) + (Decimal("0.5") if m.group(2) else 0))
    t = _WORDSEQ.sub(_w, t)
    # unit spellings / case directly after a number (optionally hyphen-joined: "5-mg")
    for pat, rep in _SPELL:
        t = re.sub(rf"(?<![\w.])({_NUMRE})(\s*|-)(?:{pat})(?![A-Za-z])", lambda m, rep=rep: m.group(1) + " " + rep, t)
    t = re.sub(rf"(?<![\w.])({_NUMRE})-({_UNIT_WORD})(?![A-Za-z])", r"\1 \2", t)
    # denominators
    t = re.sub(r"\s*/\s*(?:KG|Kg)\b", "/kg", t)
    t = re.sub(r"\s*(?:·|\.|\s)\s*kg(?:-1|⁻¹)", "/kg", t)
    t = re.sub(r"\s*/\s*(?:m\s+2|M2|M²|sq\.?\s*m)(?![\w])", "/m2", t)
    t = re.sub(r"\s*(?:·|\s)\s*m(?:-2|⁻²)", "/m2", t)
    t = re.sub(r"\s+per\s+m2\b", "/m2", t)
    t = re.sub(r"(/kg)\s+(?:daily|a day|per day)\b", r"\1/day", t)
    t = re.sub(r"(/kg)\s*/\s*24\s*h(?:ours?|rs?)?\b", r"\1/day", t)
    # ranges
    t = re.sub(rf"({_NUMRE})\s*[–—]\s*({_NUMRE})", r"\1-\2", t)
    t = re.sub(rf"({_NUMRE})-to-({_NUMRE})", r"\1 to \2", t)
    t = re.sub(rf"\bbetween\s+({_NUMRE})\s+and\s+({_NUMRE})(\s*{_UNIT_WORD})", r"\1 to \2\3", t)
    t = re.sub(rf"({_NUMRE})\s*({_UNIT_WORD})\s*(?:-|to)\s*({_NUMRE})\s*\2(?![A-Za-z])", r"\1 to \3 \2", t)
    return t


def find_spans(text: str):
    return V1.find_spans(prenormalize(text))


def canonical_quantity(span_text: str):
    return V1.canonical_quantity(prenormalize(span_text))


def apply_unf_pair(claim: str, evidence: str, mode: str = "evidence") -> Tuple[str, str, dict]:
    c2, e2, info = V1.apply_unf_pair(prenormalize(claim), prenormalize(evidence), mode=mode)
    info["normalizer"] = "unf_v2_posthoc"
    return c2, e2, info


if __name__ == "__main__":
    for s in ["five milligrams", "500 MG", "1 000 mcg", "0,5 g", "½ g", "2 1/2 mg", "5-mg", "10 mg/m 2",
              "5 mg to 10 mg", "between 5 and 10 mg", "half a gram", "twenty-five milligrams", "3 mg/kg daily", "20 Units"]:
        print(repr(s), "->", repr(prenormalize(s)), canonical_quantity(s))
