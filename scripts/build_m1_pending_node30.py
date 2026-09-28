#!/usr/bin/env python3
"""Build T1-M1 node30 pending: C0 / E1 / INV-unit rows with M1-normalized claim+evidence + sha1."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quantity_norm import apply_m1_pair  # noqa: E402

INST = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
OUT = ROOT / "data" / "v3" / "instances_m1_pending_node30.jsonl"
RAW_M1 = ROOT / "results" / "raw_m1"
MANIFEST = ROOT / "notes" / "m1_pending_node30_manifest.json"


def content_sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode("utf-8")).hexdigest()


def t1_m1_scope(row: dict) -> bool:
    if not row.get("valid", True):
        return False
    cond = row.get("condition") or ""
    if cond == "C0":
        return True
    if cond in ("E1-claim", "E1-evid"):
        return True
    if cond == "INV-claim" and row.get("magnitude") == "unit_conversion":
        return True
    return False


def m1_enrich(row: dict) -> dict:
    claim_m1, evidence_m1 = apply_m1_pair(row.get("claim") or "", row.get("evidence") or "")
    out = dict(row)
    out["claim"] = claim_m1
    out["evidence"] = evidence_m1
    out["content_sha1"] = content_sha1(claim_m1, evidence_m1)
    out["m1_preapplied"] = True
    return out


def scored_m1_ids() -> set[str]:
    done: set[str] = set()
    for name in ("v2a_minicheck.jsonl", "v3_alignscore.jsonl"):
        path = RAW_M1 / name
        if not path.is_file():
            continue
        for line in path.open():
            if line.strip():
                done.add(json.loads(line)["instance_id"])
    return done


def main() -> None:
    done = scored_m1_ids()
    scoped: list[dict] = []
    for line in INST.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if not t1_m1_scope(row):
            continue
        scoped.append(m1_enrich(row))
    pending = [r for r in scoped if r["instance_id"] not in done]
    pending.sort(key=lambda r: r["instance_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in pending:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_cond: dict[str, int] = {}
    for r in pending:
        key = r["condition"]
        if key == "INV-claim":
            key = "INV-unit"
        by_cond[key] = by_cond.get(key, 0) + 1

    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "scope": "C0, E1-claim, E1-evid, INV-claim unit_conversion (valid cpu_early)",
        "m1": "claim/evidence normalized via quantity_norm.apply_m1_pair; m1_preapplied=true",
        "content_sha1": "sha1(m1_claim + newline + m1_evidence)",
        "score_out_dir": "results/raw_m1/<verifier>.jsonl",
        "n_scoped": len(scoped),
        "n_pending": len(pending),
        "n_already_in_raw_m1": len(scoped) - len(pending),
        "pending_by_condition": by_cond,
        "node30_hint": (
            "Score with MEDVERIF_M1=0 (text pre-normalized) or MEDVERIF_M1=1 (idempotent); "
            "append to results/raw_m1/v2a_minicheck.jsonl and v3_alignscore.jsonl"
        ),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
