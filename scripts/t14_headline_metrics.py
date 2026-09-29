#!/usr/bin/env python3
"""Headline metrics: QI (INV natural PASS), US (1−P(PASS|×1000)), T13 pair (1)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from verifier_labels import CANONICAL_VERIFIERS, verifier_display_name  # noqa: E402

import t14_t3_filter_report as filt  # noqa: E402


def pair1_metrics() -> dict[str, float | None]:
    t13_json = ROOT / "notes/t13_pairwise_preference.json"
    if not t13_json.is_file():
        subprocess.run([sys.executable, str(ROOT / "scripts/t13_best_of_n_report.py")], cwd=ROOT, check=False)
    data = json.loads(t13_json.read_text()) if t13_json.is_file() else {}
    out: dict[str, float | None] = {}
    for slug in CANONICAL_VERIFIERS:
        p = ((data.get("by_verifier") or {}).get(slug) or {}).get("pairs") or {}
        cell = p.get("x1000_vs_inv") or {}
        out[slug] = cell.get("p_wrong_prefers")
    return out


def filter_metrics() -> dict[str, dict]:
    x1k = filt.x1000_claim_ids()
    inv = filt.inv_natural_ids()
    pair1 = pair1_metrics()
    out: dict[str, dict] = {}
    for slug in CANONICAL_VERIFIERS:
        scores = filt.merged_score_rows(slug)
        keep_x1k: list[int] = []
        inv_pass: list[int] = []
        for iid in x1k:
            row = scores.get(iid)
            if not row:
                continue
            p = filt.is_pass(slug, row)
            if p is None:
                continue
            keep_x1k.append(int(p))
        for iid in inv:
            row = scores.get(iid)
            if not row:
                continue
            p = filt.is_pass(slug, row)
            if p is None:
                continue
            inv_pass.append(int(p))
        keep_r = sum(keep_x1k) / len(keep_x1k) if keep_x1k else None
        qi = sum(inv_pass) / len(inv_pass) if inv_pass else None
        us = (1.0 - keep_r) if keep_r is not None else None
        out[slug] = {
            "QI_inv_natural_pass": qi,
            "US_e1_unit_x1000": us,
            "keep_x1000": keep_r,
            "n_x1000": len(keep_x1k),
            "n_inv": len(inv_pass),
            "t13_pair1_p_wrong_ge": pair1.get(slug),
        }
    return out


def cohort_snapshot() -> dict:
    t13_json = ROOT / "notes/t13_pairwise_preference.json"
    if t13_json.is_file():
        data = json.loads(t13_json.read_text())
        return {
            "main_dose_bases": data.get("cohort", {}).get("valid_main_dose_bases"),
            "structural_pairs": data.get("cohort", {}).get("structural_pairs_eligible", {}),
        }
    return {}


def compare(before: dict[str, dict], after: dict[str, dict]) -> list[dict]:
    flags: list[dict] = []
    for slug in CANONICAL_VERIFIERS:
        b, a = before.get(slug, {}), after.get(slug, {})
        for key in ("QI_inv_natural_pass", "US_e1_unit_x1000", "t13_pair1_p_wrong_ge"):
            bv, av = b.get(key), a.get(key)
            if bv is None or av is None or bv != bv or av != av:
                continue
            delta = av - bv
            if abs(delta) > 0.01:
                flags.append(
                    {
                        "verifier": slug,
                        "display": verifier_display_name(slug),
                        "metric": key,
                        "before": bv,
                        "after": av,
                        "delta": delta,
                    }
                )
    return flags


if __name__ == "__main__":
    print(json.dumps({"cohort": cohort_snapshot(), "by_verifier": filter_metrics()}, indent=2))
