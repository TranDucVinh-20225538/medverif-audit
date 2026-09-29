#!/usr/bin/env python3
"""Export QVC bundled JSONL from medverif-audit instances + QC gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from analyze import read_jsonl  # noqa: E402

OUT = ROOT / "qvc/data/bundled"
OUT.mkdir(parents=True, exist_ok=True)


def export(rows: list[dict], name: str, filt) -> None:
    out = []
    for r in rows:
        if not r.get("valid", True):
            continue
        if not filt(r):
            continue
        out.append(
            {
                "id": r["instance_id"],
                "base_id": r["base_id"],
                "claim": r.get("claim", ""),
                "evidence": r.get("evidence", ""),
                "condition": r.get("condition"),
                "expected_verdict": r.get("expected_verdict"),
                "provenance": r.get("source") or "medverif-main",
                "family": r.get("magnitude") or r.get("type"),
            }
        )
    (OUT / name).write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n")
    print(name, len(out))


def main() -> None:
    main_rows = read_jsonl(ROOT / "data/v3/instances_cpu_early.jsonl")
    export(
        main_rows,
        "inv_unit.jsonl",
        lambda r: r.get("condition") == "INV-claim" and r.get("magnitude") == "unit_conversion",
    )
    export(main_rows, "e1_x2.jsonl", lambda r: r.get("condition") == "E1-claim" and r.get("magnitude") == "x2")
    export(main_rows, "e1_x10.jsonl", lambda r: r.get("condition") == "E1-claim" and r.get("magnitude") == "x10")
    t7 = read_jsonl(ROOT / "data/t7/instances_e1_unit.jsonl")
    export(t7, "e1_unit_t7.jsonl", lambda r: r.get("valid", True))
    print("bundled ->", OUT)


if __name__ == "__main__":
    main()
