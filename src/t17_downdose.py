"""T17: down-dose counterfactuals (value ÷2/÷10, unit ÷1000) on main DOSE bases."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import List, Tuple

from perturb import _dose_diff, _dose_factor_ok_in_context, _instance  # noqa: F401
from text_utils import (
    highlight,
    normalize_micro_sign,
    outside_identical,
    replace_span,
    scale_dose_span,
    unit_swap_numeral_fixed,
)
from t7_e1_unit import load_bases_for_t7, valid_main_base_ids


def _diff_unit(before: str, start: int, end: int, new_span: str, where: str) -> dict:
    edited = replace_span(before, start, end, new_span)
    from text_utils import levenshtein

    return {
        "where": where,
        "span_before": before[start:end],
        "span_after": new_span,
        "edit_distance": levenshtein(before, edited),
        "confined_to_span": outside_identical(before, edited, start, end, new_span),
        "highlight_before": highlight(before, start, end),
        "highlight_after": highlight(edited, start, start + len(new_span)),
        "text": edited,
    }


def _span_decimal_ok(span: str, factor: Decimal) -> bool:
    try:
        new = scale_dose_span(span.strip(), factor)
    except ValueError:
        return False
    num = new.split()[0]
    if "." in num and len(num.split(".", 1)[1]) > 2:
        return False
    return True


def _unit_down_span(span: str) -> Tuple[str, str] | None:
    swapped = unit_swap_numeral_fixed(span, "down")
    if not swapped:
        return None
    new_span, pair = swapped
    new_span = new_span.replace("µg", "mcg").replace("μg", "mcg")
    if new_span.replace(" ", "") == span.replace(" ", ""):
        return None
    return new_span, pair


def _already_micro_unit(span: str) -> bool:
    try:
        from text_utils import _dose_span_parts

        _, unit = _dose_span_parts(span)
    except ValueError:
        return True
    low = unit.lower()
    return low.startswith("mcg") or "µg" in unit or "μg" in unit or "microgram" in low


def build_for_base(base: dict) -> Tuple[List[dict], List[dict]]:
    failures: List[dict] = []
    if base.get("type") != "DOSE":
        return [], failures
    claim0 = normalize_micro_sign(base["claim"])
    evid0 = normalize_micro_sign(base["evidence"])
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    e0, e1 = base["evidence_span_start"], base["evidence_span_end"]
    cspan = claim0[c0:c1]
    espan = evid0[e0:e1]
    c0_id = f"{base['id']}__C0__none"
    out: List[dict] = []

    def add_value(mag: str, factor: Decimal, cond_suffix: str, side: str) -> None:
        start, end = (c0, c1) if side == "claim" else (e0, e1)
        text = claim0 if side == "claim" else evid0
        span = cspan if side == "claim" else espan
        if not _span_decimal_ok(span, factor):
            failures.append({"base_id": base["id"], "reason": f"{mag}_decimals", "side": side})
            return
        edit = _dose_diff(text, start, end, factor, side)
        if not edit["confined_to_span"]:
            failures.append({"base_id": base["id"], "reason": "edit_not_confined", "mag": mag, "side": side})
            return
        if not _dose_factor_ok_in_context(text, start, end, edit["span_after"], factor):
            failures.append({"base_id": base["id"], "reason": "dose_factor", "mag": mag, "side": side})
            return
        cond = f"E1-{mag}"
        row_suffix = cond_suffix
        other_claim = claim0 if side == "evid" else edit["text"]
        other_evid = edit["text"] if side == "evid" else evid0
        other_cspan = cspan if side == "evid" else edit["span_after"]
        other_espan = edit["span_after"] if side == "evid" else espan
        row = _instance(
            base,
            cond,
            mag,
            other_claim,
            other_evid,
            "FAIL",
            {side: {k: edit[k] for k in edit if k != "text"}, f"{('evidence' if side == 'claim' else 'claim')}_unchanged": True},
            other_cspan,
            other_espan,
        )
        row["instance_id"] = f"{base['id']}__{cond}__{row_suffix}__{mag}"
        row["edit_side"] = side
        row["c0_instance_id"] = c0_id
        row["t17_pack"] = True
        out.append(row)

    for mag, factor in (("down2", Decimal("0.5")), ("down10", Decimal("0.1"))):
        add_value(mag, factor, "claim", "claim")
        add_value(mag, factor, "evid", "evid")

    if not (_already_micro_unit(cspan) and _already_micro_unit(espan)):
        for side in ("claim", "evid"):
            start, end = (c0, c1) if side == "claim" else (e0, e1)
            text = claim0 if side == "claim" else evid0
            span = cspan if side == "claim" else espan
            if _already_micro_unit(span):
                continue
            unit_swap = _unit_down_span(span)
            if not unit_swap:
                failures.append({"base_id": base["id"], "reason": "no_unit_down", "side": side})
                continue
            new_span, pair = unit_swap
            edit = _diff_unit(text, start, end, new_span, side)
            if not edit["confined_to_span"]:
                failures.append({"base_id": base["id"], "reason": "edit_not_confined", "mag": "unit-down", "side": side})
                continue
            cond = "E1-unit-down"
            other_claim = claim0 if side == "evid" else edit["text"]
            other_evid = edit["text"] if side == "evid" else evid0
            other_cspan = cspan if side == "evid" else edit["span_after"]
            other_espan = edit["span_after"] if side == "evid" else espan
            row = _instance(
                base,
                cond,
                "unit-down",
                other_claim,
                other_evid,
                "FAIL",
                {side: {k: edit[k] for k in edit if k != "text"}, "unit_pair": pair},
                other_cspan,
                other_espan,
            )
            row["instance_id"] = f"{base['id']}__{cond}__{side}__unit-down"
            row["edit_side"] = side
            row["c0_instance_id"] = c0_id
            row["t17_pack"] = True
            out.append(row)

    return out, failures


def generate_all(root: Path) -> tuple[list[dict], list[dict], dict]:
    root = Path(root)
    valid_ids = valid_main_base_ids(root)
    bases = load_bases_for_t7(root)
    instances: list[dict] = []
    failures: list[dict] = []
    skipped = 0
    for bid in sorted(valid_ids):
        base = bases.get(bid)
        if base is None:
            skipped += 1
            continue
        got, fail = build_for_base(base)
        failures.extend(fail)
        instances.extend(got)
    meta = {
        "valid_main_bases": len(valid_ids),
        "skipped_no_base_row": skipped,
        "instances": len(instances),
        "failed_bases": len({f["base_id"] for f in failures}),
    }
    return instances, failures, meta
