#!/usr/bin/env python3
"""Lane C: M1 H2 instance pack (main C0/INV/E1 + T7 E1-unit on main bases)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402

MAIN = ROOT / "data/v3/instances_main.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
OUT = ROOT / "data/lane_c/m1_h2_main.jsonl"
MANIFEST = ROOT / "notes/lane_c_m1_pack.json"


def main() -> None:
    main_bases = {
        r["base_id"]
        for r in read_jsonl(MAIN)
        if r.get("valid", True) and r.get("subset") == "main"
    }
    rows: list[dict] = []
    for r in read_jsonl(MAIN):
        if not r.get("valid", True) or r.get("subset") != "main":
            continue
        cond, mag = r.get("condition"), r.get("magnitude")
        keep = (
            (cond == "C0" and mag == "none")
            or (cond == "INV-claim" and mag == "unit_conversion")
            or (cond in ("E1-claim", "E1-evid") and mag in ("x2", "x10"))
        )
        if keep:
            rows.append(r)
    for r in read_jsonl(T7):
        if not r.get("valid", True):
            continue
        if r["base_id"] not in main_bases:
            continue
        if r.get("condition") in ("E1-unit-claim", "E1-unit-evid"):
            rows.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {"n": len(rows), "path": str(OUT.relative_to(ROOT))}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
