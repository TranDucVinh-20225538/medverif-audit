#!/usr/bin/env python3
"""PI_ok=Y freq/route INV rows for node30 Bespoke (v2b) rescore."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T3_PATHS = (
    ROOT / "data/v3/instances_inv_families.jsonl",
    ROOT / "data/t3/instances_inv_families.jsonl",
)
LABELS = ROOT / "qc/inv_claim_PI_ok_labels.csv"
OUT = ROOT / "data/v3/instances_t3_bespoke_pending_node30.jsonl"
MANIFEST = ROOT / "notes/t3_bespoke_pending_node30_manifest.json"


def pi_ok_ids() -> set[str]:
    out: set[str] = set()
    for row in csv.DictReader(LABELS.open()):
        if (row.get("PI_ok") or "").strip().upper() != "Y":
            continue
        if (row.get("family") or "").strip() not in ("inv_frequency", "inv_route"):
            continue
        out.add(row["instance_id"].strip())
    return out


def main() -> None:
    allowed = pi_ok_ids()
    by_id: dict[str, dict] = {}
    for path in T3_PATHS:
        if not path.is_file():
            continue
        for line in path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["instance_id"] in allowed:
                by_id.setdefault(row["instance_id"], row)
    rows = [by_id[iid] for iid in sorted(allowed) if iid in by_id and by_id[iid].get("valid", True)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "n": len(rows),
        "pi_ok_label_ids": len(allowed),
        "score_to": "results/raw/t3/t6_bespoke_minicheck.jsonl or v2b_bespoke.jsonl",
        "node30_hint": "jobs/run_node30_score_pending.sh or bespoke-only job",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
