#!/usr/bin/env python3
"""T8 unit sample: INV pass / E1 fail overall and conditional on supported + C0 PASS."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data/t8/instances_aggrefact_inv.jsonl"
C0_INST = ROOT / "data/t8/instances_aggrefact_c0.jsonl"
RAW = ROOT / "results/raw/t8"
OUT = ROOT / "notes/t8_aggrefact_inv_report.json"

VERIFIERS = ["v1b_medscore", "v2a_minicheck", "v3_alignscore"] + [
    c["id"]
    for c in json.loads((ROOT / "notes/t6a_eco_checkers.json").read_text()).get("checkers", [])
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def load_scores(name: str) -> dict[str, str]:
    path = RAW / name
    out: dict[str, str] = {}
    if path.is_file():
        for row in read_jsonl(path):
            if row.get("instance_id"):
                out[row["instance_id"]] = row.get("verdict")
    return out


def rates(verdicts: list[str]) -> dict:
    if not verdicts:
        return {"n": 0, "pass_rate": None, "fail_rate": None}
    n = len(verdicts)
    passes = sum(1 for v in verdicts if v == "PASS")
    fails = sum(1 for v in verdicts if v == "FAIL")
    return {"n": n, "pass_rate": passes / n, "fail_rate": fails / n}


def main() -> None:
    if not INST.is_file():
        raise SystemExit(f"missing {INST}")
    rows = read_jsonl(INST)
    c0_rows = read_jsonl(C0_INST) if C0_INST.is_file() else []
    c0_by_base = {r["base_id"]: r for r in c0_rows}

    inv_rows = [r for r in rows if r.get("condition") == "T8-aggrefact-inv"]
    e1_rows = [r for r in rows if r.get("condition") == "T8-aggrefact-e1-unit"]

    report = {
        "n_instances": len(rows),
        "n_inv": len(inv_rows),
        "n_e1_unit": len(e1_rows),
        "n_c0_bases": len(c0_by_base),
        "c0_gate": "aggrefact_label==1 and verifier C0 PASS",
        "verifiers": {},
    }

    for v in VERIFIERS:
        sc = load_scores(f"{v}.jsonl")
        c0_sc = load_scores("v1b_medscore_c0.jsonl") if v == "v1b_medscore" else {}

        allowed_bases = set()
        for bid, c0 in c0_by_base.items():
            if c0.get("aggrefact_label") != 1:
                continue
            iid = c0["instance_id"]
            if c0_sc.get(iid) == "PASS":
                allowed_bases.add(bid)

        inv_all = [sc[r["instance_id"]] for r in inv_rows if sc.get(r["instance_id"])]
        e1_all = [sc[r["instance_id"]] for r in e1_rows if sc.get(r["instance_id"])]
        inv_cond = [
            sc[r["instance_id"]]
            for r in inv_rows
            if r["base_id"] in allowed_bases and sc.get(r["instance_id"])
        ]
        e1_cond = [
            sc[r["instance_id"]]
            for r in e1_rows
            if r["base_id"] in allowed_bases and sc.get(r["instance_id"])
        ]

        c0_verdicts = [c0_sc[r["instance_id"]] for r in c0_rows if c0_sc.get(r["instance_id"])]

        report["verifiers"][v] = {
            "n_c0_scored": len(c0_verdicts),
            "c0_pass_rate": rates(c0_verdicts)["pass_rate"],
            "n_bases_c0_gate": len(allowed_bases),
            "inv_pass_rate_all": rates(inv_all)["pass_rate"],
            "e1_unit_fail_rate_all": rates(e1_all)["fail_rate"],
            "inv_pass_rate_given_c0_gate": rates(inv_cond)["pass_rate"],
            "e1_unit_fail_rate_given_c0_gate": rates(e1_cond)["fail_rate"],
            "n_inv_given_c0_gate": len(inv_cond),
            "n_e1_given_c0_gate": len(e1_cond),
            "fail_rate_all": rates(inv_all + e1_all)["fail_rate"],
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
