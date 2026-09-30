"""Apply qc/t14_PI_ok_labels.csv to T14 instances."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PI_CSV = ROOT / "qc" / "t14_PI_ok_labels.csv"

_SINGULAR_OK = {
    "D0066": re.compile(r"\b1\s+milligram\b", re.I),
    "D0063": re.compile(r"\b1\s+gram\b", re.I),
}


def load_pi_labels() -> dict[str, str]:
    if not PI_CSV.is_file():
        return {}
    with PI_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (r.get("instance_id") or "").strip(): (r.get("PI_ok") or "").strip().upper()
            for r in csv.DictReader(handle)
            if (r.get("instance_id") or "").strip()
        }


def _has_ug_token(text: str) -> bool:
    return bool(re.search(r"\bug\b", text or "", re.I))


def pi_allows(row: dict, labels: dict[str, str] | None = None) -> bool:
    labels = labels if labels is not None else load_pi_labels()
    iid = row.get("instance_id") or ""
    bid = row.get("base_id") or ""
    claim = row.get("claim") or ""
    if bid in _SINGULAR_OK and _SINGULAR_OK[bid].search(claim):
        return True
    pi = labels.get(iid)
    if pi == "N":
        if row.get("magnitude") == "symbol_micro" and not _has_ug_token(claim):
            return True
        return False
    if pi == "Y":
        return True
    return True


def apply_pi_validity(rows: list[dict]) -> tuple[list[dict], dict]:
    labels = load_pi_labels()
    kept: list[dict] = []
    stats = {"excluded_pi_n": 0, "excluded_ids": []}
    for row in rows:
        r = dict(row)
        if not pi_allows(r, labels):
            r["valid"] = False
            r["invalid_reason"] = "t14_pi_n"
            stats["excluded_pi_n"] += 1
            stats["excluded_ids"].append(r["instance_id"])
        kept.append(r)
    return kept, stats
