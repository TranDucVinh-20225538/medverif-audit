"""Eco answer vs evidence dose comparison (normalization + categories)."""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Optional

from text_utils import DOSE_RE, RANGE_RE, natural_unit_conversion, parse_decimal

# --- frequency ---

_FREQ_CANON = {
    "qd": "once_daily",
    "daily": "once_daily",
    "once daily": "once_daily",
    "once a day": "once_daily",
    "one time daily": "once_daily",
    "every day": "once_daily",
    "bid": "twice_daily",
    "twice daily": "twice_daily",
    "twice a day": "twice_daily",
    "two times daily": "twice_daily",
    "two times a day": "twice_daily",
    "tid": "three_times_daily",
    "three times daily": "three_times_daily",
    "three times a day": "three_times_daily",
    "thrice daily": "three_times_daily",
    "qid": "four_times_daily",
    "four times daily": "four_times_daily",
    "four times a day": "four_times_daily",
}

_QH = re.compile(r"\bq(\d+)h\b", re.I)
_EVERY_N_H = re.compile(r"\bevery\s+(\d+)\s+hours?\b", re.I)
_EVERY_HOUR = re.compile(r"\bevery\s+hour\b", re.I)
_PER_HOUR = re.compile(r"\b(?:per|each)\s+hour\b", re.I)
_THRICE_WEEKLY = re.compile(
    r"\b(thrice weekly|three times a week|three times weekly|3 times a week)\b", re.I
)
_TWICE_WEEKLY = re.compile(
    r"\b(twice weekly|two times a week|two times weekly|2 times a week)\b", re.I
)
_ONCE_WEEKLY = re.compile(r"\b(once weekly|one time weekly)\b", re.I)
_WEEKLY = re.compile(r"\bweekly\b", re.I)
_BIWEEKLY = re.compile(r"\bbiweekly\b", re.I)
_SINGLE_DAILY = re.compile(r"\bsingle daily dose\b", re.I)

_WORD_DOSE = re.compile(
    r"(?<![\w./])(\d+(?:\.\d+)?)\s*"
    r"(milligrams?|micrograms?|grams?|milliliters?|liters?)(?![\w/])",
    re.I,
)

_PER_KG = re.compile(
    r"\b(?:per|for each|for every)\s+(?:kilogram|kilograms|kg)\b", re.I
)
_PER_KG_SLASH = re.compile(r"/\s*kg\b", re.I)

_UNIT_WORD_TO_ABBR = (
    (r"\bmilligrams?\b", "mg"),
    (r"\bmicrograms?\b", "mcg"),
    (r"\bgrams?\b", "g"),
    (r"\bmilliliters?\b", "mL"),
    (r"\bliters?\b", "L"),
    (r"\bµg\b", "mcg"),
    (r"\bμg\b", "mcg"),
)


def _canon_qhours(n: int) -> str:
    return f"q{n}h"


def frequency_signature(text: str) -> frozenset[str]:
    t = prenormalize_text(text or "")
    sig: set[str] = set()
    for m in _QH.finditer(t):
        sig.add(_canon_qhours(int(m.group(1))))
    for m in _EVERY_N_H.finditer(t):
        sig.add(_canon_qhours(int(m.group(1))))
    if _EVERY_HOUR.search(t):
        sig.add("q1h")
    if _PER_HOUR.search(t):
        sig.add("q1h")
    if _THRICE_WEEKLY.search(t):
        sig.add("thrice_weekly")
    if _TWICE_WEEKLY.search(t):
        sig.add("twice_weekly")
    if _ONCE_WEEKLY.search(t):
        sig.add("once_weekly")
    if _WEEKLY.search(t):
        sig.add("once_weekly")
    if _BIWEEKLY.search(t):
        sig.add("biweekly")
    for phrase, key in _FREQ_CANON.items():
        if re.search(rf"\b{re.escape(phrase)}\b", t):
            sig.add(key)
    return frozenset(sig)


