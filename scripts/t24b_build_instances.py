#!/usr/bin/env python3
"""T24b: rule-based C0 / unit-up / unit-down / value×10 on author-approved Y cohort."""

from __future__ import annotations

import csv
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "src"))

from text_utils import DOSE_RE, replace_span, scale_dose_span, unit_swap_numeral_fixed  # noqa: E402

LABELS = ROOT / "qc/t24_labels.csv"
REVIEW = ROOT / "qc/t24_review.csv"
OUT = ROOT / "data/t24/instances_t24b.jsonl"
LOG = ROOT / "notes/t24b_edit_log.jsonl"
MANIFEST = ROOT / "notes/t24b_build_manifest.json"

DUP_RE = re.compile(r"trùng\s+T24_\d+", re.I)


def is_duplicate_note(note: str) -> bool:
    note = note or ""
    return bool(DUP_RE.search(note) or "Dòng trùng" in note)


def load_review() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with REVIEW.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            out[row["question_id"]] = row
    return out


def load_cohort() -> list[dict]:
    labels = list(csv.DictReader(LABELS.open(encoding="utf-8-sig")))
    review = load_review()
    cohort: list[dict] = []
    for lab in labels:
        if lab["same_quantity_same_context"].strip().upper() != "Y":
            continue
        if is_duplicate_note(lab.get("note") or ""):
            continue
        if lab["question_id"] == "T24_003":
            continue
        rev = review.get(lab["question_id"])
        if not rev:
            continue
        cohort.append({**rev, **lab})
    return cohort


def locate_span(answer: str, hint: str) -> tuple[int, int, str] | None:
    hint = (hint or "").strip()
    if not hint:
        return None
    norm = hint.replace(" ", "")
    for m in DOSE_RE.finditer(answer or ""):
        if m.group(0).replace(" ", "") == norm or m.group(0).strip() == hint:
            return m.start(), m.end(), m.group(0)
    idx = (answer or "").find(hint)
    if idx >= 0:
        return idx, idx + len(hint), hint
    return None


def apply_edit(answer: str, loc: tuple[int, int, str], new_span: str) -> str:
    s, e, _ = loc
    return replace_span(answer, s, e, new_span)


def build_row(
    qid: str,
    rev: dict,
    *,
    condition: str,
    claim: str,
    span_after: str,
    edit_kind: str,
    expected: str,
    extra: dict,
) -> dict:
    return {
        "instance_id": f"{qid}__{condition}",
        "question_id": qid,
        "base_id": rev.get("base_id") or qid,
        "type": "DOSE",
        "subset": "t24b",
        "condition": condition,
        "claim": claim,
        "evidence": rev.get("evidence_passage") or "",
        "expected_verdict": expected,
        "claim_span": span_after,
        "evidence_span": rev.get("evidence_dose_span") or "",
        "valid": True,
        "t24b_edit_kind": edit_kind,
        **extra,
    }


def main() -> None:
    cohort = load_cohort()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if LOG.is_file():
        LOG.unlink()
    instances: list[dict] = []
    skips: list[dict] = []
    for rev in cohort:
        qid = rev["question_id"]
        answer = rev.get("generated_answer") or ""
        hint = rev.get("answer_dose_span") or ""
        loc = locate_span(answer, hint)
        if not loc:
            skips.append({"question_id": qid, "reason": "span_not_located", "hint": hint})
            continue
        _, _, surf = loc

        # C0
        instances.append(
            build_row(
                qid,
                rev,
                condition="T24b-C0",
                claim=answer,
                span_after=surf,
                edit_kind="none",
                expected="PASS",
                extra={"diff": {"where": "none", "span_before": surf, "span_after": surf}},
            )
        )

        up = unit_swap_numeral_fixed(surf, "up")
        down = unit_swap_numeral_fixed(surf, "down")
        try:
            x10 = scale_dose_span(surf, Decimal("10"))
        except ValueError:
            x10 = None

        edits: list[tuple[str, str | None, str, str, str]] = [
            ("unit_up", up[0] if up else None, up[1] if up else "", "T24b-unit-up", "FAIL"),
            ("unit_down", down[0] if down else None, down[1] if down else "", "T24b-unit-down", "FAIL"),
            ("value_x10", x10, "value×10", "T24b-value-x10", "FAIL"),
        ]
        for kind, new_span, pair, cond, exp in edits:
            if not new_span:
                skips.append({"question_id": qid, "reason": f"no_{kind}_edit", "span": surf})
                continue
            new_answer = apply_edit(answer, loc, new_span)
            log = {
                "question_id": qid,
                "condition": cond,
                "edit_kind": kind,
                "span_before": surf,
                "span_after": new_span,
                "unit_pair": pair,
            }
            with LOG.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(log, ensure_ascii=False) + "\n")
            instances.append(
                build_row(
                    qid,
                    rev,
                    condition=cond,
                    claim=new_answer,
                    span_after=new_span,
                    edit_kind=kind,
                    expected=exp,
                    extra={
                        "diff": {
                            "claim": {
                                "span_before": surf,
                                "span_after": new_span,
                                "unit_pair": pair,
                            }
                        }
                    },
                )
            )

    with OUT.open("w", encoding="utf-8") as handle:
        for row in instances:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    appendix_n = sum(
        1
        for row in csv.DictReader(LABELS.open(encoding="utf-8-sig"))
        if row["same_quantity_same_context"].strip().upper() == "N" and not is_duplicate_note(row.get("note") or "")
    )
    manifest = {
        "p1_questions": len(cohort),
        "instances_written": len(instances),
        "skips": skips,
        "appendix_n_unique": appendix_n,
        "excluded": ["T24_003", "duplicate rows (note)", "N labels (appendix)"],
        "prevalence": "0/56 author Y answers re-express a unit (T24 prevalence; not in-the-wild conversion)",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
