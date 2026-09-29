#!/usr/bin/env python3
"""Build T12 evaluation instances (C0, E1 x2, INV-unit, T7 E1-unit, INV freq/route)."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from review_filters import analysis_keep_row  # noqa: E402
from t2_build_instances import MAIN, EXPAND, read_jsonl, t2_full_eligible, write_jsonl  # noqa: E402

T7 = ROOT / "data" / "t7" / "instances_e1_unit.jsonl"
INV_FAM = ROOT / "data" / "v3" / "instances_inv_families.jsonl"
INV_PI = ROOT / "qc" / "inv_families_sample.csv"
OUT_DIR = ROOT / "data" / "t12"
PILOT_N = 20
PILOT_SEED = 1212


def inv_family_pi_ok() -> set[str]:
    if not INV_PI.is_file():
        return set()
    out: set[str] = set()
    with INV_PI.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if (row.get("PI_ok") or "").strip().upper() == "Y":
                out.add(row["instance_id"])
    return out


def slice_key(row: dict) -> str:
    cond = row.get("condition") or ""
    mag = row.get("magnitude") or ""
    if cond == "C0":
        return "C0"
    if cond == "E1-claim" and mag == "x2":
        return "E1-claim_x2"
    if cond == "INV-claim" and mag == "unit_conversion":
        return "INV-unit"
    if cond in ("E1-unit-claim", "E1-unit-evid"):
        return cond
    if mag in ("inv_frequency", "inv_route"):
        return mag
    return ""


def main_scope_rows() -> list[dict]:
    rows: list[dict] = []
    for r in read_jsonl(MAIN) + read_jsonl(EXPAND):
        if not t2_full_eligible(r, expand=str(r.get("base_id", "")).startswith(("E", "X", "EXP"))):
            continue
        if not analysis_keep_row(r):
            continue
        if r.get("condition") == "E1-claim" and r.get("magnitude") != "x2":
            continue
        if r.get("magnitude", "").startswith("inv_") and r.get("magnitude") not in (
            "inv_frequency",
            "inv_route",
        ):
            continue
        rows.append(r)
    pi_ok = inv_family_pi_ok()
    for r in read_jsonl(INV_FAM):
        if not r.get("valid", True):
            continue
        mag = r.get("magnitude") or ""
        if mag not in ("inv_frequency", "inv_route"):
            continue
        if pi_ok and r["instance_id"] not in pi_ok:
            continue
        rows.append(r)
    for r in read_jsonl(T7):
        if not r.get("valid", True):
            continue
        if r.get("condition") in ("E1-unit-claim", "E1-unit-evid"):
            rows.append(r)
    seen: set[str] = set()
    out = []
    for r in rows:
        iid = r["instance_id"]
        if iid in seen:
            continue
        seen.add(iid)
        out.append(r)
    return out


def build_pilot(full_rows: list[dict]) -> list[dict]:
    by_slice: dict[str, list[dict]] = {}
    for r in full_rows:
        sk = slice_key(r)
        if sk:
            by_slice.setdefault(sk, []).append(r)
    rng = random.Random(PILOT_SEED)
    picked: list[dict] = []
    for sk in sorted(by_slice):
        pool = list(by_slice[sk])
        rng.shuffle(pool)
        picked.extend(pool[:PILOT_N])
    return picked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("pilot", "full"), default="full")
    args = parser.parse_args()
    full_rows = main_scope_rows()
    rows = build_pilot(full_rows) if args.mode == "pilot" else full_rows
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"instances_{args.mode}.jsonl"
    write_jsonl(out, rows)
    strata = {}
    for r in rows:
        sk = slice_key(r) or "other"
        strata[sk] = strata.get(sk, 0) + 1
    meta = {
        "mode": args.mode,
        "n_instances": len(rows),
        "n_full_scope": len(full_rows),
        "strata": strata,
        "path": str(out.relative_to(ROOT)),
    }
    (OUT_DIR / f"manifest_{args.mode}.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
