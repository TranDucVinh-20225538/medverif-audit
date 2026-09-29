#!/usr/bin/env python3
"""node30: score instances_m1plus_pending_node30.jsonl → results/raw_m1plus/ (V2a+V3)."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MEDVERIF_M1", "0")

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

import cpu_early as ce
from verifiers.io_utils import done_ids, read_jsonl


def main() -> None:
    inst_path = ROOT / "data/v3/instances_m1plus_pending_node30.jsonl"
    rows = read_jsonl(inst_path)
    out = ROOT / "results/raw_m1plus"
    out.mkdir(parents=True, exist_ok=True)
    ce.ensure_nltk()
    ckpt = ce.prepare_weights()
    from verifiers import v2a_minicheck, v3_alignscore

    v2a, _ = v2a_minicheck.load()
    v3, _ = v3_alignscore.load(str(ckpt))
    for kind, model, name in (
        ("v2a", v2a, "v2a_minicheck.jsonl"),
        ("v3", v3, "v3_alignscore.jsonl"),
    ):
        path = out / name
        ce.score_rows(kind, model, rows, path)
        print(f"{name}: {len(done_ids(path))} total lines")


if __name__ == "__main__":
    main()
