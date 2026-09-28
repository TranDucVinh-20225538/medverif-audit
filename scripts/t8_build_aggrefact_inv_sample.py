#!/usr/bin/env python3
"""Up to 200 non-medical AggreFact INV + E1-unit edits (general quantity conversions)."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from general_quantity import claim_has_number_unit  # noqa: E402
from t8_aggrefact_analysis import _MED_HINT, load_split  # noqa: E402
from t8_general_inv import general_inv_edit  # noqa: E402

OUT = ROOT / "data/t8/instances_aggrefact_inv.jsonl"
OUT_V3 = ROOT / "data/v3/instances_aggrefact_inv.jsonl"
MANIFEST = ROOT / "data/t8/manifest_aggrefact_inv.json"
QC = ROOT / "qc/t8_aggrefact_inv_sample.csv"
SEED = 20260929
TARGET = 200
QC_N = 30


def content_sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode()).hexdigest()


def _base_row(i: int, row: dict, *, condition: str, claim: str, evidence: str, pair: str, kind: str, span: str) -> dict:
    sub = row.get("dataset") or "aggrefact"
    suffix = "inv_unit" if condition.endswith("inv") else "e1_unit"
    iid = f"AF{i:06d}__{sub}__{suffix}"
    claim_c0 = (row.get("claim") or "").strip()
    doc_c0 = (row.get("doc") or "").strip()
    return {
        "instance_id": iid,
        "base_id": f"AF{i:06d}",
        "type": "DOSE",
        "condition": condition,
        "magnitude": "unit_only",
        "claim": claim,
        "evidence": evidence,
        "expected_verdict": "FAIL",
        "claim_span": span,
        "evidence_span": span if condition.endswith("e1-unit") else "",
        "claim_c0": claim_c0,
        "evidence_c0": doc_c0,
        "subset": "aggrefact",
        "valid": True,
        "source_dataset": sub,
        "unit_pair": pair,
        "edit_kind": kind,
        "content_sha1": content_sha1(claim, evidence),
    }


def main() -> None:
    rows: list[dict] = []
    for split in ("dev", "test"):
        rows.extend(load_split(split))

    inv_candidates: list[dict] = []
    e1_candidates: list[dict] = []
    for i, row in enumerate(rows):
        claim = (row.get("claim") or "").strip()
        doc = (row.get("doc") or "").strip()
        if not claim or not doc:
            continue
        if _MED_HINT.search(claim):
            continue
        if not claim_has_number_unit(claim):
            continue

        edit = general_inv_edit(claim)
        if edit:
            new_claim, pair, kind, surf = edit
            inv_candidates.append(
                _base_row(
                    i,
                    row,
                    condition="T8-aggrefact-inv",
                    claim=new_claim,
                    evidence=doc,
                    pair=pair,
                    kind=kind,
                    span=surf or new_claim[:40],
                )
            )

        doc_edit = general_inv_edit(doc)
        if doc_edit:
            new_doc, pair, kind, surf = doc_edit
            e1_candidates.append(
                _base_row(
                    i,
                    row,
                    condition="T8-aggrefact-e1-unit",
                    claim=claim,
                    evidence=new_doc,
                    pair=pair,
                    kind=kind,
                    span=surf or new_doc[:40],
                )
            )

    rng = random.Random(SEED)
    inv_pool = list(inv_candidates)
    e1_pool = list(e1_candidates)
    rng.shuffle(inv_pool)
    rng.shuffle(e1_pool)
    half = TARGET // 2
    picked = inv_pool[:half] + e1_pool[: TARGET - half]
    if len(picked) < TARGET:
        seen = {r["instance_id"] for r in picked}
        rest = [r for r in inv_pool[half:] + e1_pool[max(0, TARGET - half) :] if r["instance_id"] not in seen]
        rng.shuffle(rest)
        picked.extend(rest[: TARGET - len(picked)])
    picked = picked[:TARGET]
    picked.sort(key=lambda r: r["instance_id"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    for path in (OUT, OUT_V3):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as handle:
            for row in picked:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "path": str(OUT.relative_to(ROOT)),
        "path_v3": str(OUT_V3.relative_to(ROOT)),
        "n_inv_candidates": len(inv_candidates),
        "n_e1_candidates": len(e1_candidates),
        "n_selected": len(picked),
        "n_inv_selected": sum(1 for r in picked if r["condition"] == "T8-aggrefact-inv"),
        "n_e1_selected": sum(1 for r in picked if r["condition"] == "T8-aggrefact-e1-unit"),
        "target": TARGET,
        "splits": ["dev", "test"],
        "expected_verdict": "FAIL",
    }
    MANIFEST.write_text(json.dumps(meta, indent=2) + "\n")

    rng_qc = random.Random(SEED + 1)
    qc_pool = list(picked)
    rng_qc.shuffle(qc_pool)
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(
            handle,
            fieldnames=[
                "instance_id",
                "condition",
                "edit_kind",
                "unit_pair",
                "claim_c0",
                "claim",
                "evidence_c0",
                "evidence",
                "sample",
                "PI_ok",
                "note",
            ],
        )
        w.writeheader()
        for j, row in enumerate(qc_pool[:QC_N]):
            w.writerow(
                {
                    "instance_id": row["instance_id"],
                    "condition": row["condition"],
                    "edit_kind": row.get("edit_kind", ""),
                    "unit_pair": row.get("unit_pair", ""),
                    "claim_c0": row.get("claim_c0", ""),
                    "claim": row.get("claim", ""),
                    "evidence_c0": row.get("evidence_c0", ""),
                    "evidence": row.get("evidence", ""),
                    "sample": "1",
                    "PI_ok": "",
                    "note": "",
                }
            )

    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
