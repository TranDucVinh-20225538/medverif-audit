#!/usr/bin/env python3
"""Build JSONL of instance rows not yet in results/raw (for node30 / OpenRouter resume)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EARLY = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
G_INV = ROOT / "data" / "v3" / "instances_g_inv_paraphrase.jsonl"
RAW = ROOT / "results" / "raw"
OUT_CPU = ROOT / "data" / "v3" / "instances_score_pending_cpu_early.jsonl"
OUT_G = ROOT / "data" / "v3" / "instances_score_pending_g_inv.jsonl"
OUT_NODE30 = ROOT / "data" / "v3" / "instances_score_pending_node30.jsonl"
EXPAND = ROOT / "data" / "expand" / "instances_cpu_early.jsonl"
OUT_EXPAND = ROOT / "data" / "expand" / "instances_score_pending.jsonl"
T3_INV = ROOT / "data" / "v3" / "instances_inv_families.jsonl"
OUT_T3_INV = ROOT / "data" / "v3" / "instances_score_pending_t3_inv.jsonl"
META = ROOT / "notes" / "score_pending_manifest.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def scored_ids() -> set[str]:
    done: set[str] = set()
    for name in ("v2a_minicheck.jsonl", "v3_alignscore.jsonl"):
        path = RAW / name
        if not path.exists():
            continue
        for line in path.open():
            if line.strip():
                done.add(json.loads(line)["instance_id"])
    return done


def main() -> None:
    done = scored_ids()
    early = [r for r in read_jsonl(EARLY) if r.get("valid", True)]
    pending_cpu = [r for r in early if r["instance_id"] not in done]
    g_rows = [r for r in read_jsonl(G_INV) if r.get("valid", True)]
    pending_g = [r for r in g_rows if r["instance_id"] not in done]
    write_jsonl(OUT_CPU, pending_cpu)
    write_jsonl(OUT_G, pending_g)
    t3_inv = [r for r in read_jsonl(T3_INV) if r.get("valid") and r.get("pi_ok") == "Y"]
    pending_t3 = [r for r in t3_inv if r["instance_id"] not in done]
    write_jsonl(OUT_T3_INV, pending_t3)
    expand_rows = [r for r in read_jsonl(EXPAND) if r.get("valid", True)]
    pending_expand = [r for r in expand_rows if r["instance_id"] not in done]
    write_jsonl(OUT_EXPAND, pending_expand)
    combined = pending_cpu + pending_g + pending_t3 + pending_expand
    write_jsonl(OUT_NODE30, combined)
    manifest = {
        "scored_ids_in_raw_v2v3": len(done),
        "pending_cpu_early": len(pending_cpu),
        "pending_g_inv_paraphrase": len(pending_g),
        "pending_node30_total": len(combined),
        "pending_t3_inv_pi_ok": len(pending_t3),
        "pending_expand_set": len(pending_expand),
        "pending_node30_includes_expand": len(pending_expand) > 0,
        "paths": {
            "cpu_early_pending": str(OUT_CPU.relative_to(ROOT)),
            "g_inv_pending": str(OUT_G.relative_to(ROOT)),
            "t3_inv_pending": str(OUT_T3_INV.relative_to(ROOT)),
            "node30_combined": str(OUT_NODE30.relative_to(ROOT)),
            "expand_pending": str(OUT_EXPAND.relative_to(ROOT)),
        },
        "node30_cmd_hint": (
            "Score OUT_NODE30 with scripts/run_node30_v2v3.py (or cpu_early scorer) "
            "appending to results/raw/v2a_minicheck.jsonl and v3_alignscore.jsonl."
        ),
    }
    META.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
