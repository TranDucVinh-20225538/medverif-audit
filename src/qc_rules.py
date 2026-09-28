"""QC label rules from the PI review. Rules only. No model calls."""

from __future__ import annotations

import re
from typing import Optional

SCOPE_RE = re.compile(r"\b(?:only|except|unless|but|if not)\b", re.I)
QUANT_RE = re.compile(
    r"(?:≥|≤|>=|<=|(?<![=<>])[<>](?![=])|\bup to\b|\bat least\b|\bat most\b|"
    r"\bmaximum\b|\bminimum\b|\bmore than\b|\bgreater than\b|\bless than\b|\bno more than\b|"
    r"\bno less than\b|\bover\b|\bunder\b|\bexceeding\b)",
    re.I,
)
PRE_RE = re.compile(
    r"\b(?:dose|doses|dosing|dosage|administer(?:ed|ation)?|daily|twice|"
    r"tid|bid|qid|mg/kg|start(?:ing)?|titrat\w*|tablet|capsule|injection|"
    r"infusion|orally|intravenous(?:ly)?|recommended)\b",
    re.I,
)
DES_RE = re.compile(
    r"\b(?:study|studies|trial|cohort|intake|dietary|diet|nutrition|"
    r"protein|fish|consumed|consumption|participants|observed)\b",
    re.I,
)


def _pieces(text: str) -> list[tuple[int, int, str]]:
    parts = []
    start = 0
    for match in re.finditer(r"[.;]", text):
        parts.append((start, match.start(), text[start:match.start()]))
        start = match.end()
    parts.append((start, len(text), text[start:]))
    return parts


def clause_around(text: str, start: int, end: int) -> str:
    for left, right, piece in _pieces(text):
        if left <= start < right or left < end <= right:
            return piece
    return text


def threshold_governed(text: str, start: int, end: int) -> Optional[str]:
    """The quantifier governs this span when no other number sits between them."""
    if start < 0 or end > len(text) or start >= end:
        return None
    clause_left = clause_around_start(text, start, end)
    local = text[clause_left:start]
    chosen = None
    for match in QUANT_RE.finditer(local):
        between = local[match.end():]
        if re.search(r"\d", between):
            continue
        word = match.group(0).lower()
        if word in {"over", "under"}:
            rest = between.lstrip()
            if not re.match(r"(?:\d|the equivalent\b|a dose\b)", rest, re.I):
                continue
        chosen = match.group(0)
    return chosen


def clause_around_start(text: str, start: int, end: int) -> int:
    for left, right, _piece in _pieces(text):
        if left <= start < right or left < end <= right:
            return left
    return 0


def scope_hit(text: str, start: int, end: int) -> Optional[str]:
    clause = clause_around(text, start, end)
    match = SCOPE_RE.search(clause)
    return match.group(0).lower() if match else None


def dose_kind_rule(text: str) -> str:
    pre = PRE_RE.search(text) is not None
    des = DES_RE.search(text) is not None
    if pre and not des:
        return "prescriptive"
    if des and not pre:
        return "descriptive"
    return "unclear"


def paraphrase_candidates(claim: str, span: str) -> list[dict]:
    """Rewrites that keep the target span verbatim. At most three."""
    if span not in claim:
        return []
    out = []

    def add(template: str, text: str) -> None:
        text = " ".join(text.split())
        if text == claim or span not in text or any(item["text"] == text for item in out):
            return
        out.append({"template": template, "text": text})

    if ", " in claim:
        left, right = claim.split(", ", 1)
        if span in left and span not in right:
            add("clause_swap", right[0].upper() + right[1:] + ", " + left[0].lower() + left[1:])
        elif span in right and span not in left:
            add("clause_swap", right[0].upper() + right[1:] + ", " + left[0].lower() + left[1:])
    for src, dst in (("Patients", "Individuals"), ("Adults", "People"), ("children", "pediatric patients")):
        if src in claim and src not in span:
            add("wording_" + src.lower(), claim.replace(src, dst, 1))
    add("front_clinical", "In clinical use, " + claim[0].lower() + claim[1:])
    add("front_record", "The source states that " + claim[0].lower() + claim[1:])
    if claim.endswith("."):
        add("trailing_note", claim[:-1] + ", as stated.")
    return out[:3]
