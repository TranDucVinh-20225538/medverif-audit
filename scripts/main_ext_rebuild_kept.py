#!/usr/bin/env python3
"""Rebuild main_ext outputs from stage1 base_pairs (whitelist INV filter)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_main_ext_pack import (  # noqa: E402
    OUT_BASES,
    OUT_INST,
    QC,
    MANIFEST,
    STAGE1,
    base_from_stage1,
    bases_with_whitelist_inv,
    write_qc_all_inv,
)
from verifiers.io_utils import read_jsonl  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target-bases", type=int, default=80)
    args = p.parse_args()
    pairs_path = STAGE1 / "base_pairs.jsonl"
    all_bases = [base_from_stage1(r) for r in read_jsonl(pairs_path)]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tmp:
        for b in all_bases:
            tmp.write(json.dumps(b, ensure_ascii=False) + "\n")
        base_path = Path(tmp.name)
    fail_path = ROOT / "notes/main_ext_perturb_failures.json"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/perturb.py"),
            "--base",
            str(base_path),
            "--out",
            str(OUT_INST),
            "--failures",
            str(fail_path),
            "--unit-inv-policy",
            "author_whitelist",
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )
    instances = list(read_jsonl(OUT_INST))
    wl = bases_with_whitelist_inv(instances, all_bases)
    kept_bases = [b for b in all_bases if b["id"] in wl][: args.target_bases]
    kept_ids = {b["id"] for b in kept_bases}
    instances = [r for r in instances if r["base_id"] in kept_ids]
    with OUT_BASES.open("w") as handle:
        for b in kept_bases:
            handle.write(json.dumps(b, ensure_ascii=False) + "\n")
    with OUT_INST.open("w") as handle:
        for row in instances:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_qc_all_inv(instances)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/main_ext_disjointness.py"), "--bases", str(OUT_BASES)],
        check=True,
        cwd=str(ROOT),
    )
    cand_n = sum(1 for _ in read_jsonl(ROOT / "data/main_ext/candidates_selected.jsonl"))
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else {}
    manifest.update(
        {
            "stage1_bases_out": len(all_bases),
            "bases_kept": len(kept_bases),
            "bases_target": args.target_bases,
            "bases_whitelist_inv": len(wl),
            "instances": len(instances),
            "stage1_candidates": cand_n,
        }
    )
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"bases_kept": len(kept_bases), "whitelist_inv": len(wl)}, indent=2))


if __name__ == "__main__":
    main()
