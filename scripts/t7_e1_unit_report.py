#!/usr/bin/env python3
"""T7: FAIL/PASS rates — E1-unit vs E1-claim x2/x10 vs INV-unit, per verifier."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
MAIN = ROOT / "data/v3/instances_main.jsonl"
EXPAND = ROOT / "data/expand/instances_cpu_early.jsonl"
RAW_T7 = ROOT / "results/raw/t7"
RAW_MAIN = ROOT / "results/raw"
OUT_MD = ROOT / "notes/t7_e1_unit_report.md"
OUT_JSON = ROOT / "notes/t7_e1_unit_report.json"

HPC_VERIFIERS = ["v1_medscore", "v4_ragas_nli", "v1b_medscore", "v5_ragas_nli", "v6_ragas_nli"]
T6A_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"


def node30_verifiers() -> list[str]:
    base = ["v2a_minicheck", "v3_alignscore", "v2b_bespoke"]
    if T6A_MANIFEST.is_file():
        data = json.loads(T6A_MANIFEST.read_text())
        base.extend(c["id"] for c in data.get("checkers", []))
    return base


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def load_scores(raw_dir: Path, verifiers: list[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for v in verifiers:
        path = raw_dir / f"{v}.jsonl"
        m: dict[str, str] = {}
        for row in read_jsonl(path):
            iid = row.get("instance_id")
            if iid:
                m[iid] = row.get("verdict") or ""
        out[v] = m
    return out


def rate(ids: list[str], scores: dict[str, str], want: str) -> tuple[float | None, int, int]:
    hits = []
    for iid in ids:
        v = scores.get(iid)
        if v:
            hits.append(int(v == want))
    if not hits:
        return None, 0, len(ids)
    return sum(hits) / len(hits), len(hits), len(ids)


def main() -> None:
    t7_rows = read_jsonl(T7)
    t7_bases = {r["base_id"] for r in t7_rows}
    e1_unit_ids = [r["instance_id"] for r in t7_rows]

    ref_rows = read_jsonl(MAIN) + read_jsonl(EXPAND)
    e1_claim_ids: list[str] = []
    inv_ids: list[str] = []
    for r in ref_rows:
        if not r.get("valid", True) or r["base_id"] not in t7_bases:
            continue
        if r["condition"] == "E1-claim" and r.get("magnitude") in ("x2", "x10"):
            e1_claim_ids.append(r["instance_id"])
        if r["condition"] == "INV-claim" and r.get("magnitude") == "unit_conversion":
            inv_ids.append(r["instance_id"])

    node_verifiers = node30_verifiers()
    scores_hpc_t7 = load_scores(RAW_T7, HPC_VERIFIERS)
    scores_node = load_scores(RAW_T7, node_verifiers)
    scores_main = load_scores(RAW_MAIN, HPC_VERIFIERS)

    def pick_scores(v: str) -> dict[str, str]:
        return scores_hpc_t7.get(v) or scores_node.get(v) or scores_main.get(v) or {}

    all_v = sorted(set(HPC_VERIFIERS + node_verifiers))
    table = {}
    for v in all_v:
        sc = pick_scores(v)
        fail_e1u, n_e1u, tot_e1u = rate(e1_unit_ids, sc, "FAIL")
        sc_ref = scores_main.get(v, {})
        fail_e1c, n_e1c, tot_e1c = rate(e1_claim_ids, sc_ref, "FAIL")
        pass_inv, n_inv, tot_inv = rate(inv_ids, sc_ref, "PASS")
        table[v] = {
            "e1_unit_fail_rate": fail_e1u,
            "e1_unit_n_scored": n_e1u,
            "e1_unit_n_cohort": tot_e1u,
            "e1_claim_x2_x10_fail_rate": fail_e1c,
            "e1_claim_n_scored": n_e1c,
            "e1_claim_n_cohort": tot_e1c,
            "inv_unit_pass_rate": pass_inv,
            "inv_unit_n_scored": n_inv,
            "inv_unit_n_cohort": tot_inv,
        }

    payload = {
        "n_e1_unit_instances": len(e1_unit_ids),
        "n_e1_claim_ref": len(e1_claim_ids),
        "n_inv_unit_ref": len(inv_ids),
        "n_t7_bases": len(t7_bases),
        "verifiers": table,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T7 E1-unit vs E1-claim vs INV-unit (per verifier)",
        "",
        f"- E1-unit cohort: **{len(e1_unit_ids)}** instances ({len(t7_bases)} bases)",
        f"- Reference E1-claim x2/x10 (same bases): **{len(e1_claim_ids)}**",
        f"- Reference INV-unit (same bases): **{len(inv_ids)}**",
        "",
        "| verifier | E1-unit FAIL rate | n | E1-claim x2/x10 FAIL rate | n | INV-unit PASS rate | n |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for v in all_v:
        cell = table[v]
        def fmt(x):
            return f"{x:.3f}" if x is not None else "—"

        lines.append(
            f"| {v} | {fmt(cell['e1_unit_fail_rate'])} | {cell['e1_unit_n_scored']}/{cell['e1_unit_n_cohort']} | "
            f"{fmt(cell['e1_claim_x2_x10_fail_rate'])} | {cell['e1_claim_n_scored']}/{cell['e1_claim_n_cohort']} | "
            f"{fmt(cell['inv_unit_pass_rate'])} | {cell['inv_unit_n_scored']}/{cell['inv_unit_n_cohort']} |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
