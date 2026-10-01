#!/usr/bin/env python3
"""T15 OOD card: base vs ft MiniCheck-RoBERTa on T24b real answers and T18 non-medical (Wikipedia) packs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import N_BOOT, SEED, bootstrap_rate, read_jsonl  # noqa: E402
from t24b_report import EXCLUDED_QUESTIONS  # noqa: E402

RAW = ROOT / "results/raw/t15_cpuverif"
T24B = ROOT / "data/t24/instances_t24b.jsonl"
T18 = ROOT / "data/t18/instances_t18.jsonl"
T18_OOD = ROOT / "data/t18/instances_t18_t15ood.jsonl"
T18_X10_REV = "7d8e919"
OUT = ROOT / "notes/t15_ood_report.md"
OUT_JSON = ROOT / "notes/t15_ood_card.json"

UNIT_SCALE = {"km": 1e3, "m": 1.0, "kW": 1e3, "W": 1.0, "L": 1.0, "mL": 1e-3, "kg": 1e3, "g": 1.0}


def unit_direction(unit_pair: str) -> str:
    """unit_pair 'A→B': evidence unit A replaced by B in the claim; up if B is the larger unit."""
    a, b = unit_pair.split("→")
    return "up" if UNIT_SCALE[b] > UNIT_SCALE[a] else "down"


def build_t18() -> None:
    cur = [r for r in read_jsonl(T18) if r.get("valid", True)]
    c0 = {r["base_id"]: r for r in cur if r["condition"] == "C0"}
    old = [
        json.loads(line)
        for line in subprocess.check_output(
            ["/usr/bin/git", "show", f"{T18_X10_REV}:data/t18/instances_t18.jsonl"], text=True, cwd=ROOT
        ).splitlines()
        if line.strip()
    ]
    rows: list[dict] = list(c0.values())
    for r in old:
        b = r["base_id"]
        if r["condition"] == "E1-claim" and r["magnitude"] == "x10" and b in c0:
            if (r["claim_c0"], r["evidence_c0"]) == (c0[b]["claim"], c0[b]["evidence"]):
                rows.append({**r, "t15ood_cell": "value_x10", "t15ood_source": T18_X10_REV})
    for r in cur:
        if r["condition"] == "E1-unit" and r["base_id"] in c0:
            rows.append({**r, "t15ood_cell": f"unit_{unit_direction(r['diff']['unit_pair'])}"})
    for r in rows:
        r.setdefault("t15ood_cell", "c0" if r["condition"] == "C0" else r.get("t15ood_cell"))
    with T18_OOD.open("w") as handle:
        for r in rows:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r["t15ood_cell"]] += 1
    print(json.dumps({"built": str(T18_OOD.relative_to(ROOT)), "cells": counts}))


def read_verdicts(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in read_jsonl(path) if path.is_file() else []:
        v = row.get("verdict")
        if v in ("PASS", "FAIL"):
            out[row["instance_id"]] = v
    return out


def card(cells_by_base: dict[str, dict[str, list[str]]], cells: tuple[str, ...]) -> dict:
    """cells_by_base[base]['c0'] = [verdict]; other cells conditional on C0 PASS; cluster = base."""
    res = {}
    c0_groups = []
    for cb in cells_by_base.values():
        if cb.get("c0"):
            c0_groups.append((int(cb["c0"][0] == "PASS"), 1))
    res["c0_pass"] = bootstrap_rate(c0_groups)
    for cell in cells:
        groups = []
        for cb in cells_by_base.values():
            if not cb.get("c0") or cb["c0"][0] != "PASS":
                continue
            vs = cb.get(cell) or []
            if vs:
                groups.append((sum(v == "FAIL" for v in vs), len(vs)))
        res[cell] = bootstrap_rate(groups)
    return res


def t24b_leg(leg: str) -> dict:
    sc = read_verdicts(RAW / f"{leg}_t24b.jsonl")
    cell_of = {"T24b-C0": "c0", "T24b-value-x10": "value_x10", "T24b-unit-up": "unit_up", "T24b-unit-down": "unit_down"}
    by: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for r in read_jsonl(T24B):
        if r["question_id"] in EXCLUDED_QUESTIONS or not r.get("valid", True):
            continue
        v = sc.get(r["instance_id"])
        if v:
            by[r["question_id"]][cell_of[r["condition"]]].append(v)
    return card(by, ("value_x10", "unit_up", "unit_down"))


def t18_leg(leg: str) -> dict:
    sc = read_verdicts(RAW / f"{leg}_t18_ood.jsonl")
    by: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for r in read_jsonl(T18_OOD):
        v = sc.get(r["instance_id"])
        if v:
            by[r["base_id"]][r["t15ood_cell"]].append(v)
    return card(by, ("value_x10", "unit_up", "unit_down"))


def fmt(st: dict) -> str:
    if st.get("rate") is None:
        return f"NA (n={st.get('den', 0)})"
    ci = f" [{100*st['lo']:.1f}, {100*st['hi']:.1f}]" if st.get("lo") is not None else ""
    return f"{100*st['rate']:.1f}%{ci} (n={st['den']}, q={st['n_bases']})"


def report() -> None:
    data = {"t24b": {leg: t24b_leg(leg) for leg in ("base", "ft")}, "t18": {leg: t18_leg(leg) for leg in ("base", "ft")}}
    lines = [
        "# T15 OOD — base vs fine-tuned MiniCheck-RoBERTa",
        "",
        "Scores: reference env **cpuverif** (`results/raw/t15_cpuverif/`); vllm-env scores superseded "
        "(ft agreement 202/202 T24b, 106/106 T18; base T18 97/106 → see `notes/env_divergence.md`). "
        f"Perturbation cells are FAIL rates among units whose C0 is PASS. Bootstrap {N_BOOT} × cluster "
        f"(T24b: question_id; T18: base_id), seed {SEED}. n = instances, q = clusters.",
        "",
        f"- **T24b**: `{T24B.relative_to(ROOT)}`, excluded questions {', '.join(sorted(EXCLUDED_QUESTIONS))} (as in `t24b_report.py`).",
        f"- **T18 (Wikipedia, non-medical)**: `{T18_OOD.relative_to(ROOT)}` — reviewed C0 from `{T18.relative_to(ROOT)}`; "
        f"value ×10 = `E1-claim x10` rows from build `{T18_X10_REV}` reused only where C0 claim+evidence are identical "
        "(the reviewed pack has ×2/÷2 only); unit up/down = reviewed `E1-unit` unit_swap split by `unit_pair` direction.",
        "",
        "| Pack | Leg | C0 PASS | Value×10 FAIL|C0 | Unit-up FAIL|C0 | Unit-down FAIL|C0 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pack, label in (("t24b", "T24b real answers"), ("t18", "T18 Wikipedia")):
        for leg in ("base", "ft"):
            m = data[pack][leg]
            lines.append(
                f"| {label} | {leg} | {fmt(m['c0_pass'])} | {fmt(m['value_x10'])} | {fmt(m['unit_up'])} | {fmt(m['unit_down'])} |"
            )
    OUT.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps({**data, "bootstrap_n": N_BOOT, "seed": SEED}, indent=2) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("build", "report"))
    args = ap.parse_args()
    build_t18() if args.action == "build" else report()
