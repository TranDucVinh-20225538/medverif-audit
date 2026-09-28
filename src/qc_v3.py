"""QC v3 rules. No model calls."""

from __future__ import annotations

import re
from typing import Optional

from qc_rules import DES_RE, PRE_RE, clause_around

HEDGES = (
    "in clinical use",
    "the source states",
    "at least",
    "at most",
    "up to",
    "exactly",
    "only",
    "approximately",
    "about",
    "always",
    "never",
    "usually",
    "may",
)

FLIP_BAD_RE = re.compile(
    r"\b(?:with(?:\s+(?:great|extreme))?\s+caution|cautiously|neither|nor|none|never|relatively|"
    r"may be|can be|could be)\b|\bno\b",
    re.I,
)
ADJUNCT_AFTER_PRED_RE = re.compile(
    r"^\s*(?:at|with|as needed|when|annually|regularly|in full)\b",
    re.I,
)
FOR_DURATION_RE = re.compile(
    r"^\s*for\s+(?:\d|(?:the\s+)?(?:first|last|next)\s+\d|(?:acute|chronic|long|short)\b|"
    r"monitoring|surveillance|prophylaxis|prevention|treatment|therapy|relief|pain|symptom)",
    re.I,
)
FOR_IN_PATIENT_RE = re.compile(
    r"^\s*(?:for|in)\s+(?:patients?|children|pediatric|adults?|pregnant|pregnancy|"
    r"individuals|people|those|persons?|women|men|neonates?|infants?|elderly|"
    r"[A-Za-z][\w/-]{2,}(?:/[\w-]+)?)\b",
    re.I,
)
COORD_VP_RE = re.compile(r"\band\s+(?:is|are|was|were|should|must|can|may|will|has|have)\b", re.I)
RANGE_ENDPOINT_RE = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:to|–|—|-|/|or)\s*(\d+(?:\.\d+)?)\s*"
    r"(?:mg|g|mcg|µg|μg|mL|ml|units|mg/kg|mcg/kg)(?![\w/])",
    re.I,
)
NON_INTERVENTION_SUBJECT_RE = re.compile(
    r"\b(?:compensatory|tachycardia|adverse effect|fluid retention|headache|angina)\b",
    re.I,
)
MEAS_RE = re.compile(
    r"\b(?:mg/dL|mg/dl|g/dL|g/dl|mmol(?:/L)?|mEq(?:/L)?|mm\s*Hg|"
    r"mg/24|per 24\s*h(?:ours)?|ng/mL|µg/dL|ug/dL|IU/L|U/L|mL/min|"
    r"proteinuria|serum|plasma|creatinine|hemoglobin|haemoglobin|"
    r"hematocrit|haematocrit|leukocyte|leucocyte|platelet|titer|titre)\b",
    re.I,
)
DOMAIN_OTHER_RE = re.compile(
    r"\b(?:DSM|specifier|diagnostic criteria|ICD-\d*|coding)\b",
    re.I,
)
DOMAIN_DX_RE = re.compile(
    r"\b(?:biopsy|ultrasound|CT|MRI|radiograph|endoscopy|colonoscopy|"
    r"mammogra\w*|screening|imaging|angiograph\w*)\b",
)
DOMAIN_TX_RE = re.compile(
    r"\b(?:vaccine|antibiotic|medication|drug|therapy|inhibitor|"
    r"administered|dose|treatment|mg|tablet|infusion)\b",
    re.I,
)
DOUBLED_RE = re.compile(r"\b([A-Za-z]{2,})\s+\1\b")
DROPCAP_RE = re.compile(r"(?:^|(?<=[.!?]\s))(?:he|hus|hese|n the)\b")
HEADING_RE = re.compile(r"[a-z]\.[A-Z]{4,}|[a-z][A-Z]{5,}")
_BROKEN_SUFFIX = ("drome", "coccus", "nately", "ococcus")
_DICT: set[str] | None = None


def _vocab() -> set[str]:
    global _DICT
    if _DICT is None:
        path = "/usr/share/dict/words"
        words = set()
        try:
            with open(path) as handle:
                words = {line.strip().lower() for line in handle if line.strip().isalpha()}
        except OSError:
            words = set()
        _DICT = words
    return _DICT


def _hyphen_break(text: str) -> bool:
    words = list(re.finditer(r"[A-Za-z]{3,}", text))
    vocab = _vocab()
    for left, right in zip(words, words[1:]):
        if text[left.end():right.start()] != " ":
            continue
        a = left.group().lower()
        b = right.group().lower()
        if a in vocab and b in vocab:
            continue
        if (a + b) in vocab:
            return True
        if a not in vocab and b not in vocab and b.endswith(_BROKEN_SUFFIX):
            return True
    return False


def hedges_in(text: str) -> list[str]:
    found = []
    for hedge in HEDGES:
        if re.search(rf"\b{re.escape(hedge)}\b", text or "", re.I):
            found.append(hedge)
    return found


def extra_hedges(text: str, original: str) -> list[str]:
    original_set = set(hedges_in(original))
    return [hedge for hedge in hedges_in(text) if hedge not in original_set]


def sentence_rule_failure(text: str) -> Optional[str]:
    raw = (text or "").strip()
    if not raw:
        return "empty"
    if ".," in raw or ",." in raw:
        return "bad_punct"
    body = raw
    if body[0] in "\"'“”":
        body = body[1:].lstrip()
    if not body or body[0] in ".,;:!?-":
        return "leading_punct"
    if not body[0].isupper():
        return "leading_lower"
    if not raw.endswith("."):
        return "no_period"
    parts = [part.strip().lower() for part in raw.split(",") if len(part.split()) >= 4]
    if len(parts) != len(set(parts)):
        return "duplicated_clause"
    return None