def prenormalize_text(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"\b(\d+)\s*h\b", r"every \1 hours", t)
    for pat, repl in _UNIT_WORD_TO_ABBR:
        t = re.sub(pat, repl, t, flags=re.I)
    t = re.sub(r"(\d)(mg|mcg|g|ml|mL|L)", r"\1 \2", t)
    return t


def collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def normalize_dose_surface(span: str) -> str:
    s = collapse_ws(prenormalize_text(span))
    s = _PER_KG.sub("/kg", s)
    s = re.sub(r"/\s*kg", "/kg", s)
    s = re.sub(r"(\d)\s*/\s*kg", r"\1/kg", s)
    return collapse_ws(s)


def raw_compact(span: str) -> str:
    return re.sub(r"\s+", "", (span or "").strip().lower())


def _word_to_dose_span(num: str, unit_word: str) -> str:
    u = unit_word.lower()
    if u.startswith("milligram"):
        unit = "mg"
    elif u.startswith("microgram"):
        unit = "mcg"
    elif u.startswith("gram"):
        unit = "g"
    elif u.startswith("milliliter"):
        unit = "mL"
    elif u.startswith("liter"):
        unit = "L"
    else:
        unit = u
    return f"{num} {unit}"


def all_dose_spans(text: str) -> list[str]:
    t = text or ""
    spans: list[str] = []
    seen: set[str] = set()
    for m in DOSE_RE.finditer(t):
        s = m.group(0).strip()
        if s not in seen:
            spans.append(s)
            seen.add(s)
    for m in _WORD_DOSE.finditer(t):
        s = _word_to_dose_span(m.group(1), m.group(2))
        if s not in seen:
            spans.append(s)
            seen.add(s)
    return spans


def _with_per_kg(span: str, context: str, pos: int) -> str:
    if _PER_KG_SLASH.search(span):
        return span
    window = context[max(0, pos - 20) : pos + len(span) + 80]
    if _PER_KG.search(window) or re.search(r"\bper\s+kilogram\b", window, re.I):
        return f"{span}/kg"
    return span


def dose_spans_with_kg(text: str) -> list[str]:
    out: list[str] = []
    t = text or ""
    for m in DOSE_RE.finditer(t):
        out.append(_with_per_kg(m.group(0).strip(), t, m.start()))
    for m in _WORD_DOSE.finditer(t):
        base = _word_to_dose_span(m.group(1), m.group(2))
        out.append(_with_per_kg(base, t, m.start()))
    return out


def target_in_range(answer: str, tgt_span: str) -> bool:
    t_num_m = DOSE_RE.search(tgt_span)
    if not t_num_m:
        return False
    t_val = parse_decimal(t_num_m.group(1))
    t_unit = normalize_dose_surface(t_num_m.group(2)).replace(" ", "")
    for m in RANGE_RE.finditer(answer or ""):
        rm = DOSE_RE.search(m.group(0))
        if not rm:
            continue
        parts = re.split(r"[-–—]", m.group(0), maxsplit=1)
        if len(parts) != 2:
            continue
        lo_m = re.search(r"(\d+(?:\.\d+)?)", parts[0])
        hi_m = re.search(r"(\d+(?:\.\d+)?)", parts[1])
        if not lo_m or not hi_m:
            continue
        lo, hi = parse_decimal(lo_m.group(1)), parse_decimal(hi_m.group(1))
        u = normalize_dose_surface(rm.group(2)).replace(" ", "")
        if u == t_unit and lo <= t_val <= hi:
            return True
    return False


def doses_match(ans_span: str, tgt_span: str) -> bool:
    if raw_compact(ans_span) == raw_compact(tgt_span):
        return True
    if doses_norm_equal(ans_span, tgt_span):
        return True
    conv = natural_unit_conversion(tgt_span)
    if conv and (raw_compact(conv) == raw_compact(ans_span) or doses_norm_equal(conv, ans_span)):
        return True
    return False


def doses_norm_equal(a_span: str, b_span: str) -> bool:
    return normalize_dose_surface(a_span) == normalize_dose_surface(b_span)


