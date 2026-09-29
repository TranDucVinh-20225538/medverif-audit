#!/usr/bin/env python3
"""Full T2 summary: spend + conditional-on-C0 metrics (V1b/V5) + T3 freq/route slice."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import (  # noqa: E402
    _c0_pass_bases,
    _parsed,
    bootstrap_rate,
    load_joined_from_records,
    read_jsonl,
    sensitivity_invariance,
)
from review_filters import (  # noqa: E402
    analysis_keep_row,
    effective_unit_natural_y,
    flip_pi_ok_bases,
    inv_mechanism,
    inv_pi_ok_keys,
)
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

INST = ROOT / "data" / "t2" / "instances_full_pending.jsonl"
RAW = ROOT / "results" / "raw" / "t2_full"
RAW_T3 = ROOT / "results" / "raw" / "t3_t2"
T3_INST = ROOT / "data" / "v3" / "instances_inv_families.jsonl"
OUT = ROOT / "notes" / "t2_full_report.md"

VERIFIERS = (
    ("v1b_medscore", "V1b (gpt-4o)"),
    ("v5_ragas_nli", "V5 (Claude Sonnet)"),
)


def load_scores(name: str) -> dict[str, dict]:
    path = RAW / f"{name}.jsonl"
    return {row["instance_id"]: row for row in read_jsonl(path)}


def join_t2(instances: list[dict], verifier: str) -> list[dict]:
    inst_by = {r["instance_id"]: r for r in instances if r.get("valid", True)}
    out = []
    for rec in read_jsonl(RAW / f"{verifier}.jsonl"):
        inst = inst_by.get(rec["instance_id"])
        if not inst:
            continue
        row = dict(inst)
        row["verifier"] = verifier
        row["verdict"] = rec.get("verdict")
        row["score"] = rec.get("score")
        out.append(row)
    return out


def inv_span_before(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    return str(claim.get("span_before") or row.get("claim_span") or "")


def fail_rate_cond_c0(rows: list[dict], verifier: str, pred) -> str:
    block = [r for r in rows if r["verifier"] == verifier]
    cond = _c0_pass_bases(block)
    parsed = [r for r in block if pred(r) and r["base_id"] in cond and _parsed(r)]
    if not parsed:
        return "—"
    n_fail = sum(r["verdict"] == "FAIL" for r in parsed)
    return f"{n_fail}/{len(parsed)} ({n_fail/len(parsed):.3f})"


def pass_rate_cond_c0(rows: list[dict], verifier: str, pred) -> str:
    block = [r for r in rows if r["verifier"] == verifier]
    cond = _c0_pass_bases(block)
    parsed = [r for r in block if pred(r) and r["base_id"] in cond and _parsed(r)]
    if not parsed:
        return "—"
    n_pass = sum(r["verdict"] == "PASS" for r in parsed)
    return f"{n_pass}/{len(parsed)} ({n_pass/len(parsed):.3f})"


def pass_rate(rows: list[dict], verifier: str, pred) -> str:
    parsed = [
        r
        for r in rows
        if r["verifier"] == verifier and pred(r) and _parsed(r)
    ]
    if not parsed:
        return "—"
    n_pass = sum(r["verdict"] == "PASS" for r in parsed)
    return f"{n_pass}/{len(parsed)} ({n_pass/len(parsed):.3f})"


def t3_pi_ok_instance_ids() -> set[str]:
    path = ROOT / "qc" / "inv_claim_PI_ok_labels.csv"
    if not path.is_file():
        return set()
    out: set[str] = set()
    for row in csv.DictReader(path.open()):
        if (row.get("PI_ok") or "").strip().upper() != "Y":
            continue
        fam = (row.get("family") or "").strip()
        if fam in ("inv_frequency", "inv_route"):
            iid = (row.get("instance_id") or "").strip()
            if iid:
                out.add(iid)
    return out


def join_t3(verifier: str, allowed: set[str]) -> list[dict]:
    inst_by = {r["instance_id"]: r for r in read_jsonl(T3_INST) if r["instance_id"] in allowed}
    path = RAW_T3 / f"{verifier}.jsonl"
    out = []
    for rec in read_jsonl(path):
        inst = inst_by.get(rec["instance_id"])
        if not inst:
            continue
        row = dict(inst)
        row["verifier"] = verifier
        row["verdict"] = rec.get("verdict")
        out.append(row)
    return out


def main() -> None:
    instances = read_jsonl(INST)
    joined: list[dict] = []
    for vkey, _ in VERIFIERS:
        joined.extend(join_t2(instances, vkey))
    joined = [r for r in joined if analysis_keep_row(r)]
    flip_y = flip_pi_ok_bases()
    inv_keys = inv_pi_ok_keys()

    lines = ["# T2 full report", ""]
    credit = {}
    cp = ROOT / "notes" / "openrouter_credit.json"
    if cp.is_file():
        credit = json.loads(cp.read_text())

    total_spend = 0.0
    n_scored = 0
    for v, _ in VERIFIERS:
        for rec in load_scores(v).values():
            total_spend += float(rec.get("api_cost_usd") or 0)
            n_scored += 1

    n_inst = len(instances)
    per_inst = total_spend / max(n_scored // len(VERIFIERS), 1) if n_scored else 0.0
    lines += [
        f"- Instances: **{n_inst}**",
        f"- Scored rows: **{n_scored}** (target {n_inst * 2})",
        f"- Spend: **${total_spend:.4f}**",
        f"- Approx $/instance/verifier: **${per_inst:.5f}**",
        f"- OpenRouter limit_remaining: **{credit.get('limit_remaining', '—')}**",
        "",
        "Conditional rates below use **C0 PASS** on the same verifier unless noted.",
        "",
        "## Summary (main T2 scope)",
        "",
        "| Verifier | C0 pass | E1-claim FAIL x2 | E1-claim FAIL x10 | "
        "INV-unit PASS (all) | INV-unit PASS (natural) | INV-unit PASS (PI-reviewed) | "
        "POL E1 FAIL (26 flip_ok) | POL INV PASS (template) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for vkey, vlabel in VERIFIERS:
        dose = [r for r in joined if r["verifier"] == vkey and r["type"] == "DOSE"]
        pol = [r for r in joined if r["verifier"] == vkey and r["type"] == "POLARITY"]
        lines.append(
            f"| {vlabel} | "
            f"{pass_rate_cond_c0(dose, vkey, lambda r: r['condition']=='C0')} | "
            f"{fail_rate_cond_c0(dose, vkey, lambda r: r['condition']=='E1-claim' and r.get('magnitude')=='x2')} | "
            f"{fail_rate_cond_c0(dose, vkey, lambda r: r['condition']=='E1-claim' and r.get('magnitude')=='x10')} | "
            f"{pass_rate_cond_c0(dose, vkey, lambda r: r['condition']=='INV-claim' and r.get('magnitude')=='unit_conversion')} | "
            f"{pass_rate_cond_c0(dose, vkey, lambda r: r['condition']=='INV-claim' and r.get('magnitude')=='unit_conversion' and effective_unit_natural_y(r['base_id'], rule_natural_unit_conversion_label(inv_span_before(r))))} | "
            f"{pass_rate_cond_c0(dose, vkey, lambda r: r['condition']=='INV-claim' and r.get('magnitude')=='unit_conversion' and (r['base_id'], r['type'], 'unit') in inv_keys)} | "
            f"{fail_rate_cond_c0(pol, vkey, lambda r: r['condition']=='E1-claim' and r['base_id'] in flip_y)} | "
            f"{pass_rate(pol, vkey, lambda r: r['condition']=='INV-claim' and inv_mechanism(r)=='template')} |"
        )

    si = {v: sensitivity_invariance([r for r in joined if r["verifier"] == v]) for v, _ in VERIFIERS}
    lines += [
        "",
        "**DOSE macro (bootstrap by base, same filters):**",
        "",
        "| Verifier | Invariance (INV) | Sensitivity (E1-evid FAIL) |",
        "| --- | ---: | ---: |",
    ]
    for vkey, vlabel in VERIFIERS:
        pt = next((p for p in si[vkey] if p["type"] == "DOSE"), {})
        inv = pt.get("invariance")
        sen = pt.get("sensitivity_e1_evid")
        inv_s = f"{inv:.3f}" if inv is not None else "—"
        sen_s = f"{sen:.3f}" if sen is not None else "—"
        lines.append(f"| {vlabel} | {inv_s} | {sen_s} |")

    t3_ids = t3_pi_ok_instance_ids()
    lines += [
        "",
        f"## T3 slice (freq + route, PI_ok=Y, n={len(t3_ids)} scored in raw/t3_t2)",
        "",
        "| Verifier | INV frequency PASS | INV route PASS |",
        "| --- | --- | --- |",
    ]
    for vkey, vlabel in VERIFIERS:
        t3_rows = join_t3(vkey, t3_ids)
        lines.append(
            f"| {vlabel} | "
            f"{pass_rate(t3_rows, vkey, lambda r: (r.get('diff') or {}).get('inv_family')=='frequency')} | "
            f"{pass_rate(t3_rows, vkey, lambda r: (r.get('diff') or {}).get('inv_family')=='route')} |"
        )

    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
