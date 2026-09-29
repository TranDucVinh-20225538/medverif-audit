#!/usr/bin/env python3
"""Compare Lane B HPC scores vs node30 on calibration pack (verdict agreement)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402

CAL = ROOT / "data/lane_b/calibration_200.jsonl"
HPC = ROOT / "results/raw/lane_b"
NODE30 = ROOT / "results/raw_node30"
OUT = ROOT / "notes/lane_b_calibration_agreement.json"
MD = ROOT / "notes/lane_b_calibration_agreement.md"

CHECKERS = (
    ("t6a_minicheck_roberta", "t6_minicheck_roberta.jsonl"),
    ("t6a_minicheck_deberta", "t6_minicheck_deberta.jsonl"),
    ("t6a_alignscore_base", "t6_alignscore_base.jsonl"),
    ("t6a_summac_zs", "t6_summac_zs.jsonl"),
    ("t6a_summac_conv", "t6_summac_conv.jsonl"),
    ("t6a_hhem", "t6_hhem.jsonl"),
    ("t6a_granite_guardian", "t6_granite_guardian.jsonl"),
)


def by_id(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    return {r["instance_id"]: r for r in read_jsonl(path)}


def agreement(ref: dict[str, dict], hpc: dict[str, dict], ids: set[str]) -> dict:
    n = agree = 0
    for iid in ids:
        a, b = ref.get(iid), hpc.get(iid)
        if not a or not b:
            continue
        va, vb = a.get("verdict"), b.get("verdict")
        if va not in ("PASS", "FAIL") or vb not in ("PASS", "FAIL"):
            continue
        n += 1
        agree += int(va == vb)
    rate = agree / n if n else None
    return {"n": n, "agreement": rate}


def main() -> None:
    cal_ids = {r["instance_id"] for r in read_jsonl(CAL)}
    rows = []
    lines = ["# Lane B calibration vs node30", "", f"Calibration ids: {len(cal_ids)}", ""]
    lines.append("| Checker | n | agreement |")
    lines.append("|---|---:|---:|")
    for cid, fname in CHECKERS:
        ref = by_id(NODE30 / fname)
        hpc = by_id(HPC / fname)
        stat = agreement(ref, hpc, cal_ids)
        stat["checker"] = cid
        stat["node30_file"] = fname
        rows.append(stat)
        ag = stat["agreement"]
        if ag is not None:
            lines.append(f"| {cid} | {stat['n']} | {100 * ag:.1f}% |")
        else:
            lines.append(f"| {cid} | {stat['n']} | NA |")
    OUT.write_text(json.dumps({"checkers": rows}, indent=2) + "\n")
    MD.write_text("\n".join(lines) + "\n")
    print(OUT.read_text())


if __name__ == "__main__":
    main()