def pick_answer_dose(answer: str, tgt_span: str) -> Optional[str]:
    if not tgt_span:
        return None
    cands = dose_spans_with_kg(answer)
    if not cands:
        return None
    for c in cands:
        if doses_match(c, tgt_span):
            return c
    if target_in_range(answer, tgt_span):
        return tgt_span
    # target value appears as number+word elsewhere
    t_m = DOSE_RE.search(tgt_span)
    if t_m:
        pat = re.compile(
            rf"\b{re.escape(t_m.group(1))}\s*(?:mg|mcg|g|ml|milligrams?|micrograms?|grams?|milliliters?)\b",
            re.I,
        )
        if pat.search(answer or ""):
            return tgt_span
    return cands[0] if cands else None


def primary_dose(text: str) -> tuple[str, str] | None:
    spans = all_dose_spans(text)
    if not spans:
        return None
    s = spans[0]
    m = DOSE_RE.search(s)
    if m:
        return s, f"{m.group(1)} {m.group(2)}"
    wm = _WORD_DOSE.search(s) or _WORD_DOSE.search(text or "")
    if wm:
        s2 = _word_to_dose_span(wm.group(1), wm.group(2))
        return s2, s2
    return s, s


def dose_in_evidence_verbatim(dose_span: str, evidence: str, target_span: str) -> bool:
    hay = f"{target_span or ''}\n{evidence or ''}"
    if not dose_span or not hay:
        return False
    ds = dose_span.strip()
    if ds in hay or ds.lower() in hay.lower():
        return True
    return raw_compact(ds) in raw_compact(hay)


def _local_context(text: str, needle: str, radius: int = 140) -> str:
    if not text or not needle:
        return text or ""
    t = text
    pos = t.lower().find(needle.lower())
    if pos < 0:
        pos = 0
    return t[max(0, pos - radius) : pos + len(needle) + radius]


def frequency_surface_rephrase(
    answer: str,
    evidence: str,
    target_span: str,
    ans_span: str = "",
) -> bool:
    """True when dose is fine but frequency wording differs (not daily↔once daily)."""
    a = prenormalize_text(_local_context(answer, ans_span) if ans_span else answer)
    ev = prenormalize_text(
        _local_context(f"{target_span} {evidence}", target_span or ans_span)
    )
    ev_full = prenormalize_text(evidence)
    if _EVERY_HOUR.search(a) and (_PER_HOUR.search(ev_full) or _PER_HOUR.search(ev)):
        return True
    # qNh in source label text, every N hours in answer (D0009/D0068)
    em = _EVERY_N_H.search(a)
    if em and re.search(rf"\bq{int(em.group(1))}h\b", ev_full):
        return True
    if (_EVERY_HOUR.search(a) or _PER_HOUR.search(a)) and re.search(
        r"\bq1h\b", ev
    ):
        if not _EVERY_HOUR.search(ev):
            return True
    # thrice weekly ↔ three times a week
    if re.search(r"\bthrice weekly\b", ev) and re.search(
        r"\bthree times a week\b", a
    ):
        return True
    if re.search(r"\bthree times a week\b", ev) and re.search(
        r"\bthrice weekly\b", a
    ):
        return True
    # tid ↔ three times a day (long form)
    if re.search(r"\btid\b", ev) and re.search(r"\bthree times a day\b", a):
        return True
    if re.search(r"\btid\b", a) and re.search(r"\bthree times a day\b", ev):
        return True
    # single daily dose ↔ once daily
    if _SINGLE_DAILY.search(ev) and re.search(r"\bonce daily\b", a):
        return True
    # bid ↔ twice a day (not twice daily)
    if re.search(r"\bbid\b", ev) and re.search(r"\btwice a day\b", a):
        return True
    if re.search(r"\btwice daily\b", ev) and re.search(r"\btwice a day\b", a):
        return True
    return False


