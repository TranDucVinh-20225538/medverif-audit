#!/usr/bin/env python3
"""node30: V2a + V3 + T6-A (7 specialized checkers) on eco_instances.jsonl."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

ROOT = Path(os.environ.get("MEDVERIF_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "src"))

import cpu_early as ce
from verifiers.io_utils import done_ids, read_jsonl


def main() -> None:
    inst = ROOT / "data/t4/eco_instances.jsonl"
    if not inst.is_file():
        inst = ROOT / "data/t4/instances_eco_verify.jsonl"
    rows = read_jsonl(inst)
    raw = ROOT / "results/raw/t4_eco"
    raw.mkdir(parents=True, exist_ok=True)
    ce.ensure_nltk()
    ckpt = ce.prepare_weights()
    from verifiers import v2a_minicheck, v3_alignscore

    v2a, _ = v2a_minicheck.load()
    v3, _ = v3_alignscore.load(str(ckpt))
    for kind, model, name in (
        ("v2a", v2a, "v2a_minicheck.jsonl"),
        ("v3", v3, "v3_alignscore.jsonl"),
    ):
        path = raw / name
        ce.score_rows(kind, model, rows, path)
        print(f"{name}: {len(done_ids(path))} scored (instances {len(rows)})")

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/t6a_score_instances.py"),
            "--instances",
            str(inst),
            "--outdir",
            str(raw),
            "--checker",
            "all",
        ],
        check=True,
        env={**os.environ, "MEDVERIF_ROOT": str(ROOT), "PYTHONPATH": str(ROOT / "src")},
    )


if __name__ == "__main__":
    main()
