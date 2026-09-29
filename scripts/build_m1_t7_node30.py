#!/usr/bin/env python3
"""Publish T7 M1-normalized pack for node30 (V1/V4 → results/raw_m1/t7/)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/t7/instances_e1_unit_m1_pending.jsonl"
OUT = ROOT / "data/v3/instances_m1_t7_node30.jsonl"
MANIFEST = ROOT / "notes/m1_t7_node30_manifest.json"


def main() -> None:
    try:
        subprocess.check_call([sys.executable, str(ROOT / "scripts/build_t7_m1_pending.py")])
    except subprocess.CalledProcessError:
        if not SRC.is_file():
            raise
        print(f"warn: build_t7_m1_pending failed; using existing {SRC}", file=sys.stderr)
    if not SRC.is_file():
        raise SystemExit(f"missing {SRC}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, OUT)
    n = sum(1 for line in OUT.open() if line.strip())
    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "source": str(SRC.relative_to(ROOT)),
        "n_total": n,
        "score_out_dir": "results/raw_m1/t7/",
        "normalization": "M1 dose/unit (apply_m1_pair); m1_preapplied=true",
        "contents": "E1-unit claim/evid + C0 per T7 base (115 bases)",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
