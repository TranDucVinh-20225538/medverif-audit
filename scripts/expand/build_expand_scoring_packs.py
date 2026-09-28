#!/usr/bin/env python3
"""Build expand cpu_early + node30 / T6-A pending manifests after QC v3."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from t2_build_instances import t2_full_eligible, write_jsonl  # noqa: E402

V2 = ROOT / "data" / "expand"
AUDIT = V2 / "v3" / "instances_audit.jsonl"
CPU_EARLY = V2 / "instances_cpu_early.jsonl"
NODE30 = V2 / "instances_pending_node30.jsonl"
T6A = V2 / "instances_pending_t6a.jsonl"
MANIFEST = ROOT / "notes" / "expand_node30_manifest.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def content_sha1(row: dict) -> str:
    claim = row.get("claim") or ""
    evidence = row.get("evidence") or ""
    return hashlib.sha1(f"{claim}\n{evidence}".encode("utf-8")).hexdigest()


def main() -> None:
    audit = read_jsonl(AUDIT)
    cpu_early = [
        r
        for r in audit
        if r.get("valid")
        and r.get("subset") in ("main", "threshold")
        and r.get("magnitude") != "paraphrase"
    ]
    write_jsonl(CPU_EARLY, cpu_early)
    for row in cpu_early:
        row["content_sha1"] = content_sha1(row)

    expand_elig = [r for r in cpu_early if t2_full_eligible(r, expand=True)]
    write_jsonl(T6A, expand_elig)
    write_jsonl(NODE30, cpu_early)

    manifest = {
        "instances_cpu_early": str(CPU_EARLY.relative_to(ROOT)),
        "n_cpu_early": len(cpu_early),
        "n_main": sum(1 for r in cpu_early if r.get("subset") == "main"),
        "n_threshold": sum(1 for r in cpu_early if r.get("subset") == "threshold"),
        "node30_v2v3_pending": str(NODE30.relative_to(ROOT)),
        "t6a_scope_pending": str(T6A.relative_to(ROOT)),
        "n_t6a_eligible": len(expand_elig),
        "content_sha1": "sha1(claim + newline + evidence)",
        "node30_hint": (
            "On node30: score instances_pending_node30.jsonl → results/raw/ "
            "v2a_minicheck.jsonl + v3_alignscore.jsonl (resume by instance_id). "
            "T6-A: local V1 anchor run on instances_pending_t6a.jsonl if used on main set."
        ),
        "hpc_hint": "jobs/run_expand_score_openrouter.sh (V1 + V4 append)",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
