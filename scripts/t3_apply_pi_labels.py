#!/usr/bin/env python3
"""Apply PI_ok labels to T3 INV-family instances; drop numerals/format families."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data" / "v3" / "instances_inv_families.jsonl"
AUDIT = ROOT / "data" / "v3" / "instances_inv_families_audit.jsonl"
OUT_T3 = ROOT / "data" / "t3" / "instances_inv_families.jsonl"
LABELS = ROOT / "qc" / "inv_claim_PI_ok_labels.csv"
MANIFEST = ROOT / "data" / "t3" / "manifest_inv_families.json"

DROPPED_FAMILIES = frozenset({"inv_numerals", "inv_format"})


def load_labels() -> dict[str, str]:
    out: dict[str, str] = {}
    with LABELS.open(newline="") as handle:
        for row in csv.DictReader(handle):
            out[row["instance_id"]] = row["PI_ok"].strip().upper()
    return out


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def apply(rows: list[dict], labels: dict[str, str]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        r = dict(row)
        mag = r.get("magnitude") or ""
        iid = r["instance_id"]
        pi = labels.get(iid)
        r["pi_ok"] = pi
        if mag in DROPPED_FAMILIES:
            r["valid"] = False
            r["invalid_reason"] = "family_dropped"
        elif pi == "Y":
            r["valid"] = True
            r["invalid_reason"] = None
        elif pi == "N":
            r["valid"] = False
            r["invalid_reason"] = "pi_review_n"
        else:
            r["valid"] = False
            r["invalid_reason"] = "pi_not_reviewed"
        out.append(r)
    return out


def main() -> None:
    if not LABELS.is_file():
        raise SystemExit(f"missing {LABELS}")
    labels = load_labels()
    rows = read_jsonl(INST) if INST.is_file() else []
    if not rows:
        raise SystemExit(f"empty or missing {INST}; run t3_build_instances.py first")
    updated = apply(rows, labels)
    write_jsonl(AUDIT, updated)
    write_jsonl(INST, updated)
    write_jsonl(OUT_T3, updated)
    valid = [r for r in updated if r.get("valid")]
    by_mag = Counter(r["magnitude"] for r in updated)
    by_valid_mag = Counter(r["magnitude"] for r in valid)
    meta = {
        "path_v3": str(INST.relative_to(ROOT)),
        "audit_path": str(AUDIT.relative_to(ROOT)),
        "n_instances_total": len(updated),
        "n_scoring_valid": len(valid),
        "by_family_all": dict(by_mag),
        "by_family_valid": dict(by_valid_mag),
        "pi_labels_file": str(LABELS.relative_to(ROOT)),
        "dropped_families": sorted(DROPPED_FAMILIES),
        "ready_for_scoring": len(valid) > 0,
    }
    MANIFEST.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
