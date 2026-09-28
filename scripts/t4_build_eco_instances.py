#!/usr/bin/env python3
"""Verifier instances: claim=eco answer, evidence=unchanged."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from non_dose_targets import NON_DOSE_TARGET_BASES  # noqa: E402

INP = ROOT / "data" / "t4" / "eco_classified.jsonl"
OUT = ROOT / "data" / "t4" / "eco_instances.jsonl"
OUT_LEGACY = ROOT / "data" / "t4" / "instances_eco_verify.jsonl"


def main() -> None:
    rows = []
    for line in INP.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("base_id") in NON_DOSE_TARGET_BASES:
            continue
        iid = f"{row['task_id']}__{row['answerer_id']}__eco"
        rows.append(
            {
                "instance_id": iid,
                "base_id": row["base_id"],
                "type": "DOSE",
                "condition": "ECO-answer",
                "magnitude": row.get("eco_category_final") or row.get("eco_category"),
                "claim": row["answer"],
                "evidence": row["evidence"],
                "expected_verdict": "PASS",
                "claim_span": row.get("target_span_claim"),
                "evidence_span": row.get("target_span_evidence"),
                "claim_c0": row.get("claim_c0"),
                "evidence_c0": row["evidence"],
                "answerer_id": row["answerer_id"],
                "openrouter_model": row.get("openrouter_model"),
                "valid": True,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"
    OUT.write_text(payload)
    OUT_LEGACY.write_text(payload)
    print(
        json.dumps(
            {
                "n": len(rows),
                "path": str(OUT.relative_to(ROOT)),
                "legacy": str(OUT_LEGACY.relative_to(ROOT)),
            }
        )
    )


if __name__ == "__main__":
    main()
