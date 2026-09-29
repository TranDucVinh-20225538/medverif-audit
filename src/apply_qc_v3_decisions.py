"""Apply decision-log G/H/I/J to v3 audit rows. CPU-only; keeps invalid rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from human_review_overrides import apply_human_overrides
from non_dose_targets import invalidate_non_dose_row
from perturb import perturb_one
from qc_v3 import (
    dose_kind_v3,
    dose_range_endpoint,
    domain_kind_rule,
    extra_hedges,
    flip_bad_term,
    focus_sentence,
    main_polarity_domain,
    neighbor_text,
    ocr_hits,
    polarity_flip_allowed,
    sentence_rule_failure,
)
from text_utils import rephrase_polarity_cue

ROOT = Path("/data2/hpcshared/medverif-audit")
_EXPAND = __import__("os").environ.get("MEDVERIF_QC_V3_EXPAND") == "1"
V2 = ROOT / ("data/expand" if _EXPAND else "data/v2")
OUT = ROOT / ("data/expand/v3" if _EXPAND else "data/v3")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(path: Path, rows: list[dict], *, allow_shrink: bool | None = None) -> None:
    from safe_jsonl import write_jsonl_atomic

    write_jsonl_atomic(path, rows, allow_shrink=allow_shrink)


def load_bases() -> dict[str, dict]:
    found = {}
    for name in ("bases_main.jsonl", "bases_threshold.jsonl", "bases_scope_excluded.jsonl"):
        for row in read_jsonl(V2 / name):
            found[row["id"]] = row
    return found


def base_meta(base: dict) -> dict:
    claim = base.get("claim") or ""
    target_field = base.get("target_sentence") or ""
    span = base.get("target_span_claim") or base.get("target_span_evidence") or ""
    target = focus_sentence(target_field, span)
    evidence = base.get("evidence") or ""
    c0 = claim.find(span) if span else -1
    if c0 < 0:
        c0, c1 = base.get("claim_span_start", 0), base.get("claim_span_end", 0)
    else:
        c1 = c0 + len(span)
    t0 = target.find(span) if span else -1
    t1 = t0 + len(span) if t0 >= 0 else 0
    target_ocr = ocr_hits(target)
    neigh_ocr = ocr_hits(neighbor_text(evidence, target))
    info = {
        "subset": base.get("subset") or "main",
        "ocr_noise": bool(neigh_ocr) and not target_ocr,
        "c0_drift": bool(extra_hedges(claim, target)),
        "c0_qc_fail": base.get("c0_qc_fail"),
        "dose_kind": None,
        "domain_kind": None,
        "flip_block": None,
        "range_endpoint": False,
    }
    if base["type"] == "DOSE":
        info["dose_kind"] = dose_kind_v3(claim, target, c0, c1)
        info["range_endpoint"] = dose_range_endpoint(claim, span)
        if info["range_endpoint"] and info["subset"] == "main":
            info["subset"] = "range"
    elif base["type"] == "POLARITY":
        info["domain_kind"] = domain_kind_rule(claim, target)
        info["flip_block"] = polarity_flip_allowed(claim, span, base["id"])
    return info


def rebuild_base_instances(base: dict, meta: dict) -> list[dict]:
    row = dict(base)
    row["subset"] = meta.get("subset") or row.get("subset") or "main"
    if meta.get("flip_block"):
        row["_skip_flip"] = True
    instances, failed = perturb_one(row)
    if failed:
        return []
    for inst in instances:
        inst["dose_kind"] = meta.get("dose_kind") if inst["type"] == "DOSE" else None
        inst["domain_kind"] = meta.get("domain_kind") if inst["type"] == "POLARITY" else None
        inst["ocr_noise"] = meta["ocr_noise"]
        inst["c0_drift"] = meta["c0_drift"]
        inst["subset"] = meta.get("subset") or inst.get("subset") or "main"
        inst["valid"] = True
        inst["invalid_reason"] = None
    return instances


def apply_validity(inst: dict, meta: dict, flip_block: str | None) -> None:
    invalid: str | None = None
    if inst.get("condition") == "C0" and meta.get("c0_qc_fail"):
        invalid = str(meta["c0_qc_fail"])
    elif inst.get("magnitude") == "paraphrase" or inst["instance_id"].endswith("paraphrase_v3"):
        invalid = "inv_paraphrase_regen"
    elif (
        inst.get("magnitude") == "rephrase"
        and inst.get("condition") == "INV-claim"
        and inst.get("type") == "POLARITY"
    ):
        diff = inst.get("diff") or {}
        if diff.get("rephrase_nonequivalent") or (
            (inst.get("claim") or "") == (inst.get("claim_c0") or "")
        ):
            invalid = "pol_rephrase_nonequivalent"
        else:
            reason = sentence_rule_failure(inst.get("claim") or "")
            if reason:
                invalid = f"sentence:{reason}"
            elif meta.get("subset") not in (None, "main"):
                invalid = "pol_rephrase_not_main"
            elif not main_polarity_domain(meta.get("domain_kind")):
                invalid = f"pol_rephrase_domain:{meta.get('domain_kind')}"
    elif meta.get("subset") == "excluded_scope":
        invalid = "scope"
    elif inst["type"] == "POLARITY" and inst.get("magnitude") == "flip" and flip_block:
        invalid = flip_block
    elif (
        inst["type"] == "POLARITY"
        and inst["condition"] == "C0"
        and meta.get("subset") == "main"
        and not main_polarity_domain(meta.get("domain_kind"))
    ):
        invalid = f"domain_not_treatment:{meta.get('domain_kind')}"

    if invalid:
        inst["valid"] = False
        inst["invalid_reason"] = invalid
    else:
        inst["valid"] = True
        inst["invalid_reason"] = None
    if inst.get("type") == "DOSE" and inst.get("condition") == "C0":
        invalidate_non_dose_row(inst)
        if inst.get("invalid_reason") == "non_dose_target":
            inst["valid"] = False
    if invalid != "inv_paraphrase_regen":
        apply_human_overrides(inst)


def valid_counts(rows: list[dict]) -> dict:
    c = Counter()
    for row in rows:
        if not row.get("valid"):
            continue
        if row.get("subset") not in {"main", "threshold", "range"}:
            continue
        c[(row["type"], row["condition"], row.get("subset", "main"))] += 1
    return {f"{a}|{b}|{c}": n for (a, b, c), n in sorted(c.items())}


def main() -> None:
    bases = load_bases()
    audit = read_jsonl(OUT / "instances_audit.jsonl")
    if not audit:
        raise SystemExit("missing instances_audit.jsonl; run prepare_v3 first")

    by_base: dict[str, list[dict]] = defaultdict(list)
    for row in audit:
        by_base[row["base_id"]].append(row)

    metas = {bid: base_meta(bases[bid]) for bid in bases}
    rebuild_ids = set()
    for bid, meta in metas.items():
        if bid not in by_base:
            continue
        if meta.get("flip_block") or meta.get("range_endpoint"):
            rebuild_ids.add(bid)
        # Rebuild POLARITY/DOSE for template INV and natural unit INV rules.
        if bases[bid]["type"] in {"POLARITY", "DOSE"}:
            rebuild_ids.add(bid)

    new_audit = []
    for bid, rows in by_base.items():
        if bid in rebuild_ids and bid in bases:
            fresh = rebuild_base_instances(bases[bid], metas[bid])
            if fresh:
                for inst in fresh:
                    apply_validity(inst, metas[bid], metas[bid].get("flip_block"))
                new_audit.extend(fresh)
                continue
        for inst in rows:
            meta = metas.get(bid, {})
            inst["dose_kind"] = meta.get("dose_kind") if inst["type"] == "DOSE" else inst.get("dose_kind")
            inst["domain_kind"] = meta.get("domain_kind") if inst["type"] == "POLARITY" else inst.get("domain_kind")
            inst["ocr_noise"] = meta.get("ocr_noise", inst.get("ocr_noise"))
            inst["c0_drift"] = meta.get("c0_drift", inst.get("c0_drift"))
            if meta.get("subset"):
                inst["subset"] = meta["subset"]
            apply_validity(inst, meta, meta.get("flip_block"))
            new_audit.append(inst)

    # Paraphrase todo: all valid C0 main/threshold bases (LLM regen later).
    todo = []
    flips = []
    seen_todo = set()
    seen_flip = set()
    for inst in new_audit:
        if inst["condition"] != "C0" or not inst.get("valid"):
            continue
        bid = inst["base_id"]
        base = bases.get(bid)
        if not base or inst.get("subset") not in {"main", "threshold"}:
            continue
        if bid in seen_todo:
            continue
        seen_todo.add(bid)
        todo.append({
            "base_id": bid,
            "type": inst["type"],
            "subset": inst["subset"],
            "claim": inst["claim"],
            "span": inst.get("claim_span") or base.get("target_span_claim") or "",
            "dose_kind": inst.get("dose_kind"),
            "domain_kind": inst.get("domain_kind"),
            "need_dose_kind": inst.get("dose_kind") == "unclear",
            "need_domain": inst.get("domain_kind") == "unclear",
        })
        if inst["type"] == "POLARITY" and bid not in seen_flip:
            seen_flip.add(bid)
            flips.append({"base_id": bid, "claim": inst["claim"], "span": inst.get("claim_span") or ""})

    # Reset LLM paraphrase artifacts (G) — opt-in only (avoid accidental truncation).
    import os
    from safe_jsonl import backup_file, write_jsonl_atomic

    para_path = OUT / "para_attempts.jsonl"
    if os.environ.get("MEDVERIF_QC_V3_RESET_PARA", "").lower() in ("1", "true", "yes"):
        pre = OUT / "para_attempts.pre_qc_v3.jsonl"
        bak = backup_file(para_path)
        if para_path.exists() and para_path.stat().st_size > 0:
            pre.write_bytes(para_path.read_bytes())
        write_jsonl_atomic(para_path, [], allow_shrink=True)
        if bak:
            print(json.dumps({"para_attempts_backup": str(bak), "pre_qc_copy": str(pre)}))
    write_jsonl(OUT / "paraphrase_todo.jsonl", todo)
    write_jsonl(OUT / "flip_fluency_todo.jsonl", flips)
    write_jsonl(OUT / "instances_audit.jsonl", new_audit)

    main_rows = [r for r in new_audit if r.get("valid") and r.get("subset") == "main"]
    thr_rows = [r for r in new_audit if r.get("valid") and r.get("subset") == "threshold"]
    range_rows = [r for r in new_audit if r.get("valid") and r.get("subset") == "range"]
    write_jsonl(OUT / "instances_main.jsonl", main_rows)
    write_jsonl(OUT / "instances_threshold.jsonl", thr_rows)
    write_jsonl(OUT / "instances_range.jsonl", range_rows)

    # cpu_early: main + threshold, no paraphrase magnitude
    cpu_early = [
        r for r in main_rows + thr_rows
        if r.get("magnitude") != "paraphrase"
    ]
    write_jsonl(OUT / "instances_cpu_early.jsonl", cpu_early)
    write_jsonl(OUT / "instances_cpu_main.jsonl", [r for r in main_rows if r.get("magnitude") != "paraphrase"])
    write_jsonl(OUT / "instances_cpu_threshold.jsonl", [r for r in thr_rows if r.get("magnitude") != "paraphrase"])

    polarity_unclear = sum(
        1 for r in new_audit
        if r["type"] == "POLARITY" and r["condition"] == "C0" and r.get("domain_kind") == "unclear"
    )
    report = {
        "rebuilt_bases": sorted(rebuild_ids),
        "valid_n_type_condition": valid_counts(new_audit),
        "valid_main_instances": len(main_rows),
        "valid_threshold_instances": len(thr_rows),
        "valid_range_instances": len(range_rows),
        "cpu_early_instances": len(cpu_early),
        "paraphrase_todo": len(todo),
        "polarity_domain_unclear_c0": polarity_unclear,
        "ocr_noise_main_bases": sum(
            1 for r in new_audit if r["condition"] == "C0" and r.get("subset") == "main" and r.get("ocr_noise")
        ),
        "sensitivity_exclude_ocr_n": sum(
            1 for r in cpu_early if not r.get("ocr_noise")
        ),
    }
    (OUT / "qc_v3_apply_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
