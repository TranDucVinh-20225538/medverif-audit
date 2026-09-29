#!/usr/bin/env python3
"""After M1 rule fix: scoped rows whose dose normalization changes text → purge + pending."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_m1_pending_node30 import INST, m1_enrich, t1_m1_scope  # noqa: E402
from quantity_norm import normalize_quantities  # noqa: E402
from raw_jsonl_backup import backup_raw  # noqa: E402

OUT = ROOT / "data" / "v3" / "instances_m1_rescore_affected.jsonl"
PENDING = ROOT / "data" / "v3" / "instances_m1_pending_node30.jsonl"
MANIFEST = ROOT / "notes" / "m1_rescore_affected_manifest.json"
RAW_M1 = ROOT / "results" / "raw_m1"
M1_FILES = (
    "v2a_minicheck.jsonl",
    "v3_alignscore.jsonl",
    "v1_medscore.jsonl",
    "v4_ragas_nli.jsonl",
)


def dose_norm_changes(text: str) -> bool:
    if not text:
        return False
    return normalize_quantities(text) != text


def purge_ids(path: Path, drop: set[str]) -> int:
    if not path.is_file() or not drop:
        return 0
    backup_raw(path)
    kept = []
    removed = 0
    for line in path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["instance_id"] in drop:
            removed += 1
            continue
        kept.append(row)
    with path.open("w") as handle:
        for row in kept:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return removed


def main() -> None:
    affected: list[dict] = []
    for line in INST.open():
        if not line.strip():
            continue
        raw = json.loads(line)
        if not t1_m1_scope(raw):
            continue
        claim, evid = raw.get("claim") or "", raw.get("evidence") or ""
        if dose_norm_changes(claim) or dose_norm_changes(evid):
            affected.append(m1_enrich(raw))
    affected.sort(key=lambda r: r["instance_id"])
    drop = {r["instance_id"] for r in affected}
    purged = {name: purge_ids(RAW_M1 / name, drop) for name in M1_FILES}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in affected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    PENDING.write_text(OUT.read_text())

    residual_path = ROOT / "results/tables/m1_inv_unit_residuals.jsonl"
    residual_ids = sorted(
        {json.loads(l)["instance_id"] for l in residual_path.open() if l.strip()}
    )
    manifest = {
        "n_affected": len(affected),
        "n_residual_inv_unit": len(residual_ids),
        "residual_ids_subset_of_affected": set(residual_ids) <= drop,
        "purged_lines": purged,
        "paths": {
            "affected": str(OUT.relative_to(ROOT)),
            "node30_pending": str(PENDING.relative_to(ROOT)),
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
