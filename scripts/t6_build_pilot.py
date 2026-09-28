#!/usr/bin/env python3
"""Stratified T6-B pilot sample (default 20 instances)."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "data" / "v3" / "instances_t6_scope.jsonl"
OUT = ROOT / "data" / "t6" / "instances_pilot_20.jsonl"
SEED = 20260929


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def stratum_key(row: dict) -> str:
    typ = row.get("type", "?")
    cond = row.get("condition", "?")
    mag = row.get("magnitude") or "none"
    if cond == "E1-claim":
        return f"{typ}|E1-claim|{mag}"
    if cond == "INV-claim":
        return f"{typ}|INV|{mag}"
    return f"{typ}|{cond}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()
    rows = read_jsonl(SCOPE)
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[stratum_key(r)].append(r)
    rng = random.Random(SEED)
    keys = sorted(by)
    rng.shuffle(keys)
    picked: list[dict] = []
    while len(picked) < args.n and keys:
        for k in list(keys):
            if len(picked) >= args.n:
                break
            pool = by[k]
            if not pool:
                keys.remove(k)
                continue
            picked.append(pool.pop(rng.randrange(len(pool))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in picked:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = {"n": len(picked), "seed": SEED, "path": str(OUT.relative_to(ROOT))}
    (ROOT / "data" / "t6" / "manifest_pilot.json").write_text(
        json.dumps(meta, indent=2) + "\n"
    )
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
