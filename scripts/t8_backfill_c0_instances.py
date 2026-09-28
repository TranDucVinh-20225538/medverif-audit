#!/usr/bin/env python3
"""Backfill aggrefact_label + emit C0 instances for existing T8 unit sample bases."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t8_aggrefact_analysis import load_split  # noqa: E402

INV = ROOT / "data/t8/instances_aggrefact_inv.jsonl"
INV_V3 = ROOT / "data/v3/instances_aggrefact_inv.jsonl"
C0 = ROOT / "data/t8/instances_aggrefact_c0.jsonl"
C0_V3 = ROOT / "data/v3/instances_aggrefact_c0.jsonl"


def norm(s: str) -> str:
    return " ".join((s or "").split())


def build_index() -> dict[tuple[str, str], dict]:
    idx: dict[tuple[str, str], dict] = {}
    for split in ("dev", "test"):
        for i, row in enumerate(load_split(split)):
            key = (row.get("dataset") or "", norm(row.get("claim") or ""))
            idx[key] = {**row, "_split": split, "_index": i}
    return idx


def sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode()).hexdigest()


def main() -> None:
    index = build_index()
    inv_rows = [json.loads(line) for line in INV.open() if line.strip()]
    updated: list[dict] = []
    c0_rows: list[dict] = []
    missing = 0
    for row in inv_rows:
        key = (row.get("source_dataset") or "", norm(row.get("claim_c0") or ""))
        src = index.get(key)
        if not src:
            missing += 1
            label = None
        else:
            label = int(src.get("label", -1))
            row["aggrefact_label"] = label
            row["source_split"] = src["_split"]
            row["source_index"] = src["_index"]
        updated.append(row)

        bid = row["base_id"]
        sub = row.get("source_dataset") or "aggrefact"
        claim = (row.get("claim_c0") or "").strip()
        doc = (row.get("evidence_c0") or "").strip()
        c0_id = f"{bid}__{sub}__c0"
        if not any(c["instance_id"] == c0_id for c in c0_rows):
            c0_rows.append(
                {
                    "instance_id": c0_id,
                    "base_id": bid,
                    "type": "DOSE",
                    "condition": "T8-aggrefact-c0",
                    "magnitude": "native",
                    "claim": claim,
                    "evidence": doc,
                    "expected_verdict": "PASS",
                    "claim_c0": claim,
                    "evidence_c0": doc,
                    "subset": "aggrefact",
                    "valid": True,
                    "source_dataset": sub,
                    "aggrefact_label": label,
                    "source_split": row.get("source_split"),
                    "source_index": row.get("source_index"),
                    "content_sha1": sha1(claim, doc),
                }
            )

    c0_rows.sort(key=lambda r: r["instance_id"])
    for path, rows in ((INV, updated), (INV_V3, updated), (C0, c0_rows), (C0_V3, c0_rows)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "inv_rows": len(updated),
                "c0_bases": len(c0_rows),
                "label_lookup_miss": missing,
                "supported_c0": sum(1 for r in c0_rows if r.get("aggrefact_label") == 1),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
