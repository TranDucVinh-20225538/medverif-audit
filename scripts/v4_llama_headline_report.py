#!/usr/bin/env python3
"""V4 Llama headline numbers + legacy vs Llama on T7 (|C0)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _c0_pass_bases, _parsed, read_jsonl  # noqa: E402
from review_filters import analysis_keep_row, unit_natural_y_bases  # noqa: E402

MAIN = ROOT / "data/v3/instances_main.jsonl"
THR = ROOT / "data/v3/instances_threshold.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
E2 = ROOT / "data/e2/instances_main_x2.jsonl"
T7_DIR = ROOT / "results/raw/t7"
RAW = ROOT / "results/raw"
T7_DIR = ROOT / "results/raw/t7"
E2_DIR = ROOT / "results/raw/e2_main"
OUT_MD = ROOT / "notes/v4_llama_headline.md"
OUT_JSON = ROOT / "notes/v4_llama_headline.json"


def load_scores(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for row in read_jsonl(path):
        iid = row.get("instance_id")
        if iid:
            out[iid] = row.get("verdict") or ""
    return out


def join_scores(instances: list[dict], scores: dict[str, str]) -> list[dict]:
    rows = []
    for inst in instances:
        iid = inst["instance_id"]
        v = scores.get(iid)
        if not v:
            continue
        row = dict(inst)
        row["verifier"] = "v4_ragas_nli"
        row["verdict"] = v
        rows.append(row)
    return rows


def pass_rate(rows: list[dict], pred) -> str:
    parsed = [r for r in rows if pred(r) and _parsed(r)]
    if not parsed:
        return "—"
    n = sum(r["verdict"] == "PASS" for r in parsed)
    return f"{n}/{len(parsed)}"


def fail_rate(rows: list[dict], pred) -> str:
    parsed = [r for r in rows if pred(r) and _parsed(r)]
    if not parsed:
        return "—"
    n = sum(r["verdict"] == "FAIL" for r in parsed)
    return f"{n}/{len(parsed)}"


def cond_slice(rows: list[dict], c0_cond: bool = True) -> list[dict]:
    if not c0_cond:
        return rows
    cond = _c0_pass_bases(rows)
    return [r for r in rows if r["base_id"] in cond]


def merged_v4_scores() -> dict[str, str]:
    m: dict[str, str] = {}
    for d in (RAW, T7_DIR, ROOT / "results/raw/e2_main"):
        p = d / "v4_ragas_nli.llama.jsonl"
        if p.is_file():
            for row in read_jsonl(p):
                iid = row.get("instance_id")
                if iid:
                    m[iid] = row.get("verdict") or ""
    return m


def t7_cond_metrics(scores: dict[str, str]) -> dict:
    t7_rows = read_jsonl(T7)
    ref = read_jsonl(MAIN) + read_jsonl(THR)
    t7_bases = {r["base_id"] for r in t7_rows}
    c0_ref = [
        r for r in ref if r.get("valid", True) and r["base_id"] in t7_bases and r.get("condition") == "C0"
    ]
    claim_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-claim"]
    evid_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-evid"]
    iid_base = {r["instance_id"]: r["base_id"] for r in t7_rows}
    joined = []
    for r in c0_ref:
        v = scores.get(r["instance_id"])
        if v:
            row = dict(r)
            row["verifier"] = "v4_ragas_nli"
            row["verdict"] = v
            joined.append(row)
    c0b = _c0_pass_bases(joined)

    def fail_on(ids: list[str]) -> str:
        hits = []
        for iid in ids:
            if iid_base.get(iid) not in c0b:
                continue
            verdict = scores.get(iid)
            if verdict and verdict != "PARSE_FAIL":
                hits.append(int(verdict == "FAIL"))
        if not hits:
            return "—"
        return f"{sum(hits)}/{len(hits)}"

    return {"c0_pass_bases": len(c0b), "e1_unit_claim_fail": fail_on(claim_ids), "e1_unit_evid_fail": fail_on(evid_ids)}


def e2_pass(scores: dict[str, str]) -> str:
    e2_ids = {r["instance_id"] for r in read_jsonl(E2)}
    inst = read_jsonl(MAIN) + read_jsonl(THR)
    inst_map = {r["instance_id"]: r for r in inst if r.get("valid", True)}
    joined = join_scores(
        [inst_map[iid] for iid in scores if iid in inst_map and iid in e2_ids], scores
    )
    cond = _c0_pass_bases(joined)
    e2 = [r for r in joined if r["condition"] == "E2" and r["base_id"] in cond and _parsed(r)]
    if not e2:
        return "—"
    n = sum(r["verdict"] == "PASS" for r in e2)
    return f"{n}/{len(e2)}"


def main() -> None:
    instances = [r for r in read_jsonl(MAIN) + read_jsonl(THR) if r.get("valid", True)]
    llama = load_scores(RAW / "v4_ragas_nli.llama.jsonl")
    e2_sc = {**load_scores(RAW / "v4_ragas_nli.llama.jsonl"), **load_scores(E2_DIR / "v4_ragas_nli.llama.jsonl")}
    joined = join_scores(instances, llama)
    joined = [r for r in joined if analysis_keep_row(r) and r["type"] == "DOSE"]
    cond = cond_slice(joined, True)
    nat_y = unit_natural_y_bases()

    main_metrics = {
        "inv_unit_pass_all": pass_rate(
            cond,
            lambda r: r["condition"] == "INV-claim" and r.get("magnitude") == "unit_conversion",
        ),
        "inv_unit_pass_natural_y": pass_rate(
            cond,
            lambda r: r["condition"] == "INV-claim"
            and r.get("magnitude") == "unit_conversion"
            and r["base_id"] in nat_y,
        ),
        "e1_evid_x2_fail": fail_rate(
            cond, lambda r: r["condition"] == "E1-evid" and r.get("magnitude") == "x2"
        ),
        "e1_evid_x10_fail": fail_rate(
            cond, lambda r: r["condition"] == "E1-evid" and r.get("magnitude") == "x10"
        ),
        "e1_claim_x2_fail": fail_rate(
            cond, lambda r: r["condition"] == "E1-claim" and r.get("magnitude") == "x2"
        ),
        "e1_claim_x10_fail": fail_rate(
            cond, lambda r: r["condition"] == "E1-claim" and r.get("magnitude") == "x10"
        ),
        "c0_pass_none": pass_rate(cond, lambda r: r["condition"] == "C0" and r.get("magnitude") == "none"),
        "e2_pass_given_c0": e2_pass(e2_sc if e2_sc else llama),
        "t9_v4_scored": "none",
    }

    t7_llama = t7_cond_metrics(merged_v4_scores())
    legacy = load_scores(T7_DIR / "v4_ragas_nli.legacy.jsonl")
    main_v4 = load_scores(RAW / "v4_ragas_nli.llama.jsonl")
    t7_legacy = t7_cond_metrics({**main_v4, **legacy})

    payload = {"llama": main_metrics, "t7_cond_llama": t7_llama, "t7_cond_legacy": t7_legacy}
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# V4 (Llama-3.3-70B) headline numbers",
        "",
        "Provenance: `results/raw/v4_ragas_nli.llama.jsonl` (+ E2 overlay from `e2_main/`).",
        "DOSE main+threshold, `analysis_keep_row`, conditional on **C0 PASS** unless noted.",
        "",
        "| Metric | Llama |",
        "|---|---|",
        f"| INV-unit PASS (all valid) | {main_metrics['inv_unit_pass_all']} |",
        f"| INV-unit PASS (natural=Y) | {main_metrics['inv_unit_pass_natural_y']} |",
        f"| E1-evid x2 FAIL | {main_metrics['e1_evid_x2_fail']} |",
        f"| E1-evid x10 FAIL | {main_metrics['e1_evid_x10_fail']} |",
        f"| E1-claim x2 FAIL | {main_metrics['e1_claim_x2_fail']} |",
        f"| E1-claim x10 FAIL | {main_metrics['e1_claim_x10_fail']} |",
        f"| C0 PASS (magnitude none) | {main_metrics['c0_pass_none']} |",
        f"| E2 PASS (|C0; main×2 cohort scores) | {main_metrics['e2_pass_given_c0']} |",
        f"| T7 E1-unit-claim FAIL (|C0) | {t7_llama['e1_unit_claim_fail']} |",
        f"| T7 E1-unit-evid FAIL (|C0) | {t7_llama['e1_unit_evid_fail']} |",
        f"| T9 V4 scores | {main_metrics['t9_v4_scored']} |",
        "",
        "## T7 (115 bases): legacy vs Llama (|C0)",
        "",
        f"Pack agreement (legacy↔Llama): see `notes/v4_legacy_llama_agreement.md` (**78.8%** on t7).",
        "",
        "| Source | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |",
        "|---|---:|---|---|",
        f"| legacy | {t7_legacy['c0_pass_bases']} | {t7_legacy['e1_unit_claim_fail']} | {t7_legacy['e1_unit_evid_fail']} |",
        f"| llama | {t7_llama['c0_pass_bases']} | {t7_llama['e1_unit_claim_fail']} | {t7_llama['e1_unit_evid_fail']} |",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
