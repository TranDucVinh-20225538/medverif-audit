#!/usr/bin/env python3
"""Build T19 evaluation pack: main DOSE slices + T7 E1-unit + T14 (+ T17 if present)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from non_dose_targets import invalidate_non_dose_row  # noqa: E402

OUT = ROOT / "data/t19/instances_t19.jsonl"
MANIFEST = ROOT / "data/t19/manifest_t19.json"

MAIN = ROOT / "data/v3/instances_main.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
T14 = ROOT / "data/t14/instances_t14.jsonl"
T17 = ROOT / "data/v3/t17_downdose.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def main_dose_rows() -> list[dict]:
    main_bases = {
        r["base_id"]
        for r in read_jsonl(MAIN)
        if r.get("valid", True) and r.get("type") == "DOSE" and r.get("subset") == "main"
    }
    out: list[dict] = []
    for r in read_jsonl(MAIN):
        if not r.get("valid", True) or r.get("type") != "DOSE" or r.get("subset") != "main":
            continue
        cond = r.get("condition") or ""
        mag = r.get("magnitude") or ""
        keep = False
        if cond == "C0" and mag == "none":
            keep = True
        elif cond == "INV-claim" and mag == "unit_conversion":
            keep = True
        elif cond in ("E1-claim", "E1-evid") and mag in ("x2", "x10"):
            keep = True
        if keep:
            row = dict(r)
            row["t19_pack"] = "main_dose"
            out.append(row)
    for r in read_jsonl(T7):
        if not r.get("valid", True):
            continue
        if r.get("condition") not in ("E1-unit-claim", "E1-unit-evid"):
            continue
        if r["base_id"] not in main_bases:
            continue
        row = dict(r)
        row["t19_pack"] = "main_e1_unit"
        out.append(row)
    return out


def main_pol_rows() -> list[dict]:
    """POL C0 + INV rephrase on main (Rephrase metric for local scale sweep)."""
    out: list[dict] = []
    for r in read_jsonl(MAIN):
        if not r.get("valid", True) or r.get("type") != "POLARITY" or r.get("subset") != "main":
            continue
        cond, mag = r.get("condition"), r.get("magnitude")
        if (cond == "C0" and mag == "none") or (cond == "INV-claim" and mag == "rephrase"):
            row = dict(r)
            row["t19_pack"] = "main_pol"
            out.append(row)
    return out


def main() -> None:
    rows: list[dict] = []
    rows.extend(main_dose_rows())
    rows.extend(main_pol_rows())
    for r in read_jsonl(T14):
        if not r.get("valid", True):
            continue
        row = dict(r)
        row["t19_pack"] = "t14"
        rows.append(row)
    t17_n = 0
    for r in read_jsonl(T17):
        if not r.get("valid", True):
            continue
        row = dict(r)
        row["t19_pack"] = "t17"
        rows.append(row)
        t17_n += 1
    for r in rows:
        invalidate_non_dose_row(r)
    rows = [r for r in rows if r.get("valid", True)]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_pack: dict[str, int] = {}
    by_cond: dict[str, int] = {}
    for r in rows:
        by_pack[r.get("t19_pack", "?")] = by_pack.get(r.get("t19_pack", "?"), 0) + 1
        key = f"{r.get('condition')}:{r.get('magnitude')}"
        by_cond[key] = by_cond.get(key, 0) + 1
    manifest = {
        "path": str(OUT.relative_to(ROOT)),
        "n_instances": len(rows),
        "t17_present": t17_n > 0,
        "t17_n": t17_n,
        "by_pack": by_pack,
        "by_condition": by_cond,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
