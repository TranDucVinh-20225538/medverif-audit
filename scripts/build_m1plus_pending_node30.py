#!/usr/bin/env python3
"""T3 PI_ok=Y freq/route (+ C0/E1 scope) with M1+ normalization for node30 V2/V3."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quantity_norm import apply_m1_plus_pair  # noqa: E402

T3_PATHS = (
    ROOT / "data" / "v3" / "instances_inv_families.jsonl",
    ROOT / "data" / "t3" / "instances_inv_families.jsonl",
)
T1_PATHS = (
    ROOT / "data" / "v3" / "instances_cpu_early.jsonl",
    ROOT / "data" / "v3" / "instances_main.jsonl",
)
LABELS = ROOT / "qc" / "inv_claim_PI_ok_labels.csv"
OUT = ROOT / "data" / "v3" / "instances_m1plus_pending_node30.jsonl"
MANIFEST = ROOT / "notes" / "m1plus_pending_node30_manifest.json"


def content_sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode("utf-8")).hexdigest()


def pi_ok_t3_ids() -> set[str]:
    out: set[str] = set()
    for row in csv.DictReader(LABELS.open()):
        if (row.get("PI_ok") or "").strip().upper() != "Y":
            continue
        if (row.get("family") or "").strip() in ("inv_frequency", "inv_route"):
            out.add(row["instance_id"].strip())
    return out


def t1_scope(row: dict) -> bool:
    if not row.get("valid", True):
        return False
    cond = row.get("condition") or ""
    if cond == "C0":
        return True
    if cond in ("E1-claim", "E1-evid"):
        return True
    if cond == "INV-claim" and row.get("magnitude") == "unit_conversion":
        return True
    return False


def enrich(row: dict) -> dict:
    c, e = apply_m1_plus_pair(row.get("claim") or "", row.get("evidence") or "")
    out = dict(row)
    out["claim"] = c
    out["evidence"] = e
    out["content_sha1"] = content_sha1(c, e)
    out["m1_preapplied"] = True
    out["m1plus"] = True
    return out


def main() -> None:
    allowed = pi_ok_t3_ids()
    rows: list[dict] = []
    seen: set[str] = set()
    by_id: dict[str, dict] = {}
    for t3_path in T3_PATHS:
        if not t3_path.is_file():
            continue
        for line in t3_path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["instance_id"] not in allowed:
                continue
            by_id.setdefault(row["instance_id"], row)
    for iid in sorted(allowed):
        row = by_id.get(iid)
        if not row:
            continue
        if not row.get("valid", True):
            continue
        rows.append(enrich(row))
        seen.add(iid)
    for t1_path in T1_PATHS:
        if not t1_path.is_file():
            continue
        for line in t1_path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            if not t1_scope(row):
                continue
            if row["instance_id"] in seen:
                continue
            rows.append(enrich(row))
            seen.add(row["instance_id"])
    rows.sort(key=lambda r: r["instance_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    MANIFEST.write_text(
        json.dumps(
            {
                "n": len(rows),
                "t3_pi_ok_freq_route": len(allowed),
                "path": str(OUT.relative_to(ROOT)),
                "normalization": "M1 dose/unit + M1+ frequency/route",
            },
            indent=2,
        )
        + "\n"
    )
    print(MANIFEST)


if __name__ == "__main__":
    main()
