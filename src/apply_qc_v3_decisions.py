"""Apply decision-log G/H/I/J to v3 audit rows. CPU-only; keeps invalid rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

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
V2 = ROOT / "data" / "v2"
OUT = ROOT / "data" / "v3"


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


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


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
    row["subset"] = meta["subset"]
    if meta["flip_block"]:
        row["_skip_flip"] = True
    instances, failed = perturb_one(row)
    if failed:
        return []
    for inst in instances:
        inst["dose_kind"] = meta.get("dose_kind") if inst["type"] == "DOSE" else None
        inst["domain_kind"] = meta.get("domain_kind") if inst["type"] == "POLARITY" else None
        inst["ocr_noise"] = meta["ocr_noise"]
        inst["c0_drift"] = meta["c0_drift"]
        inst["subset"] = meta["subset"]
        inst["valid"] = True
        inst["invalid_reason"] = None
    return instances


def apply_validity(inst: dict, meta: dict, flip_block: str | None) -> None:
    if inst.get("magnitude") == "paraphrase" or inst["instance_id"].endswith("paraphrase_v3"):
        inst["valid"] = False
        inst["invalid_reason"] = "inv_paraphrase_regen"
        return
    if meta["subset"] == "excluded_scope":
        inst["valid"] = False
        inst["invalid_reason"] = "scope"
        return
    if inst["type"] == "POLARITY" and inst.get("magnitude") == "flip" and flip_block:
        inst["valid"] = False
        inst["invalid_reason"] = flip_block
        return
    if inst["type"] == "POLARITY" and inst["condition"] == "C0" and meta["subset"] == "main":
        if not main_polarity_domain(meta.get("domain_kind")):
            inst["valid"] = False
            inst["invalid_reason"] = f"domain_not_treatment:{meta.get('domain_kind')}"
            return
    inst["valid"] = True
    inst["invalid_reason"] = None


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
        # Always rebuild POLARITY to pick up rephrase INV template (G).
        if bases[bid]["type"] == "POLARITY":
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

    # Reset LLM paraphrase artifacts (G).
    backup = OUT / "para_attempts.pre_qc_v3.jsonl"
    if (OUT / "para_attempts.jsonl").exists():
        backup.write_text((OUT / "para_attempts.jsonl").read_text())
    write_jsonl(OUT / "para_attempts.jsonl", [])
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
