#!/usr/bin/env python3
"""Rule-classify ecological answer vs evidence target dose."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import DOSE_RE, natural_unit_conversion, parse_decimal  # noqa: E402

FREQ_TOKENS = re.compile(
    r"\b(bid|tid|qd|qid|twice daily|three times daily|once daily|four times daily|"
    r"every \d+ hours|daily|weekly|biweekly)\b",
    re.I,
)


def primary_dose(text: str) -> tuple[str, str] | None:
    matches = list(DOSE_RE.finditer(text or ""))
    if not matches:
        return None
    m = matches[0]
    return m.group(0).strip(), f"{m.group(1)} {m.group(2)}"


def classify_answer(answer: str, evidence: str, target_span: str) -> str:
    ans = primary_dose(answer)
    tgt = primary_dose(target_span) or primary_dose(evidence)
    if ans is None:
        return "omitted"
    ans_span, _ = ans
    if tgt is None:
        return "changed_value"
    tgt_span, _ = tgt
    if ans_span.replace(" ", "").lower() == tgt_span.replace(" ", "").lower():
        return "exact"
    conv = natural_unit_conversion(tgt_span)
    if conv and ans_span.replace(" ", "").lower() == conv.replace(" ", "").lower():
        return "unit_converted"
    try:
        a_num = parse_decimal(DOSE_RE.search(ans_span).group(1))  # type: ignore[union-attr]
        t_num = parse_decimal(DOSE_RE.search(tgt_span).group(1))  # type: ignore[union-attr]
        a_u = DOSE_RE.search(ans_span).group(2)  # type: ignore[union-attr]
        t_u = DOSE_RE.search(tgt_span).group(2)  # type: ignore[union-attr]
        if a_u == t_u and a_num != t_num:
            return "changed_value"
    except Exception:
        pass
    if FREQ_TOKENS.search(answer) and FREQ_TOKENS.search(evidence):
        return "frequency_rephrased"
    return "changed_value"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="inp", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for line in args.inp.open():
        if not line.strip():
            continue
        row = json.loads(line)
        row["eco_category"] = classify_answer(
            row.get("answer") or "",
            row.get("evidence") or "",
            row.get("target_span_evidence") or row.get("evidence_span") or "",
        )
        rows.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    from collections import Counter

    print(json.dumps(dict(Counter(r["eco_category"] for r in rows)), indent=2))


if __name__ == "__main__":
    main()
