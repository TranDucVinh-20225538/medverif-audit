#!/usr/bin/env python3
"""Random main-set DOSE audit sheet (seed 20261001, 40 bases)."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data/v3/instances_main.jsonl"
OUT = ROOT / "qc/main_dose_audit.csv"
SEED = 20261001
N = 40


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    inst = read_jsonl(INST)
    dose_bases = sorted(
        {
            r["base_id"]
            for r in inst
            if r.get("type") == "DOSE"
            and r.get("valid", True)
            and r.get("subset") == "main"
            and r.get("condition") == "C0"
        }
    )
    rng = random.Random(SEED)
    pick = rng.sample(dose_bases, min(N, len(dose_bases)))
    c0 = {r["base_id"]: r for r in inst if r.get("condition") == "C0" and r.get("type") == "DOSE"}
    e1: dict[str, dict[str, dict]] = {}
    for r in inst:
        if r.get("type") != "DOSE" or r.get("condition") != "E1-claim":
            continue
        e1.setdefault(r["base_id"], {})[r.get("magnitude") or ""] = r
    rows = []
    for bid in sorted(pick):
        c = c0.get(bid, {})
        x2 = (e1.get(bid) or {}).get("x2", {})
        x10 = (e1.get(bid) or {}).get("x10", {})
        rows.append(
            {
                "base_id": bid,
                "claim_c0": c.get("claim", ""),
                "evidence_c0": c.get("evidence", ""),
                "e1_x2_claim": x2.get("claim", ""),
                "e1_x10_claim": x10.get("claim", ""),
                "PI_ok": "",
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"seed": SEED, "n_bases": len(rows), "path": str(OUT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