def classify_answer(answer: str, evidence: str, target_span: str) -> str:
    tgt = primary_dose(target_span) or primary_dose(evidence)
    if tgt is None:
        ans = primary_dose(answer)
        return "omitted" if ans is None else "changed_value"
    tgt_span, _ = tgt

    ans_span = pick_answer_dose(answer, tgt_span)
    if ans_span is None:
        # spelled-out target dose without unit token DOSE_RE likes
        if re.search(r"\b\d", answer or ""):
            wm = _WORD_DOSE.search(answer)
            if wm and doses_match(_word_to_dose_span(wm.group(1), wm.group(2)), tgt_span):
                ans_span = _word_to_dose_span(wm.group(1), wm.group(2))
        if ans_span is None:
            return "omitted"

    if not doses_match(ans_span, tgt_span):
        try:
            a_m = DOSE_RE.search(ans_span)
            t_m = DOSE_RE.search(tgt_span)
            if a_m and t_m:
                a_num = parse_decimal(a_m.group(1))
                t_num = parse_decimal(t_m.group(1))
                a_u = normalize_dose_surface(a_m.group(2)).replace(" ", "")
                t_u = normalize_dose_surface(t_m.group(2)).replace(" ", "")
                if a_u == t_u and a_num != t_num:
                    return "changed_value"
        except Exception:
            pass
        conv = natural_unit_conversion(tgt_span)
        if conv and doses_match(ans_span, conv):
            return "unit_converted"
        return "changed_value"

    if frequency_surface_rephrase(answer, evidence, target_span, ans_span):
        return "frequency_rephrased"

    verbatim = dose_in_evidence_verbatim(ans_span, evidence, target_span)
    if raw_compact(ans_span) == raw_compact(tgt_span):
        return "exact_verbatim" if verbatim else "exact_surface_variant"
    return "exact_verbatim" if verbatim else "exact_surface_variant"


def collapse_exact(cat: str) -> str:
    if cat in ("exact_verbatim", "exact_surface_variant"):
        return "exact"
    return cat


def gold_from_pi_row(row: dict) -> str:
    cc = (row.get("correct_category") or "").strip()
    if cc:
        return cc
    if (row.get("PI_ok") or "").upper() == "Y":
        ec = (row.get("eco_category") or "").strip()
        return collapse_exact(ec) if ec in ("exact_verbatim", "exact_surface_variant") else ec
    return cc or "?"


def apply_pi_override(
    task_id: str,
    answerer_id: str,
    classifier_cat: str,
    labels: dict[tuple[str, str], dict],
) -> str:
    key = (task_id, answerer_id)
    if key not in labels:
        return classifier_cat
    row = labels[key]
    cc = (row.get("correct_category") or "").strip()
    if cc:
        if cc == "exact":
            if classifier_cat in ("exact_verbatim", "exact_surface_variant"):
                return classifier_cat
            return "exact_surface_variant"
        return cc
    return classifier_cat


def _read_pi_csv(path) -> dict[tuple[str, str], dict]:
    import csv

    out: dict[tuple[str, str], dict] = {}
    p = Path(path)
    if not p.is_file():
        return out
    with p.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if not (row.get("task_id") and row.get("answerer_id")):
                continue
            pi = (row.get("PI_ok") or "").strip()
            cc = (row.get("correct_category") or "").strip()
            if not pi and not cc:
                continue
            out[(row["task_id"], row["answerer_id"])] = row
    return out


def load_pi_labels(path) -> dict[tuple[str, str], dict]:
    """All rows with PI_ok or correct_category set (utf-8-sig CSV)."""
    return _read_pi_csv(path)


def load_pi_sheet_keys(path) -> set[tuple[str, str]]:
    import csv

    keys: set[tuple[str, str]] = set()
    p = Path(path)
    if not p.is_file():
        return keys
    with p.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("task_id") and row.get("answerer_id"):
                keys.add((row["task_id"], row["answerer_id"]))
    return keys


def load_pi_label_paths(paths: list) -> dict[tuple[str, str], dict]:
    merged: dict[tuple[str, str], dict] = {}
    for path in paths:
        for key, row in _read_pi_csv(path).items():
            merged[key] = row
    return merged


def default_pi_label_paths(root) -> list:
    from pathlib import Path

    r = Path(root)
    return [
        r / "qc" / "eco_PI_ok_labels.csv",
        r / "qc" / "eco_review2.csv",
    ]
