"""T7: E1-unit counterfactuals (unit-only edit, same numeral, factor 1000)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from text_utils import e1_unit_only_swap, highlight, outside_identical, replace_span

MAGNITUDE = "x1000"


def _diff(before: str, after: str, start: int, end: int, new_span: str, where: str) -> dict:
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


def _instance(
    base: dict,
    condition: str,
    claim: str,
    evidence: str,
    expected: str,
    diff: dict,
    claim_span: str,
    evidence_span: str,
    unit_pair: str,
) -> dict:
    return {
        "instance_id": f"{base['id']}__{condition}__{MAGNITUDE}",
        "base_id": base["id"],
        "type": base["type"],
        "condition": condition,
        "magnitude": MAGNITUDE,
        "claim": claim,
        "evidence": evidence,
        "expected_verdict": expected,
        "claim_span": claim_span,
        "evidence_span": evidence_span,
        "claim_c0": base["claim"],
        "evidence_c0": base["evidence"],
        "diff": diff,
        "flip_mechanism": base.get("flip_mechanism"),
        "dose_kind": base.get("dose_kind"),
        "subset": base.get("subset", "main"),
        "unit_pair": unit_pair,
        "unit_edit_kind": "numeral_fixed",
        "valid": True,
    }


def build_e1_unit_for_base(base: dict) -> Tuple[List[dict], List[dict]]:
    failures: List[dict] = []
    if base.get("type") != "DOSE":
        return [], failures
    claim0 = base["claim"]
    evid0 = base["evidence"]
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    e0, e1 = base["evidence_span_start"], base["evidence_span_end"]
    cspan = claim0[c0:c1]
    espan = evid0[e0:e1]
    if cspan != base.get("target_span_claim") or espan != base.get("target_span_evidence"):
        failures.append({"base_id": base["id"], "reason": "span_offset_mismatch"})
        return [], failures
    if cspan.replace(" ", "") != espan.replace(" ", ""):
        if cspan != espan:
            failures.append({"base_id": base["id"], "reason": "dose_span_not_verbatim"})
            return [], failures

    claim_swap = e1_unit_only_swap(cspan)
    evid_swap = e1_unit_only_swap(espan)
    if not claim_swap and not evid_swap:
        failures.append({"base_id": base["id"], "reason": "no_e1_unit_swap"})
        return [], failures

    instances: List[dict] = []
    if claim_swap:
        new_span, pair = claim_swap
        if new_span.replace(" ", "") == cspan.replace(" ", ""):
            failures.append({"base_id": base["id"], "reason": "claim_swap_noop"})
        else:
            claim_edit = _diff(claim0, claim0, c0, c1, new_span, "claim")
            if not claim_edit["confined_to_span"]:
                failures.append({"base_id": base["id"], "reason": "edit_not_confined", "where": "claim"})
            else:
                instances.append(
                    _instance(
                        base,
                        "E1-unit-claim",
                        claim_edit["text"],
                        evid0,
                        "FAIL",
                        {
                            "claim": {k: claim_edit[k] for k in claim_edit if k != "text"},
                            "evidence_unchanged": True,
                            "unit_pair": pair,
                        },
                        new_span,
                        espan,
                        pair,
                    )
                )
    if evid_swap:
        new_span, pair = evid_swap
        if new_span.replace(" ", "") == espan.replace(" ", ""):
            failures.append({"base_id": base["id"], "reason": "evid_swap_noop"})
        else:
            evid_edit = _diff(evid0, evid0, e0, e1, new_span, "evidence")
            if not evid_edit["confined_to_span"]:
                failures.append({"base_id": base["id"], "reason": "edit_not_confined", "where": "evidence"})
            else:
                instances.append(
                    _instance(
                        base,
                        "E1-unit-evid",
                        claim0,
                        evid_edit["text"],
                        "FAIL",
                        {
                            "evidence": {k: evid_edit[k] for k in evid_edit if k != "text"},
                            "claim_unchanged": True,
                            "unit_pair": pair,
                        },
                        cspan,
                        new_span,
                        pair,
                    )
                )
    return instances, failures


def valid_main_base_ids(root: Path) -> set[str]:
    from inv_families import valid_base_ids_from_instances

    ids: set[str] = set()
    inst_paths = [
        root / "data/v3/instances_main.jsonl",
        root / "data/expand/instances_cpu_early.jsonl",
        root / "data/expand/instances_main.jsonl",
    ]
    for path in inst_paths:
        if not path.is_file():
            continue
        with path.open() as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if (
                    row.get("valid")
                    and row.get("type") == "DOSE"
                    and row.get("subset") == "main"
                    and row.get("condition") == "C0"
                    and row.get("magnitude") == "none"
                ):
                    ids.add(row["base_id"])
    return ids


def load_bases_for_t7(root: Path) -> dict[str, dict]:
    from inv_families import load_bases

    bases = load_bases(root)
    expand_path = root / "data/expand/bases_main.jsonl"
    if expand_path.is_file() and expand_path.stat().st_size > 0:
        with expand_path.open() as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    if row.get("type") == "DOSE":
                        bases[row["id"]] = row
    return bases


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
        got, fail = build_e1_unit_for_base(base)
        failures.extend(fail)
        instances.extend(got)
    meta = {
        "valid_main_bases": len(valid_ids),
        "bases_with_bases_row": sum(1 for b in valid_ids if b in bases),
        "skipped_no_base_row": skipped,
        "instances": len(instances),
        "failed_bases": len({f["base_id"] for f in failures}),
    }
    return instances, failures, meta
