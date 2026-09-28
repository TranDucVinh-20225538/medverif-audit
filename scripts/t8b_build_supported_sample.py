#!/usr/bin/env python3
"""T8b: supported AggreFact pairs — format-mismatch vs qty-match samples for false-alarm test."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from general_quantity import claim_has_any_number, format_quantity_mismatch  # noqa: E402
from t8_aggrefact_analysis import load_split  # noqa: E402

OUT = ROOT / "data/t8/instances_aggrefact_t8b.jsonl"
OUT_V3 = ROOT / "data/v3/instances_aggrefact_t8b.jsonl"
MANIFEST = ROOT / "data/t8/manifest_aggrefact_t8b.json"
SEED = 20260929
MAX_PER_GROUP = 300


def sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode()).hexdigest()


def classify(row: dict) -> str | None:
    if int(row.get("label", -1)) != 1:
        return None
    claim = row.get("claim") or ""
    doc = row.get("doc") or ""
    if not claim_has_any_number(claim):
        return "no_quantity"
    if format_quantity_mismatch(claim, doc):
        return "format_mismatch"
    return "qty_match"


def inst(row_id: str, row: dict, group: str) -> dict:
    claim = (row.get("claim") or "").strip()
    doc = (row.get("doc") or "").strip()
    sub = row.get("dataset") or "aggrefact"
    return {
        "instance_id": f"T8B{row_id}__{sub}__{group}",
        "base_id": f"T8B{row_id}",
        "type": "T8B",
        "condition": f"T8b-supported-{group}",
        "magnitude": "native",
        "claim": claim,
        "evidence": doc,
        "expected_verdict": "PASS",
        "subset": "aggrefact",
        "valid": True,
        "source_dataset": sub,
        "t8b_group": group,
        "aggrefact_label": 1,
        "content_sha1": sha1(claim, doc),
    }


def main() -> None:
    buckets: dict[str, list[tuple[str, dict]]] = {
        "format_mismatch": [],
        "qty_match": [],
        "no_quantity": [],
    }
    for split in ("dev", "test"):
        for i, row in enumerate(load_split(split)):
            g = classify(row)
            if g:
                buckets[g].append((f"{split[0].upper()}{i:06d}", row))

    rng = random.Random(SEED)
    for g in buckets:
        rng.shuffle(buckets[g])
    n = min(MAX_PER_GROUP, len(buckets["format_mismatch"]), len(buckets["qty_match"]))
    if n == 0:
        raise SystemExit("empty format_mismatch or qty_match pool")
    picked = [inst(rid, row, "format_mismatch") for rid, row in buckets["format_mismatch"][:n]]
    picked += [inst(rid, row, "qty_match") for rid, row in buckets["qty_match"][:n]]
    picked.sort(key=lambda r: r["instance_id"])

    for path in (OUT, OUT_V3):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as handle:
            for row in picked:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "path": str(OUT.relative_to(ROOT)),
        "path_v3": str(OUT_V3.relative_to(ROOT)),
        "supported_total_by_group": {k: len(v) for k, v in buckets.items()},
        "n_sample_per_group": n,
        "n_instances": len(picked),
        "expected_verdict": "PASS",
        "groups_scored": ["format_mismatch", "qty_match"],
    }
    MANIFEST.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
