#!/usr/bin/env python3
"""Score T4 eco instances with CPU encoders V2a + V3 (resume by instance_id)."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

import cpu_early as ce
from verifiers.io_utils import done_ids, read_jsonl


def main() -> None:
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
        print(f"{name}: {len(done_ids(path))} scored (todo was {len(rows)})")


if __name__ == "__main__":
    main()
