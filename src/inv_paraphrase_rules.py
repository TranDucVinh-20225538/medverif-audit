"""Hard rules for INV paraphrase (G full run), before LLM validator."""

from __future__ import annotations

import re

from generate_v3 import rule_failure as _base_rule_failure

PILOT_QUALIFIERS = (
    "relatively",
    "exactly",
    "about",
    "approximately",
    "up to",
    "at least",
    "may",
    "can",
    "usually",
    "generally",
    "typically",
    "only",
    "often",
    "commonly",
)

_SUBORD_MARKERS = (
    " due to ",
    " because ",
    " if ",
    " when ",
    " unless ",
    " as ",
    " after ",
    " before ",
)


def _qualifiers_present(text: str) -> set[str]:
    low = (text or "").lower()
    found: set[str] = set()
    for q in sorted(PILOT_QUALIFIERS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(q)}\b", low):
            found.add(q)
    return found


def qualifier_set_mismatch(original: str, rewrite: str) -> str | None:
    a = _qualifiers_present(original)
    b = _qualifiers_present(rewrite)
    if a != b:
        missing = sorted(a - b)
        extra = sorted(b - a)
        parts = []
        if missing:
            parts.append("missing:" + ",".join(missing))
        if extra:
            parts.append("extra:" + ",".join(extra))
        return "qualifier_set:" + ";".join(parts)
    return None


def _starts_subordinate_clause(text: str) -> bool:
    s = (text or "").strip().lower()
    if re.match(r"^(if|when|unless|because|as|after|before)\b", s):
        return True
    return bool(re.match(r"^due to\b", s))


def subordinate_clause_reorder(original: str, rewrite: str) -> bool:
    """Allow pure token permutations that move a subordinate clause start ↔ end."""
    o_sub = _starts_subordinate_clause(original)
    r_sub = _starts_subordinate_clause(rewrite)
    if o_sub == r_sub:
        return False
    pad_o = f" {(original or '').lower()} "
    pad_r = f" {(rewrite or '').lower()} "
    return any(m in pad_o and m in pad_r for m in _SUBORD_MARKERS)


def fronting_violation(original: str, rewrite: str) -> str | None:
    """Reject only when a short (≤4 token) trailing adverbial/PP is moved to the front."""
    raw = (rewrite or "").strip()
    m = re.match(r"^(.+?),\s", raw)
    if not m:
        return None
    prefix_raw = m.group(1).strip()
    prefix_tokens = _tokens(prefix_raw)
    if len(prefix_tokens) > 4:
        return None
    prefix = re.sub(r"\s+", " ", prefix_raw.lower())
    if not prefix:
        return None
    orig = (original or "").strip().rstrip(".").lower()
    orig_norm = re.sub(r"\s+", " ", orig)
    if orig_norm.endswith(prefix):
        return "fronting"
    tail = orig_norm.split(",")[-1].strip()
    if tail == prefix or tail.endswith(" " + prefix) or tail.endswith(prefix):
        return "fronting"
    return None


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def word_edit_violation(original: str, rewrite: str) -> str | None:
    a = _tokens(original)
    b = _tokens(rewrite)
    if not a or not b:
        return "empty_tokens"
    sa, sb = set(a), set(b)
    union = len(sa | sb)
    jacc = len(sa & sb) / union if union else 0.0
    if jacc < 0.5:
        return f"jaccard_low:{jacc:.3f}"
    if sorted(a) == sorted(b):
        if subordinate_clause_reorder(original, rewrite):
            return None
        return "pure_permutation"
    return None


def rule_failure_v2(original: str, rewrite: str, span: str) -> str | None:
    reason = _base_rule_failure(original, rewrite, span)
    if reason:
        return reason
    reason = qualifier_set_mismatch(original, rewrite)
    if reason:
        return reason
    reason = fronting_violation(original, rewrite)
    if reason:
        return reason
    return word_edit_violation(original, rewrite)
