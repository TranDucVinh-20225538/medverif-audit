#!/usr/bin/env python3
"""Build JSONL of instance rows not yet in results/raw (for node30 / OpenRouter resume)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EARLY = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
G_INV = ROOT / "data" / "v3" / "instances_g_inv_paraphrase.jsonl"
RAW = ROOT / "results" / "raw"
RAW_T3 = ROOT / "results/raw/t3"
OUT_CPU = ROOT / "data" / "v3" / "instances_score_pending_cpu_early.jsonl"
OUT_G = ROOT / "data" / "v3" / "instances_score_pending_g_inv.jsonl"
OUT_NODE30 = ROOT / "data" / "v3" / "instances_score_pending_node30.jsonl"
EXPAND = ROOT / "data" / "expand" / "instances_cpu_early.jsonl"
OUT_EXPAND = ROOT / "data" / "expand" / "instances_score_pending.jsonl"
T3_INV = ROOT / "data" / "v3" / "instances_inv_families.jsonl"
T3_LABELS = ROOT / "qc/inv_claim_PI_ok_labels.csv"
OUT_T3_INV = ROOT / "data" / "v3" / "instances_score_pending_t3_inv.jsonl"
POL_FLIP = ROOT / "data/v3/instances_pol_flip_pending_node30.jsonl"
M1PLUS = ROOT / "data/v3/instances_m1plus_pending_node30.jsonl"
OUT_M1PLUS = ROOT / "data/v3/instances_m1plus_score_pending_node30.jsonl"
T3_BESPOKE = ROOT / "data/v3/instances_t3_bespoke_pending_node30.jsonl"
RAW_M1PLUS = ROOT / "results/raw_m1plus"
META = ROOT / "notes/score_pending_manifest.json"


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


def scored_ids_raw(*dirs: Path) -> set[str]:
    done: set[str] = set()
    for raw_dir in dirs:
        for name in ("v2a_minicheck.jsonl", "v3_alignscore.jsonl"):
            path = raw_dir / name
            if not path.is_file():
                continue
            for line in path.open():
                if line.strip():
                    done.add(json.loads(line)["instance_id"])
    return done


def t3_pi_ok_ids() -> set[str]:
    out: set[str] = set()
    for row in csv.DictReader(T3_LABELS.open()):
        if (row.get("PI_ok") or "").strip().upper() != "Y":
            continue
        if (row.get("family") or "").strip() in ("inv_frequency", "inv_route"):
            out.add(row["instance_id"].strip())
    return out


def m1plus_scored_ids() -> set[str]:
    done: set[str] = set()
    if not RAW_M1PLUS.is_dir():
        return done
    for name in ("v2a_minicheck.jsonl", "v3_alignscore.jsonl"):
        path = RAW_M1PLUS / name
        if not path.is_file():
            continue
        for line in path.open():
            if line.strip():
                done.add(json.loads(line)["instance_id"])
    return done


def main() -> None:
    done = scored_ids_raw(RAW, RAW_T3)
    early = [r for r in read_jsonl(EARLY) if r.get("valid", True)]
    pending_cpu = [r for r in early if r["instance_id"] not in done]
    g_rows = [r for r in read_jsonl(G_INV) if r.get("valid", True)]
    pending_g = [r for r in g_rows if r["instance_id"] not in done]
    pi_ok = t3_pi_ok_ids()
    t3_inv = [
        r
        for r in read_jsonl(T3_INV)
        if r.get("valid", True) and r["instance_id"] in pi_ok
    ]
    pending_t3 = [r for r in t3_inv if r["instance_id"] not in done]
    write_jsonl(OUT_T3_INV, pending_t3)
    expand_rows = [r for r in read_jsonl(EXPAND) if r.get("valid", True)]
    pending_expand = [r for r in expand_rows if r["instance_id"] not in done]
    write_jsonl(OUT_EXPAND, pending_expand)
    pol_flip = read_jsonl(POL_FLIP)
    t3_bespoke = read_jsonl(T3_BESPOKE)
    m1plus_done = m1plus_scored_ids()
    m1plus_all = read_jsonl(M1PLUS)
    pending_m1plus = [r for r in m1plus_all if r["instance_id"] not in m1plus_done]
    write_jsonl(OUT_M1PLUS, pending_m1plus)

    write_jsonl(OUT_CPU, pending_cpu)
    write_jsonl(OUT_G, pending_g)
    combined = pending_cpu + pending_g + pending_t3 + pending_expand + pol_flip + t3_bespoke
    write_jsonl(OUT_NODE30, combined)
    manifest = {
        "scored_ids_in_raw_v2v3": len(done),
        "pending_cpu_early": len(pending_cpu),
        "pending_g_inv_paraphrase": len(pending_g),
        "pending_node30_total": len(combined),
        "pending_t3_inv_pi_ok": len(pending_t3),
        "pending_pol_flip_rescore": len(pol_flip),
        "pending_t3_bespoke_node30": len(t3_bespoke),
        "pending_m1plus_node30": len(pending_m1plus),
        "pending_expand_set": len(pending_expand),
        "pending_node30_includes_expand": len(pending_expand) > 0,
        "paths": {
            "cpu_early_pending": str(OUT_CPU.relative_to(ROOT)),
            "g_inv_pending": str(OUT_G.relative_to(ROOT)),
            "t3_inv_pending": str(OUT_T3_INV.relative_to(ROOT)),
            "pol_flip_pending": str(POL_FLIP.relative_to(ROOT)),
            "t3_bespoke_pending": str(T3_BESPOKE.relative_to(ROOT)),
            "m1plus_pending": str(OUT_M1PLUS.relative_to(ROOT)),
            "node30_combined": str(OUT_NODE30.relative_to(ROOT)),
            "expand_pending": str(OUT_EXPAND.relative_to(ROOT)),
        },
        "node30_cmd_hint": (
            "Non-M1: jobs/run_node30_score_pending.sh → results/raw/. "
            "M1+: jobs/run_t1_m1plus_score_node30.sh → results/raw_m1plus/. "
            "T7 M1: jobs/run_t7_m1_node30.sh → results/raw_m1/t7/."
        ),
    }
    META.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
