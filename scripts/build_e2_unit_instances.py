#!/usr/bin/env python3
"""Build E2-unit instances for 115 T7 bases; refresh node30 pending slice."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from e2_unit import generate_e2_unit_t7  # noqa: E402

OUT = ROOT / "data/e2/instances_e2_unit_t7.jsonl"
MANIFEST = ROOT / "data/e2/manifest_e2_unit_t7.json"
FAILURES = ROOT / "data/e2/e2_unit_build_failures.json"
PENDING_NODE30 = ROOT / "data/e2/instances_e2_unit_pending_node30.jsonl"
PENDING_EXPAND = ROOT / "data/expand/instances_pending_node30.jsonl"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""))


def merge_pending_expand(e2_rows: list[dict]) -> int:
    """Append E2-unit rows not already in expand pending (by instance_id)."""
    existing: set[str] = set()
    lines: list[str] = []
    if PENDING_EXPAND.is_file():
        for line in PENDING_EXPAND.open():
            if not line.strip():
                continue
            existing.add(json.loads(line)["instance_id"])
            lines.append(line.rstrip("\n"))
    added = 0
    for row in e2_rows:
        iid = row["instance_id"]
        if iid in existing:
            continue
        lines.append(json.dumps(row, ensure_ascii=False))
        existing.add(iid)
        added += 1
    if added:
        PENDING_EXPAND.write_text("\n".join(lines) + "\n")
    return added


def main() -> None:
    instances, failures, meta = generate_e2_unit_t7(ROOT)
    instances.sort(key=lambda r: r["instance_id"])
    write_jsonl(OUT, instances)
    FAILURES.write_text(json.dumps({"failures": failures, **meta}, indent=2) + "\n")
    write_jsonl(PENDING_NODE30, instances)
    added = merge_pending_expand(instances)
    manifest = {
        **meta,
        "n": len(instances),
        "instances": str(OUT.relative_to(ROOT)),
        "expected_verdict": "PASS",
        "description": "×1000 unit swap on claim AND evidence (T7 bases)",
        "budget_usd_cap": 1.5,
        "hpc_job": "jobs/run_e2_unit_hpc.sh",
        "node30_job": "jobs/run_e2_unit_node30.sh",
        "raw_scores": "results/raw/e2_unit",
        "report": "scripts/e2_unit_comparison_report.py",
        "pending_node30": str(PENDING_NODE30.relative_to(ROOT)),
        "pending_expand_merged": added,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
