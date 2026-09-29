"""T4c: rule-based claim = sentence(s) containing the target dose mention."""

from __future__ import annotations

import re

from t4_eco_compare import pick_answer_dose, raw_compact
from text_utils import DOSE_RE, split_sentences


_FREQ_CLAUSE = re.compile(
    r"\b("
    r"once daily|twice daily|three times daily|four times daily|"
    r"once a day|twice a day|three times a day|four times a day|"
    r"every\s+\d+\s+hours?|every hour|q\d+h|"
    r"bid|tid|qid|qd|"
    r"weekly|biweekly|thrice weekly|twice weekly|once weekly|"
    r"single daily dose"
    r")\b",
    re.I,
)


def _sentence_has_dose(sentence: str, needle: str) -> bool:
    if not sentence or not needle:
        return False
    if needle.lower() in sentence.lower():
        return True
    if raw_compact(needle) in raw_compact(sentence):
        return True
    nm = DOSE_RE.search(needle)
    if nm:
        pat = re.compile(
            rf"\b{re.escape(nm.group(1))}\s*(?:{re.escape(nm.group(2))}|mg|mcg|g|ml|mL)\b",
            re.I,
        )
        if pat.search(sentence):
            return True
    return False


def _next_clause_frequency(sentences: list[str], idx: int) -> str:
    """If frequency lives in the next sentence/clause, include it."""
    if idx + 1 >= len(sentences):
        return ""
    nxt = sentences[idx + 1].strip()
    if not nxt or not _FREQ_CLAUSE.search(nxt):
        return ""
    if _FREQ_CLAUSE.search(sentences[idx]):
        return ""
    return nxt


def extract_claim_sentence(answer: str, target_span_claim: str) -> tuple[str, str]:
    """Return (claim_sentence, rule_note)."""
    ans = (answer or "").strip()
    if not ans:
        return ans, "empty_answer"
    tgt = (target_span_claim or "").strip()
    needle = pick_answer_dose(ans, tgt) or tgt
    sentences = split_sentences(ans)
    if not sentences:
        return ans, "no_split"
    hit = None
    for i, sent in enumerate(sentences):
        if needle and _sentence_has_dose(sent, needle):
            hit = i
            break
    if hit is None and tgt:
        for i, sent in enumerate(sentences):
            if _sentence_has_dose(sent, tgt):
                hit = i
                break
    if hit is None:
        for i, sent in enumerate(sentences):
            if DOSE_RE.search(sent):
                hit = i
                break
    if hit is None:
        return ans[:800], "fallback_full_answer"
    claim = sentences[hit].strip()
    extra = _next_clause_frequency(sentences, hit)
    if extra:
        claim = f"{claim} {extra}".strip()
        note = "dose_sentence+freq_next"
    else:
        note = "dose_sentence"
    return claim, note
