#!/usr/bin/env python3
"""Build Lane B M1 instance packs (T7 E1-unit + main INV/E1/C0 subset)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quantity_norm import apply_m1_pair  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402
import hashlib

MAIN = ROOT / "data/v3/instances_main.jsonl"
T7_SRC = ROOT / "data/t7/instances_e1_unit.jsonl"
OUT_T7 = ROOT / "data/lane_b/m1_t7_e1_unit.jsonl"
OUT_MAIN = ROOT / "data/lane_b/m1_main_inv_e1_c0.jsonl"


def _m1_enrich(row: dict) -> dict:
    claim_m1, evidence_m1 = apply_m1_pair(row.get("claim") or "", row.get("evidence") or "")
    out = dict(row)
    out["claim"] = claim_m1
    out["evidence"] = evidence_m1
    out["content_sha1"] = hashlib.sha1(f"{claim_m1}\n{evidence_m1}".encode()).hexdigest()
    out["m1_preapplied"] = True
    return out


def main() -> None:
    t7_rows = [
        _m1_enrich(r)
        for r in read_jsonl(T7_SRC)
        if r.get("valid", True)
        and r.get("condition") in ("E1-unit-claim", "E1-unit-evid")
    ]
    OUT_T7.parent.mkdir(parents=True, exist_ok=True)
    with OUT_T7.open("w") as handle:
        for row in sorted(t7_rows, key=lambda r: r["instance_id"]):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    main_rows = [
        r
        for r in read_jsonl(MAIN)
        if r.get("subset") == "main"
        and r.get("valid", True)
        and (
            r.get("condition") in ("E1-evid", "E1-claim", "C0")
            or (r.get("condition") == "INV-claim" and r.get("magnitude") == "unit_conversion")
        )
    ]
    with OUT_MAIN.open("w") as handle:
        for row in main_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps({"m1_t7_e1_unit": len(t7_rows), "m1_main_inv_e1_c0": len(main_rows)}, indent=2))


if __name__ == "__main__":
    main()
