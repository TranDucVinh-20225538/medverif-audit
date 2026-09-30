#!/usr/bin/env python3
"""Granite (cpuverif) inputs for M1-strong: build chunked instance packs, or merge scored chunks into targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import read_jsonl  # noqa: E402

JSONL = "t6_granite_guardian.jsonl"
CHUNK_DIR = ROOT / "data/lane_b/granite_chunks"
SCORE_DIR = ROOT / "results/raw/lane_b/granite_chunks"
CHUNK = 80

TARGETS = (
    (
        "m1_t7_e1_unit",
        ROOT / "data/lane_b/m1_t7_e1_unit.jsonl",
        lambda r: True,
        ROOT / "results/raw/lane_b/m1_t7_e1_unit",
    ),
    (
        "m1_strong_ns",
        ROOT / "data/lane_b/m1_strong_ns.jsonl",
        lambda r: r.get("condition") in ("E1-evid", "E1-down10"),
        ROOT / "results/raw/lane_b/m1_strong_ns",
    ),
    (
        "t17_downdose",
        ROOT / "data/v3/t17_downdose.jsonl",
        lambda r: r.get("condition") == "E1-unit-down",
        ROOT / "results/raw/lane_b/t17_downdose",
    ),
    (
        "m1_t17_unit_down",
        ROOT / "data/lane_b/m1_t17_unit_down.jsonl",
        lambda r: True,
        ROOT / "results/raw/lane_b/m1_t17_unit_down",
    ),
)


def done(path: Path) -> set[str]:
    return {r["instance_id"] for r in read_jsonl(path)} if path.is_file() else set()


def build() -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    for old in CHUNK_DIR.glob("*.jsonl"):
        old.unlink()
    listing = []
    for name, src, pred, outdir in TARGETS:
        have = done(outdir / JSONL)
        rows = [r for r in read_jsonl(src) if r.get("valid", True) and pred(r) and r["instance_id"] not in have]
        for k in range(0, len(rows), CHUNK):
            path = CHUNK_DIR / f"{name}__{k // CHUNK:02d}.jsonl"
            with path.open("w") as handle:
                for r in rows[k : k + CHUNK]:
                    handle.write(json.dumps(r, ensure_ascii=False) + "\n")
            listing.append(path.name)
        print(json.dumps({"target": name, "todo": len(rows), "already": len(have)}))
    (CHUNK_DIR / "chunks.txt").write_text("\n".join(listing) + "\n")
    print(json.dumps({"chunks": len(listing)}))


def merge() -> None:
    for name, _src, _pred, outdir in TARGETS:
        target = outdir / JSONL
        have = done(target)
        added = 0
        with target.open("a") as out:
            for d in sorted(SCORE_DIR.glob(f"{name}__*")):
                for r in read_jsonl(d / JSONL):
                    if r["instance_id"] in have:
                        continue
                    out.write(json.dumps(r, ensure_ascii=False) + "\n")
                    have.add(r["instance_id"])
                    added += 1
        print(json.dumps({"target": str(target.relative_to(ROOT)), "added": added, "total": len(have)}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("build", "merge"))
    args = ap.parse_args()
    build() if args.action == "build" else merge()