def span_once(text: str, span: str) -> bool:
    return bool(span) and text.count(span) == 1


def flip_bad_term(text: str, start: int, end: int) -> Optional[str]:
    clause = clause_around(text or "", start, end)
    match = FLIP_BAD_RE.search(clause)
    return match.group(0).lower() if match else None


def flip_post_predicate_ok(text: str, cue_end: int) -> Optional[str]:
    """Return None if flip is allowed; else a short exclusion reason."""
    clause = clause_around(text or "", cue_end, cue_end)
    tail = (text or "")[cue_end:]
    if cue_end < len(text or ""):
        idx = text.find(clause)
        if idx >= 0:
            tail = text[idx + (cue_end - idx) :]
            rel = cue_end - idx
            tail = clause[rel:] if rel <= len(clause) else ""
    tail = tail.strip()
    if not tail or tail in {".", ",", ";"}:
        return None
    if ADJUNCT_AFTER_PRED_RE.search(tail):
        return "adjunct_after_predicate"
    if FOR_DURATION_RE.search(tail):
        return "for_duration_or_purpose"
    if COORD_VP_RE.search(tail):
        return "coordinated_vp"
    if FOR_IN_PATIENT_RE.match(tail):
        return None
    if re.match(r"^[.,;]", tail):
        return None
    return "predicate_not_at_clause_end"


def polarity_flip_allowed(claim: str, span: str, base_id: str = "") -> Optional[str]:
    """Return invalid_reason if this base must not contribute flip instances."""
    if base_id == "P0143":
        return "flip_not_intervention"
    if not span or span not in (claim or ""):
        return "missing_span"
    start = claim.index(span)
    end = start + len(span)
    bad = flip_bad_term(claim, start, end)
    if bad:
        return f"flip_scope:{bad}"
    post = flip_post_predicate_ok(claim, end)
    if post:
        return post
    prefix = claim[:start]
    if NON_INTERVENTION_SUBJECT_RE.search(prefix) and not DOMAIN_TX_RE.search(prefix):
        return "flip_not_intervention"
    return None


def dose_range_endpoint(claim: str, span: str) -> bool:
    if not span or span not in (claim or ""):
        return False
    for match in RANGE_ENDPOINT_RE.finditer(claim):
        a, b = match.group(1), match.group(2)
        unit = match.group(0).split()[-1]
        left = f"{a} {unit}"
        right = f"{b} {unit}"
        if span.strip() in {left, right, a, b}:
            return True
    return False


def main_polarity_domain(domain_kind: str | None) -> bool:
    return domain_kind == "treatment"


def ocr_hits(text: str) -> list[str]:
    if not text:
        return []
    hits = []
    if DOUBLED_RE.search(text):
        hits.append("doubled_word")
    if DROPCAP_RE.search(text):
        hits.append("drop_cap")
    if _hyphen_break(text):
        hits.append("hyphen_break")
    if HEADING_RE.search(text):
        hits.append("run_on_heading")
    return hits


def focus_sentence(text: str, span: str) -> str:
    """Sentence that contains the span. Glued neighbours stay out of this string."""
    from text_utils import split_sentences

    raw = text or ""
    if not span or span not in raw:
        return raw
    for sentence in split_sentences(raw):
        if span in sentence:
            return sentence
    start = raw.find(span)
    return raw


def neighbor_text(evidence: str, target_sentence: str) -> str:
    evidence = evidence or ""
    target = target_sentence or ""
    if target and target in evidence:
        start = evidence.find(target)
        return (evidence[:start] + " " + evidence[start + len(target):]).strip()
    return ""


def dose_kind_v3(claim: str, target_sentence: str, span_start: int, span_end: int) -> str:
    clause = clause_around(claim or "", span_start, span_end)
    blob = clause + " " + (target_sentence or "")
    if MEAS_RE.search(blob):
        return "measurement"
    pre = PRE_RE.search(blob) is not None
    des = DES_RE.search(blob) is not None
    if pre and not des:
        return "prescriptive"
    if des and not pre:
        return "descriptive"
    return "unclear"


def domain_kind_rule(claim: str, target_sentence: str) -> str:
    blob = (claim or "") + " " + (target_sentence or "")
    if DOMAIN_OTHER_RE.search(blob):
        return "other"
    if DOMAIN_DX_RE.search(blob):
        return "diagnostic_procedure"
    if DOMAIN_TX_RE.search(blob):
        return "treatment"
    return "unclear"


def selftest() -> None:
    bad = "40 mg biweekly., adalimumab is given by subcutaneous injection"
    assert sentence_rule_failure(bad) == "bad_punct"
    assert sentence_rule_failure("in clinical use, this is a sentence.") == "leading_lower"
    assert sentence_rule_failure("This is fine.") is None
    assert extra_hedges("Use exactly 75 g.", "Use 75 g.") == ["exactly"]
    assert extra_hedges("Use 75 g.", "Use exactly 75 g.") == []
    assert span_once("Give 75 g daily.", "75 g")
    assert not span_once("Give 75 g and 75 g.", "75 g")
    assert "doubled_word" in ocr_hits("or or vaccine")
    assert "drop_cap" in ocr_hits("Done. he attenuated vaccine is used.")
    assert "hyphen_break" in ocr_hits("Unfortu nately it failed.")
    assert "run_on_heading" in ocr_hits("is indicated.STRESS GASTRITIS")
    assert dose_kind_v3("Proteinuria above 500 mg per 24 h.", "Proteinuria above 500 mg per 24 h.", 18, 24) == "measurement"
    print("qc_v3 selftest ok")


if __name__ == "__main__":
    selftest()
