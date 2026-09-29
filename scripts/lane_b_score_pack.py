#!/usr/bin/env python3
"""Score one Lane B pack on HPC (cpuverif): 7× T6-A + V2a/V3 if missing vs node30."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE30 = ROOT / "results/raw_node30"
T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"

CPU_VERIFIERS = [
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
    "t6a_summac_zs",
    "t6a_summac_conv",
    "t6a_hhem",
    "t6a_granite_guardian",
]
API_CPU = ("v2a_minicheck", "v3_alignscore")


def node30_has(checker_jsonl: str, instance_id: str) -> bool:
    p = NODE30 / checker_jsonl
    if not p.is_file():
        return False
    for line in p.open():
        if not line.strip():
            continue
        if json.loads(line).get("instance_id") == instance_id:
            return True
    return False


def pack_complete(outdir: Path, checker_id: str, jsonl_name: str, n_inst: int) -> bool:
    out = outdir / jsonl_name
    if not out.is_file():
        return False
    return sum(1 for _ in out.open()) >= n_inst


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--pack", required=True, help="subdir under results/raw/lane_b/")
    p.add_argument("--instances", type=Path, required=True)
    args = p.parse_args()
    outdir = ROOT / "results/raw/lane_b" / args.pack
    outdir.mkdir(parents=True, exist_ok=True)
    n_inst = sum(1 for _ in args.instances.open() if _.strip())
    os.environ["MEDVERIF_SCORE_ENV"] = "hpc"

    manifest = json.loads(T6_MANIFEST.read_text())
    id_to_jsonl = {c["id"]: c["jsonl"] for c in manifest["checkers"]}

    for cid in CPU_VERIFIERS:
        jname = id_to_jsonl[cid]
        if pack_complete(outdir, cid, jname, n_inst):
            print(json.dumps({"skip": cid, "reason": "complete"}))
            continue
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/t6a_score_instances.py"),
                "--instances",
                str(args.instances),
                "--outdir",
                str(outdir),
                "--checker",
                cid,
            ],
            check=True,
            cwd=str(ROOT),
        )
    sample_ids = []
    for line in args.instances.open():
        if line.strip():
            sample_ids.append(json.loads(line)["instance_id"])
            if len(sample_ids) >= 5:
                break
    for vid in API_CPU:
        out = outdir / f"{vid}.jsonl"
        if out.is_file() and sum(1 for _ in out.open()) >= n_inst:
            continue
        skip_all = all(node30_has(f"{vid.replace('v2a', 'v2a')}.jsonl" if vid == "v2a_minicheck" else "v3_alignscore.jsonl", iid) for iid in sample_ids)
        if vid == "v2a_minicheck":
            skip_all = all(node30_has("v2a_minicheck.jsonl", iid) for iid in sample_ids)
        else:
            skip_all = all(node30_has("v3_alignscore.jsonl", iid) for iid in sample_ids)
        if skip_all and sample_ids:
            print(json.dumps({"skip": vid, "reason": "node30_has_sample"}))
            continue
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "src/score_jsonl.py"),
                "--verifier",
                vid,
                "--instances",
                str(args.instances),
                "--out",
                str(out),
            ],
            check=True,
            cwd=str(ROOT),
            env={**os.environ, "CUDA_VISIBLE_DEVICES": ""},
        )
    print(json.dumps({"pack": args.pack, "instances": n_inst, "outdir": str(outdir.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
