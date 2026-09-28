#!/usr/bin/env python3
"""Build T9 NeMo Guardrails / AlignScore input sets (a–d) + combined manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from review_filters import effective_unit_natural_y, unit_natural_labels  # noqa: E402
from t4_eco_compare import apply_pi_override, load_pi_label_paths  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

OUT_DIR = ROOT / "data" / "t9"
MANIFEST = ROOT / "data" / "t9" / "manifest.json"
CLASSIFIED = ROOT / "data" / "t4" / "eco_classified.jsonl"
MAIN = ROOT / "data" / "v3" / "instances_main.jsonl"
EXPAND = ROOT / "data" / "expand" / "instances_cpu_early.jsonl"
T7 = ROOT / "data" / "t7" / "instances_e1_unit.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def t9_row(
    *,
    instance_id: str,
    t9_group: str,
    claim: str,
    evidence: str,
    expected_block: bool | None,
    **extra,
) -> dict:
    ev = evidence or ""
    return {
        "instance_id": instance_id,
        "t9_group": t9_group,
        "claim": claim,
        "evidence": ev,
        "relevant_chunks": [ev] if ev else [],
        "bot_message": claim,
        "expected_block": expected_block,
        **extra,
    }


def inv_span_before(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    return str(claim.get("span_before") or row.get("claim_span") or "")


def build_a(labels: dict) -> list[dict]:
    rows = []
    for r in read_jsonl(CLASSIFIED):
        if r.get("subset") != "main":
            continue
        key = (r["task_id"], r["answerer_id"])
        lab = labels.get(key)
        if not lab or (lab.get("PI_ok") or "").strip().upper() != "Y":
            continue
        cat = apply_pi_override(r["task_id"], r["answerer_id"], r.get("eco_category_final") or r.get("eco_category") or "", labels)
        if cat != "exact_verbatim":
            continue
        iid = f"{r['task_id']}__{r['answerer_id']}__eco"
        rows.append(
            t9_row(
                instance_id=iid,
                t9_group="a",
                claim=r["answer"],
                evidence=r["evidence"],
                expected_block=False,
                base_id=r.get("base_id"),
                eco_category_final=cat,
            )
        )
    return rows


def build_b_eco(labels: dict) -> list[dict]:
    rows = []
    for r in read_jsonl(CLASSIFIED):
        if r.get("subset") != "main":
            continue
        key = (r["task_id"], r["answerer_id"])
        lab = labels.get(key)
        if not lab or (lab.get("PI_ok") or "").strip().upper() != "Y":
            continue
        cat = apply_pi_override(r["task_id"], r["answerer_id"], r.get("eco_category_final") or r.get("eco_category") or "", labels)
        if cat not in ("exact_surface_variant", "frequency_rephrased"):
            continue
        iid = f"{r['task_id']}__{r['answerer_id']}__eco"
        rows.append(
            t9_row(
                instance_id=iid,
                t9_group="b",
                claim=r["answer"],
                evidence=r["evidence"],
                expected_block=False,
                base_id=r.get("base_id"),
                eco_category_final=cat,
                stratum="eco_reexpressed",
            )
        )
    return rows


def build_b_inv_natural() -> list[dict]:
    labels = unit_natural_labels()
    rows = []
    for path in (MAIN, EXPAND):
        for r in read_jsonl(path):
            if not r.get("valid", True):
                continue
            if r.get("subset") != "main" and path == MAIN:
                continue
            if r.get("condition") != "INV-claim" or r.get("magnitude") != "unit_conversion":
                continue
            orig = inv_span_before(r)
            rule_y = bool(rule_natural_unit_conversion_label(orig))
            if not effective_unit_natural_y(r["base_id"], rule_y):
                continue
            rows.append(
                t9_row(
                    instance_id=r["instance_id"],
                    t9_group="b",
                    claim=r["claim"],
                    evidence=r["evidence"],
                    expected_block=False,
                    base_id=r.get("base_id"),
                    stratum="inv_unit_natural",
                )
            )
    return rows


def build_c() -> list[dict]:
    rows = []
    for r in read_jsonl(MAIN):
        if not r.get("valid", True):
            continue
        if r.get("subset") != "main":
            continue
        if r.get("type") != "DOSE":
            continue
        if r.get("condition") != "E1-claim" or r.get("magnitude") != "x2":
            continue
        rows.append(
            t9_row(
                instance_id=r["instance_id"],
                t9_group="c",
                claim=r["claim"],
                evidence=r["evidence"],
                expected_block=True,
                base_id=r.get("base_id"),
            )
        )
    return rows


def build_d() -> list[dict]:
    rows = []
    for r in read_jsonl(T7):
        if not r.get("valid", True):
            continue
        rows.append(
            t9_row(
                instance_id=r["instance_id"],
                t9_group="d",
                claim=r["claim"],
                evidence=r["evidence"],
                expected_block=True,
                base_id=r.get("base_id"),
                condition=r.get("condition"),
            )
        )
    return rows


def main() -> None:
    labels = load_pi_label_paths([ROOT / "qc/eco_PI_ok_labels.csv", ROOT / "qc/eco2_PI_ok_labels.csv"])
    a = build_a(labels)
    b = build_b_eco(labels) + build_b_inv_natural()
    c = build_c()
    d = build_d()
    write_jsonl(OUT_DIR / "instances_a_verbatim.jsonl", a)
    write_jsonl(OUT_DIR / "instances_b_reexpressed.jsonl", b)
    write_jsonl(OUT_DIR / "instances_c_e1_x2.jsonl", c)
    write_jsonl(OUT_DIR / "instances_d_t7_e1_unit.jsonl", d)
    combined = a + b + c + d
    write_jsonl(OUT_DIR / "instances_all.jsonl", combined)
    manifest = {
        "nemoguardrails_pin": "0.24.1",
        "groups": {
            "a_verbatim": len(a),
            "b_reexpressed": len(b),
            "c_e1_x2": len(c),
            "d_t7_e1_unit": len(d),
            "all": len(combined),
        },
        "paths": {
            "a": "data/t9/instances_a_verbatim.jsonl",
            "b": "data/t9/instances_b_reexpressed.jsonl",
            "c": "data/t9/instances_c_e1_x2.jsonl",
            "d": "data/t9/instances_d_t7_e1_unit.jsonl",
            "all": "data/t9/instances_all.jsonl",
        },
        "b_strata": {
            "eco_reexpressed": sum(1 for r in b if r.get("stratum") == "eco_reexpressed"),
            "inv_unit_natural": sum(1 for r in b if r.get("stratum") == "inv_unit_natural"),
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
