#!/usr/bin/env python3
"""~200 non-medical AggreFact claims → INV-style unit-only claim edits for T8 scoring."""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import e1_unit_only_swap  # noqa: E402
from t8_aggrefact_analysis import _MED_HINT, dose_tokens, load_split  # noqa: E402

OUT = ROOT / "data/t8/instances_aggrefact_inv.jsonl"
OUT_V3 = ROOT / "data/v3/instances_aggrefact_inv.jsonl"
MANIFEST = ROOT / "data/t8/manifest_aggrefact_inv.json"
SEED = 20260929
TARGET = 200


def content_sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode()).hexdigest()


def main() -> None:
    rows = load_split("dev")
    candidates = []
    for i, row in enumerate(rows):
        claim = (row.get("claim") or "").strip()
        doc = (row.get("doc") or "").strip()
        if not claim or not doc:
            continue
        if _MED_HINT.search(claim):
            continue
        spans = dose_tokens(claim)
        if not spans:
            continue
        # pick first swappable dose in claim
        for num, unit, surface in spans:
            swap = e1_unit_only_swap(surface)
            if not swap:
                continue
            new_span, pair = swap
            new_claim = claim.replace(surface, new_span, 1)
            if new_claim == claim:
                continue
            sub = row.get("dataset") or "aggrefact"
            iid = f"AF{i:06d}__{sub}__inv_unit"
            candidates.append(
                {
                    "instance_id": iid,
                    "base_id": f"AF{i:06d}",
                    "type": "DOSE",
                    "condition": "T8-aggrefact-inv",
                    "magnitude": "unit_only",
                    "claim": new_claim,
                    "evidence": doc,
                    "expected_verdict": "FAIL",
                    "claim_span": new_span,
                    "evidence_span": surface,
                    "claim_c0": claim,
                    "evidence_c0": doc,
                    "subset": "aggrefact",
                    "valid": True,
                    "source_dataset": sub,
                    "unit_pair": pair,
                    "content_sha1": content_sha1(new_claim, doc),
                }
            )
            break

    rng = random.Random(SEED)
    rng.shuffle(candidates)
    picked = candidates[:TARGET]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for path in (OUT, OUT_V3):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as handle:
            for row in picked:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "path": str(OUT.relative_to(ROOT)),
        "path_v3": str(OUT_V3.relative_to(ROOT)),
        "n_candidates": len(candidates),
        "n_selected": len(picked),
        "target": TARGET,
        "expected_verdict": "FAIL",
    }
    MANIFEST.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
