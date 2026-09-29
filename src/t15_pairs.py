"""Rule-generated MiniCheck pairs for T15 fine-tuning."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple

from text_utils import (
    convert_dose_span,
    normalize_micro_sign,
    replace_span,
    scale_dose_in_context,
    unit_swap_numeral_fixed,
)


def dose_claim_from_sentence(sentence: str) -> str:
    return normalize_micro_sign(sentence.strip())


def _edit_sentence(sentence: str, local_start: int, local_end: int, new_span: str) -> str:
    return replace_span(sentence, local_start, local_end, new_span)


def pairs_for_base(base: dict) -> Tuple[List[dict], List[dict]]:
    """Return (pairs, failures) for one T15 base row."""
    failures: List[dict] = []
    sentence = dose_claim_from_sentence(base["target_sentence"])
    evidence = normalize_micro_sign(base["evidence"])
    ls = base["span_start_in_sentence"]
    le = base["span_end_in_sentence"]
    span = sentence[ls:le]
    if span != base.get("target_span"):
        failures.append({"base_id": base["base_id"], "reason": "span_mismatch"})
        return [], failures

    claim0 = sentence
    e0 = base["evidence_span_start"]
    e1 = base["evidence_span_end"]
    evid_span = evidence[e0:e1]

    pairs: List[dict] = []
    bid = base["base_id"]

    def add(pair_id: str, claim: str, evid: str, label: str, variant: str) -> None:
        pairs.append(
            {
                "pair_id": f"{bid}__{pair_id}",
                "base_id": bid,
                "variant": variant,
                "claim": claim,
                "evidence": evid,
                "label": label,
                "source_passage_id": base.get("source_passage_id"),
                "sentence_hash": base.get("sentence_hash"),
            }
        )

    add("C0", claim0, evidence, "SUPPORTED", "C0")

    try:
        conv_span = convert_dose_span(span)
        if conv_span.replace(" ", "") != span.replace(" ", ""):
            claim_conv = _edit_sentence(sentence, ls, le, conv_span)
            add("Conv", claim_conv, evidence, "SUPPORTED", "Conv")
    except ValueError:
        failures.append({"base_id": bid, "reason": "no_conv"})

    for direction, suffix in (("up", "Unit-up-claim"), ("down", "Unit-down-claim")):
        swap = unit_swap_numeral_fixed(span, direction)
        if swap:
            new_span, _pair = swap
            if new_span.replace(" ", "") != span.replace(" ", ""):
                add(
                    suffix,
                    _edit_sentence(sentence, ls, le, new_span),
                    evidence,
                    "UNSUPPORTED",
                    suffix,
                )

    try:
        new_sent, new_span = scale_dose_in_context(sentence, ls, le, Decimal(2))
        if new_span.replace(" ", "") != span.replace(" ", ""):
            add("Value-x2-claim", new_sent, evidence, "UNSUPPORTED", "Value-x2-claim")
    except ValueError:
        failures.append({"base_id": bid, "reason": "value_x2"})

    swap_e = unit_swap_numeral_fixed(evid_span, "up") or unit_swap_numeral_fixed(evid_span, "down")
    if swap_e:
        new_span, _pair = swap_e
        if new_span.replace(" ", "") != evid_span.replace(" ", ""):
            new_evid = replace_span(evidence, e0, e1, new_span)
            add("Unit-evid", claim0, new_evid, "UNSUPPORTED", "Unit-evid")

    try:
        new_evid, new_span = scale_dose_in_context(evidence, e0, e1, Decimal(2))
        if new_span.replace(" ", "") != evid_span.replace(" ", ""):
            add("Value-x2-evid", claim0, new_evid, "UNSUPPORTED", "Value-x2-evid")
    except ValueError:
        failures.append({"base_id": bid, "reason": "evid_value_x2"})

    if len(pairs) < 3:
        failures.append({"base_id": bid, "reason": "too_few_pairs", "n": len(pairs)})
        return [], failures
    return pairs, failures
