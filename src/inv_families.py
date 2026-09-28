"""Rule-based DOSE INV-claim families (frequency, route, numerals, number format)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator

from text_utils import DOSE_RE, highlight, levenshtein, outside_identical, replace_span

# Frequency: pairwise swaps within each equivalence group (both directions).
FREQ_GROUPS: tuple[tuple[str, ...], ...] = (
    ("bid", "twice daily", "every 12 hours"),
    ("tid", "three times daily"),
    ("qd", "once daily"),
    ("qid", "four times daily"),
)

ROUTE_PAIRS: tuple[tuple[str, str], ...] = (
    ("IV", "intravenously"),
    ("IM", "intramuscularly"),
    ("PO", "orally"),
    ("SC", "subcutaneously"),
    ("SQ", "subcutaneously"),
)

WORD_TO_DIGIT = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}
DIGIT_TO_WORD = {v: k for k, v in WORD_TO_DIGIT.items()}

FAMILY_MAG = {
    "frequency": "inv_frequency",
    "route": "inv_route",
    "numerals": "inv_numerals",
    "format": "inv_format",
}


@dataclass(frozen=True)
class Edit:
    family: str
    span_before: str
    span_after: str
    start: int
    end: int
    tag: str


def _freq_edits(claim: str) -> list[Edit]:
    out: list[Edit] = []
    lower = claim.lower()
    for group in FREQ_GROUPS:
        for a in group:
            for b in group:
                if a == b:
                    continue
                pat = re.compile(rf"(?<![A-Za-z0-9]){re.escape(a)}(?![A-Za-z0-9])", re.I)
                for m in pat.finditer(claim):
                    # preserve case of matched slice for span_before
                    seg = claim[m.start() : m.end()]
                    repl = b if seg.lower() == a.lower() else b
                    if seg.isupper() and len(b) <= 4:
                        repl = b.upper()
                    elif seg[0].isupper():
                        repl = b[:1].upper() + b[1:] if b else b
                    out.append(
                        Edit(
                            "frequency",
                            seg,
                            repl,
                            m.start(),
                            m.end(),
                            f"{a}_to_{b}",
                        )
                    )
    return out


def _route_edits(claim: str) -> list[Edit]:
    out: list[Edit] = []
    pairs = list(ROUTE_PAIRS)
    # bidirectional route pairs (dedupe SC/SQ both → subcutaneously)
    seen: set[tuple[str, str]] = set()
    expanded: list[tuple[str, str]] = []
    for a, b in pairs:
        if (a, b) not in seen:
            expanded.append((a, b))
            seen.add((a, b))
        if (b, a) not in seen and not b.isupper() or len(b) > 3:
            expanded.append((b, a))
            seen.add((b, a))
    for a, b in expanded:
        if a in {"IV", "IM", "PO", "SC", "SQ"}:
            pat = re.compile(rf"\b{re.escape(a)}\b")
        else:
            pat = re.compile(rf"(?<![A-Za-z0-9]){re.escape(a)}(?![A-Za-z0-9])", re.I)
        for m in pat.finditer(claim):
            seg = claim[m.start() : m.end()]
            repl = b
            if a in {"IV", "IM", "PO", "SC", "SQ"} and seg.isupper():
                repl = b  # long form lower case
            out.append(Edit("route", seg, repl, m.start(), m.end(), f"{a}_to_{b}"))
    return out


def _dose_spans(claim: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in DOSE_RE.finditer(claim)]


def _overlaps_dose(start: int, end: int, dose_spans: list[tuple[int, int]]) -> bool:
    for ds, de in dose_spans:
        if start < de and end > ds:
            return True
    return False


def _numeral_edits(claim: str) -> list[Edit]:
    out: list[Edit] = []
    dose_spans = _dose_spans(claim)
    for word, digit in WORD_TO_DIGIT.items():
        pat = re.compile(rf"\b{word}\b", re.I)
        for m in pat.finditer(claim):
            if _overlaps_dose(m.start(), m.end(), dose_spans):
                continue
            seg = claim[m.start() : m.end()]
            repl = digit
            out.append(Edit("numerals", seg, repl, m.start(), m.end(), f"{word}_to_{digit}"))
    for digit, word in DIGIT_TO_WORD.items():
        pat = re.compile(rf"\b{re.escape(digit)}\b")
        for m in pat.finditer(claim):
            if _overlaps_dose(m.start(), m.end(), dose_spans):
                continue
            seg = claim[m.start() : m.end()]
            repl = word if seg.islower() else word.capitalize()
            out.append(Edit("numerals", seg, repl, m.start(), m.end(), f"{digit}_to_{word}"))
    return out


def _format_edits(claim: str) -> list[Edit]:
    out: list[Edit] = []
    dose_spans = _dose_spans(claim)
    pat = re.compile(r"\b(\d{1,3}(?:,\d{3})+)\b")
    for m in pat.finditer(claim):
        if _overlaps_dose(m.start(), m.end(), dose_spans):
            continue
        seg = m.group(1)
        repl = seg.replace(",", "")
        if repl == seg:
            continue
        out.append(Edit("format", seg, repl, m.start(), m.end(), "comma_strip"))
    pat2 = re.compile(r"\b(\d{4,})\b")
    for m in pat2.finditer(claim):
        if _overlaps_dose(m.start(), m.end(), dose_spans):
            continue
        seg = m.group(1)
        if len(seg) < 4 or "," in seg:
            continue
        repl = f"{int(seg):,}"
        out.append(Edit("format", seg, repl, m.start(), m.end(), "comma_add"))
    return out


def find_edits(claim: str) -> list[Edit]:
    edits: list[Edit] = []
    edits.extend(_freq_edits(claim))
    edits.extend(_route_edits(claim))
    edits.extend(_numeral_edits(claim))
    edits.extend(_format_edits(claim))
    # dedupe same (family, start, end, span_after)
    seen: set[tuple] = set()
    uniq: list[Edit] = []
    for e in edits:
        key = (e.family, e.start, e.end, e.span_after.lower())
        if key in seen:
            continue
        seen.add(key)
        if e.span_before == e.span_after:
            continue
        uniq.append(e)
    return uniq


def _instance_from_edit(base: dict, edit: Edit) -> dict | None:
    claim0 = base["claim"]
    evid0 = base["evidence"]
    cspan = claim0[base["claim_span_start"] : base["claim_span_end"]]
    espan = evid0[base["evidence_span_start"] : base["evidence_span_end"]]
    new_claim = replace_span(claim0, edit.start, edit.end, edit.span_after)
    if new_claim == claim0:
        return None
    if not outside_identical(claim0, new_claim, edit.start, edit.end, edit.span_after):
        return None
    mag = FAMILY_MAG[edit.family]
    tag = edit.tag.replace(" ", "_")
    iid = f"{base['id']}__INV-claim__{mag}__{tag}"
    diff = {
        "claim": {
            "where": "claim",
            "span_before": edit.span_before,
            "span_after": edit.span_after,
            "edit_distance": levenshtein(claim0, new_claim),
            "confined_to_span": True,
            "highlight_before": highlight(claim0, edit.start, edit.end),
            "highlight_after": highlight(new_claim, edit.start, edit.start + len(edit.span_after)),
        },
        "evidence_unchanged": True,
        "inv_family": edit.family,
        "inv_tag": edit.tag,
    }
    return {
        "instance_id": iid,
        "base_id": base["id"],
        "type": "DOSE",
        "condition": "INV-claim",
        "magnitude": mag,
        "claim": new_claim,
        "evidence": evid0,
        "expected_verdict": "PASS",
        "claim_span": cspan,
        "evidence_span": espan,
        "claim_c0": claim0,
        "evidence_c0": evid0,
        "diff": diff,
        "flip_mechanism": None,
        "dose_kind": base.get("dose_kind"),
        "subset": base.get("subset", "main"),
        "valid": True,
        "invalid_reason": None,
    }


def valid_base_ids_from_instances(paths: Iterable) -> set[str]:
    from pathlib import Path
    import json

    out: set[str] = set()
    for path in paths:
        p = Path(path)
        if not p.is_file():
            continue
        with p.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("valid") and row.get("condition") == "C0" and row.get("type") == "DOSE":
                    out.add(row["base_id"])
    return out


def load_bases(root) -> dict[str, dict]:
    from pathlib import Path
    import json

    root = Path(root)
    by_id: dict[str, dict] = {}
    for rel in (
        "data/v2/bases_main.jsonl",
        "data/v2/bases_threshold.jsonl",
        "data/expand/bases_main.jsonl",
    ):
        path = root / rel
        if not path.is_file() or path.stat().st_size == 0:
            continue
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if line:
                    row = json.loads(line)
                    if row.get("type") == "DOSE":
                        by_id[row["id"]] = row
    return by_id


def generate_inv_family_instances(root) -> tuple[list[dict], dict[str, int]]:
    from pathlib import Path

    root = Path(root)
    inst_paths = [
        root / "data/v3/instances_main.jsonl",
        root / "data/v3/instances_threshold.jsonl",
        root / "data/expand/instances_cpu_early.jsonl",
    ]
    valid_ids = valid_base_ids_from_instances(inst_paths)
    bases = load_bases(root)
    instances: list[dict] = []
    counts = {FAMILY_MAG[k]: 0 for k in FAMILY_MAG}
    for base_id in sorted(valid_ids):
        base = bases.get(base_id)
        if base is None:
            continue
        for edit in find_edits(base["claim"]):
            inst = _instance_from_edit(base, edit)
            if inst is None:
                continue
            instances.append(inst)
            counts[inst["magnitude"]] += 1
    return instances, counts
