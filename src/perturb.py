"""Span-local counterfactuals. Rules only. INV meaning is checked later by Phi-4."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Dict, List

from text_utils import (
    convert_dose_span,
    flip_cue,
    flip_mechanism,
    highlight,
    levenshtein,
    outside_identical,
    parse_decimal,
    replace_span,
    rephrase_polarity_cue,
    scale_dose_span,
)


def _diff(before: str, after: str, start: int, end: int, new_span: str, where: str) -> dict:
    edited = replace_span(before, start, end, new_span)
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


def _dose_factor_ok(old_span: str, new_span: str, factor: Decimal) -> bool:
    old = parse_decimal(old_span.split()[0])
    new = parse_decimal(new_span.split()[0])
    return new / old == factor


def _instance(
    base: dict,
    condition: str,
    magnitude: str,
    claim: str,
    evidence: str,
    expected: str,
    diff: dict,
    claim_span: str,
    evidence_span: str,
) -> dict:
    return {
        "instance_id": f"{base['id']}__{condition}__{magnitude}",
        "base_id": base["id"],
        "type": base["type"],
        "condition": condition,
        "magnitude": magnitude,
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
    }


def perturb_one(base: dict) -> tuple[List[dict], List[dict]]:
    """Return (instances, failures). Failures mean the whole base is dropped."""
    failures = []
    instances = []
    claim0 = base["claim"]
    evid0 = base["evidence"]
    c0 = base["claim_span_start"]
    c1 = base["claim_span_end"]
    e0 = base["evidence_span_start"]
    e1 = base["evidence_span_end"]
    cspan = claim0[c0:c1]
    espan = evid0[e0:e1]
    if cspan != base["target_span_claim"] or espan != base["target_span_evidence"]:
        failures.append({"base_id": base["id"], "reason": "span_offset_mismatch"})
        return [], failures
    if base["type"] == "DOSE" and cspan.replace(" ", "") != espan.replace(" ", ""):
        # Verbatim fact: same number and unit. Spacing may differ only if both strings equal.
        if cspan != espan:
            failures.append({"base_id": base["id"], "reason": "dose_span_not_verbatim"})
            return [], failures
    if base["type"] == "POLARITY" and cspan.lower() != espan.lower():
        failures.append({"base_id": base["id"], "reason": "polarity_span_not_verbatim"})
        return [], failures
    if base["type"] == "POLARITY":
        base = dict(base)
        base["flip_mechanism"] = flip_mechanism(espan)

    unchanged = {
        "where": "none",
        "span_before": cspan,
        "span_after": cspan,
        "edit_distance": 0,
        "confined_to_span": True,
        "highlight_before": highlight(claim0, c0, c1),
        "highlight_after": highlight(claim0, c0, c1),
        "evidence_highlight": highlight(evid0, e0, e1),
    }
    instances.append(_instance(base, "C0", "none", claim0, evid0, "PASS", unchanged, cspan, espan))

    try:
        if base["type"] == "DOSE":
            variants = []
            for factor, mag in ((Decimal(2), "x2"), (Decimal(10), "x10")):
                new_span = scale_dose_span(espan, factor)
                if not _dose_factor_ok(espan, new_span, factor):
                    raise ValueError(f"factor check failed for {mag}")
                variants.append((mag, new_span))
            inv_span = None
            try:
                inv_span = convert_dose_span(cspan)
            except ValueError:
                inv_span = None
        else:
            flipped = flip_cue(espan)
            variants = [("flip", flipped)]
            inv_span = None
    except ValueError as exc:
        failures.append({"base_id": base["id"], "reason": "rule_edit_failed", "detail": str(exc)})
        return [], failures

    for mag, new_span in variants:
        evid_edit = _diff(evid0, evid0, e0, e1, new_span, "evidence")
        claim_edit = _diff(claim0, claim0, c0, c1, new_span, "claim")
        if not evid_edit["confined_to_span"] or not claim_edit["confined_to_span"]:
            failures.append({"base_id": base["id"], "reason": "edit_not_confined", "magnitude": mag})
            return [], failures
        if base["type"] == "DOSE":
            factor = Decimal(10) if mag == "x10" else Decimal(2)
            if not _dose_factor_ok(espan, new_span, factor):
                failures.append({"base_id": base["id"], "reason": "dose_factor", "magnitude": mag})
                return [], failures
        both = {
            "evidence": {k: evid_edit[k] for k in evid_edit if k != "text"},
            "claim": {k: claim_edit[k] for k in claim_edit if k != "text"},
        }
        instances.append(_instance(
            base, "E1-evid", mag, claim0, evid_edit["text"], "FAIL",
            {"evidence": both["evidence"], "claim_unchanged": True},
            cspan, new_span,
        ))
        instances.append(_instance(
            base, "E1-claim", mag, claim_edit["text"], evid0, "FAIL",
            {"claim": both["claim"], "evidence_unchanged": True},
            new_span, espan,
        ))
        instances.append(_instance(
            base, "E2", mag, claim_edit["text"], evid_edit["text"], "PASS",
            both, new_span, new_span,
        ))

    if inv_span:
        inv_edit = _diff(claim0, claim0, c0, c1, inv_span, "claim")
        if inv_edit["confined_to_span"] and inv_edit["text"] != claim0:
            instances.append(_instance(
                base, "INV-claim", "unit_conversion",
                inv_edit["text"], evid0, "PASS",
                {"claim": {k: inv_edit[k] for k in inv_edit if k != "text"}, "evidence_unchanged": True},
                inv_span, espan,
            ))
    if base["type"] == "POLARITY":
        rep_ok = False
        rep_edit = None
        rep_span = cspan
        try:
            rep_span = rephrase_polarity_cue(cspan)
            rep_edit = _diff(claim0, claim0, c0, c1, rep_span, "claim")
            rep_ok = rep_edit["confined_to_span"] and rep_edit["text"] != claim0
        except ValueError:
            rep_edit = _diff(claim0, claim0, c0, c1, cspan, "claim")
        diff_payload = {
            "claim": {k: rep_edit[k] for k in rep_edit if k != "text"},
            "evidence_unchanged": True,
        }
        if not rep_ok:
            diff_payload["rephrase_nonequivalent"] = True
        instances.append(_instance(
            base, "INV-claim", "rephrase",
            rep_edit["text"] if rep_ok else claim0,
            evid0, "PASS",
            diff_payload,
            rep_span if rep_ok else cspan,
            espan,
        ))
    return instances, failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--failures", type=Path, required=True)
    args = parser.parse_args()
    instances: List[dict] = []
    failures: List[dict] = []
    n_base = 0
    with args.base.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            n_base += 1
            got, failed = perturb_one(json.loads(line))
            if failed:
                failures.extend(failed)
                continue
            instances.extend(got)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as handle:
        for row in instances:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    args.failures.write_text(json.dumps({
        "bases_read": n_base,
        "bases_failed": len({f["base_id"] for f in failures}),
        "instances": len(instances),
        "failures": failures,
    }, indent=2) + "\n")
    print(json.dumps({"bases_read": n_base, "instances": len(instances), "failed_bases": len(failures)}))


if __name__ == "__main__":
    main()
