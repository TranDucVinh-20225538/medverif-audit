#!/usr/bin/env python3
"""T7: E1-unit instances + C0 for same bases, M1-normalized (node30 / HPC M1 rescore)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quantity_norm import apply_m1_pair  # noqa: E402

T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
MAIN = ROOT / "data/v3/instances_main.jsonl"
EXPAND = ROOT / "data/expand/instances_cpu_early.jsonl"
OUT = ROOT / "data/t7/instances_e1_unit_m1_pending.jsonl"
MANIFEST = ROOT / "notes/t7_m1_pending_manifest.json"


def content_sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode("utf-8")).hexdigest()


def m1_enrich(row: dict) -> dict:
    claim_m1, evidence_m1 = apply_m1_pair(row.get("claim") or "", row.get("evidence") or "")
    out = dict(row)
    out["claim"] = claim_m1
    out["evidence"] = evidence_m1
    out["content_sha1"] = content_sha1(claim_m1, evidence_m1)
    out["m1_preapplied"] = True
    return out


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    t7_rows = read_jsonl(T7)
    bases = {r["base_id"] for r in t7_rows}
    c0_by_base: dict[str, dict] = {}
    for row in read_jsonl(MAIN) + read_jsonl(EXPAND):
        if not row.get("valid", True):
            continue
        if row["base_id"] not in bases or row.get("condition") != "C0":
            continue
        c0_by_base[row["base_id"]] = row

    missing_c0 = sorted(bases - set(c0_by_base))
    if missing_c0:
        raise SystemExit(f"missing C0 for T7 bases: {missing_c0[:5]} n={len(missing_c0)}")

    out_rows: list[dict] = []
    seen: set[str] = set()
    for row in t7_rows:
        out_rows.append(m1_enrich(row))
        seen.add(row["instance_id"])
    for bid in sorted(bases):
        row = c0_by_base[bid]
        if row["instance_id"] in seen:
            continue
        out_rows.append(m1_enrich(row))
        seen.add(row["instance_id"])

    out_rows.sort(key=lambda r: r["instance_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in out_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "n_e1_unit": len(t7_rows),
        "n_c0": len(c0_by_base),
        "n_total": len(out_rows),
        "n_bases": len(bases),
        "score_out_dir": "results/raw_m1/t7/",
        "m1": "apply_m1_pair; m1_preapplied=true; score with MEDVERIF_M1=0 or idempotent MEDVERIF_M1=1",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
