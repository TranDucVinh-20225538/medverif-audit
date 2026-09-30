"""E2-unit: ×1000 unit swap on BOTH claim and evidence (faithful-but-absurd; expected PASS)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from t7_e1_unit import MAGNITUDE, _diff, load_bases_for_t7, valid_main_base_ids
from text_utils import e1_unit_only_swap, normalize_micro_sign


def build_e2_unit_for_base(base: dict) -> Tuple[List[dict], List[dict]]:
    failures: List[dict] = []
    if base.get("type") != "DOSE":
        return [], failures
    claim0 = normalize_micro_sign(base["claim"])
    evid0 = normalize_micro_sign(base["evidence"])
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    e0, e1 = base["evidence_span_start"], base["evidence_span_end"]
    cspan = claim0[c0:c1]
    espan = evid0[e0:e1]
    if cspan != base.get("target_span_claim") or espan != base.get("target_span_evidence"):
        failures.append({"base_id": base["id"], "reason": "span_offset_mismatch"})
        return [], failures

    claim_swap = e1_unit_only_swap(cspan)
    evid_swap = e1_unit_only_swap(espan)
    if not claim_swap or not evid_swap:
        failures.append({"base_id": base["id"], "reason": "no_unit_swap_both_sides"})
        return [], failures
    new_c, pair_c = claim_swap
    new_e, pair_e = evid_swap
    if pair_c != pair_e:
        failures.append({"base_id": base["id"], "reason": "claim_evid_unit_pair_mismatch", "pair_c": pair_c, "pair_e": pair_e})
        return [], failures
    if new_c.replace(" ", "") == cspan.replace(" ", "") and new_e.replace(" ", "") == espan.replace(" ", ""):
        failures.append({"base_id": base["id"], "reason": "swap_noop"})
        return [], failures

    claim_edit = _diff(claim0, claim0, c0, c1, new_c, "claim")
    evid_edit = _diff(evid0, evid0, e0, e1, new_e, "evidence")
    if not claim_edit["confined_to_span"] or not evid_edit["confined_to_span"]:
        failures.append({"base_id": base["id"], "reason": "edit_not_confined"})
        return [], failures

    inst = {
        "instance_id": f"{base['id']}__E2-unit__{MAGNITUDE}",
        "base_id": base["id"],
        "type": base["type"],
        "condition": "E2-unit",
        "magnitude": MAGNITUDE,
        "claim": claim_edit["text"],
        "evidence": evid_edit["text"],
        "expected_verdict": "PASS",
        "claim_span": new_c,
        "evidence_span": new_e,
        "claim_c0": base["claim"],
        "evidence_c0": base["evidence"],
        "diff": {
            "claim": {k: claim_edit[k] for k in claim_edit if k != "text"},
            "evidence": {k: evid_edit[k] for k in evid_edit if k != "text"},
            "unit_pair": pair_c,
        },
        "flip_mechanism": base.get("flip_mechanism"),
        "dose_kind": base.get("dose_kind"),
        "subset": base.get("subset", "main"),
        "unit_pair": pair_c,
        "unit_edit_kind": "numeral_fixed",
        "valid": True,
    }
    return [inst], failures


def generate_e2_unit_t7(root: Path) -> tuple[list[dict], list[dict], dict]:
    root = Path(root)
    t7_bases = {r["base_id"] for r in _read_t7(root)}
    valid_ids = valid_main_base_ids(root) & t7_bases
    bases = load_bases_for_t7(root)
    instances: list[dict] = []
    failures: list[dict] = []
    skipped = 0
    for bid in sorted(valid_ids):
        base = bases.get(bid)
        if base is None:
            skipped += 1
            continue
        got, fail = build_e2_unit_for_base(base)
        failures.extend(fail)
        instances.extend(got)
    meta = {
        "t7_bases": len(t7_bases),
        "eligible_bases": len(valid_ids),
        "instances": len(instances),
        "skipped_no_base_row": skipped,
        "failed_bases": len({f["base_id"] for f in failures}),
    }
    return instances, failures, meta


def _read_t7(root: Path) -> list[dict]:
    import json

    path = root / "data/t7/instances_e1_unit.jsonl"
    return [json.loads(line) for line in path.open() if line.strip()]
