#!/usr/bin/env python3
"""LEGACY helper — paper table: scripts/compute_paper_numbers.py → results/tables/m1_before_after.md."""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
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
from review_filters import analysis_keep_row  # noqa: E402

INST = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
RAW = ROOT / "results" / "raw"
RAW_M1 = ROOT / "results" / "raw_m1"
OUT = ROOT / "results" / "tables" / "m1_before_after.md"
RESIDUAL = ROOT / "results" / "tables" / "m1_inv_unit_residuals.jsonl"

VERIFIERS = (
    ("v2a_minicheck", "V2a"),
    ("v3_alignscore", "V3"),
    ("v1_medscore", "V1"),
    ("v4_ragas_nli", "V4"),
)


def mcnemar(b: int, c: int) -> tuple[float | None, float | None]:
    """Discordant pairs: b=raw pass m1 fail, c=raw fail m1 pass."""
    if b + c == 0:
        return None, None
    # chi-square with continuity correction
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    # approximate two-sided p from chi2(1)
    p = math.erfc(math.sqrt(stat / 2))
    return stat, p


def paired_inv(rows_raw: list[dict], rows_m1: list[dict], verifier: str) -> dict:
    raw_by = {r["instance_id"]: r for r in rows_raw if r["verifier"] == verifier}
    m1_by = {r["instance_id"]: r for r in rows_m1 if r["verifier"] == verifier}
    block = [r for r in rows_raw if r["verifier"] == verifier and r["type"] == "DOSE"]
    cond = _c0_pass_bases(block)
    b = c = 0
    for iid, r0 in raw_by.items():
        r1 = m1_by.get(iid)
        if not r1:
            continue
        if r0["base_id"] not in cond or r0["condition"] != "INV-claim":
            continue
        if not _parsed(r0) or not _parsed(r1):
            continue
        if r0["verdict"] == "PASS" and r1["verdict"] == "FAIL":
            b += 1
        elif r0["verdict"] == "FAIL" and r1["verdict"] == "PASS":
            c += 1
    stat, p = mcnemar(b, c)
    return {"discordant_pass_fail": b, "discordant_fail_pass": c, "chi2": stat, "p_approx": p}


def residual_inv_unit_fail(rows_m1: list[dict], verifier: str) -> list[dict]:
    out = []
    block = [r for r in rows_m1 if r["verifier"] == verifier]
    cond = _c0_pass_bases(block)
    for row in block:
        if row["base_id"] not in cond:
            continue
        if row["condition"] != "INV-claim" or row.get("magnitude") != "unit_conversion":
            continue
        if row["verdict"] != "FAIL":
            continue
        out.append(
            {
                "instance_id": row["instance_id"],
                "base_id": row["base_id"],
                "verifier": verifier,
                "claim_span": row.get("claim_span"),
                "evidence_span": row.get("evidence_span"),
                "unit_inv_source": row.get("unit_inv_source"),
            }
        )
    return out


def slice_table(rows: list[dict], verifier: str, label: str, tag: str) -> str:
    block = [r for r in rows if r["verifier"] == verifier and analysis_keep_row(r)]
    cond = _c0_pass_bases(block)
    inv = bootstrap_rate(
        [
            (sum(1 for r in g if r["verdict"] == "PASS"), len(g))
            for _, g in _group_by_base(
                [
                    r
                    for r in block
                    if r["base_id"] in cond
                    and r["condition"] == "INV-claim"
                    and _parsed(r)
                ]
            ).items()
        ]
    )
    e1 = bootstrap_rate(
        [
            (sum(1 for r in g if r["verdict"] == "FAIL"), len(g))
            for _, g in _group_by_base(
                [
                    r
                    for r in block
                    if r["base_id"] in cond
                    and r["condition"] == "E1-evid"
                    and _parsed(r)
                ]
            ).items()
        ]
    )
    c0 = bootstrap_rate(
        [
            (sum(1 for r in g if r["verdict"] == "PASS"), len(g))
            for _, g in _group_by_base(
                [r for r in block if r["condition"] == "C0" and _parsed(r)]
            ).items()
        ]
    )

    def fmt(st: dict) -> str:
        if st["rate"] is None:
            return "NA"
        if st["lo"] is None:
            return f"{st['rate']:.3f} ({st['num']}/{st['den']})"
        return f"{st['rate']:.3f} [{st['lo']:.3f},{st['hi']:.3f}] ({st['num']}/{st['den']})"

    return f"| {label} | {fmt(c0)} | {fmt(inv)} | {fmt(e1)} | {tag} |"


def _group_by_base(rows: list[dict]) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["base_id"]].append(r)
    return by


def main() -> None:
    instances = [r for r in read_jsonl(INST) if r.get("valid", True)]
    raw = load_joined_from_records(instances, RAW)
    m1 = load_joined_from_records(instances, RAW_M1) if RAW_M1.is_dir() else []

    lines = [
        "# M1 before / after",
        "",
        f"Instances: `{INST.relative_to(ROOT)}` (n={len(instances)}). "
        "Rates cluster-bootstrap by `base_id` (seed 42). Conditional: **C0 PASS**. "
        "Columns: **C0** = baseline support; **QI** = INV-claim PASS (all magnitudes); "
        "**NS** = E1-evid FAIL (not QI). See `notes/reconcile_llama70b_qi.md`.",
        "",
        "| Verifier | C0 (support) | QI INV pass (|C0) | NS E1-evid FAIL (|C0) | raw | M1 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    mcnemar_lines = ["", "## McNemar (INV-claim, |C0, parsed)", ""]
    residuals: list[dict] = []

    for vkey, vlabel in VERIFIERS:
        if not any(r["verifier"] == vkey for r in raw):
            continue
        lines.append(slice_table(raw, vkey, f"{vlabel} raw", "raw"))
        if m1:
            lines.append(slice_table(m1, vkey, f"{vlabel} M1", "M1"))
            mc = paired_inv(raw, m1, vkey)
            mcnemar_lines.append(
                f"- **{vlabel}:** b={mc['discordant_pass_fail']} c={mc['discordant_fail_pass']} "
                f"χ²≈{mc['chi2']:.3f} p≈{mc['p_approx']:.4g}"
                if mc["chi2"] is not None
                else f"- **{vlabel}:** no discordant pairs"
            )
            residuals.extend(residual_inv_unit_fail(m1, vkey))

    si_raw = {v: sensitivity_invariance(raw) for v, _ in VERIFIERS}
    si_m1 = {v: sensitivity_invariance(m1) for v, _ in VERIFIERS} if m1 else {}
    lines += [
        "",
        "## DOSE macro (sensitivity_invariance)",
        "",
        "| Verifier | QI raw | NS raw | QI M1 | NS M1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for vkey, vlabel in VERIFIERS:
        pr = next((p for p in si_raw.get(vkey, []) if p["type"] == "DOSE"), {})
        pm = next((p for p in si_m1.get(vkey, []) if p["type"] == "DOSE"), {}) if si_m1 else {}
        lines.append(
            f"| {vlabel} | "
            f"{pr.get('invariance', '—')} | {pr.get('sensitivity_e1_evid', '—')} | "
            f"{pm.get('invariance', '—')} | {pm.get('sensitivity_e1_evid', '—')} |"
        )

    lines += mcnemar_lines
    lines += [
        "",
        f"Residual INV-unit still FAIL after M1: `{RESIDUAL.relative_to(ROOT)}` "
        f"(n={len(residuals)} rows).",
        "",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    with RESIDUAL.open("w") as handle:
        for row in residuals:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(OUT)
    print(RESIDUAL)


if __name__ == "__main__":
    main()
