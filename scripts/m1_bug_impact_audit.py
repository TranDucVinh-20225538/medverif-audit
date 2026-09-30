#!/usr/bin/env python3
"""Audit impact of missing parse_decimal in m1_canonical_mg_for_surface (dd98330..fix)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import read_jsonl  # noqa: E402
from m1_lib import edited_span_surfaces  # noqa: E402
from review_filters import analysis_keep_row, flip_pi_ok_bases, inv_pi_ok_keys  # noqa: E402
from text_utils import DOSE_RE  # noqa: E402

OUT = ROOT / "notes/m1_bug_audit.json"


def load_rows(path: Path, pred=None) -> list[dict]:
    flip = flip_pi_ok_bases()
    inv = inv_pi_ok_keys()
    out = []
    for r in read_jsonl(path):
        if not r.get("valid", True):
            continue
        if not analysis_keep_row(r, flip_y=flip, inv_keys=inv):
            continue
        if pred and not pred(r):
            continue
        out.append(r)
    return out


def count_buggy_m1_fail_spans(rows: list[dict]) -> dict:
    """Spans where DOSE_RE matches (would enter m1 path) — all failed m1_ok with NameError bug."""
    dose_spans = 0
    seen: set[str] = set()
    for row in rows:
        for surf in edited_span_surfaces(row):
            s = surf.strip().replace("«", "").replace("»", "").strip()
            if not s or s in seen:
                continue
            seen.add(s)
            if DOSE_RE.search(s):
                dose_spans += 1
    return {"edited_target_spans_dose_regex": dose_spans}


def main() -> None:
    packs = {
        "us_up_x1000": load_rows(
            ROOT / "data/t7/instances_e1_unit.jsonl", lambda r: r.get("magnitude") == "x1000"
        ),
        "ns_x10_claim": load_rows(
            ROOT / "data/v3/instances_main.jsonl",
            lambda r: r.get("condition") == "E1-claim" and r.get("magnitude") == "x10",
        ),
        "ns_x10_evid": load_rows(
            ROOT / "data/v3/instances_main.jsonl",
            lambda r: r.get("condition") == "E1-evid" and r.get("magnitude") == "x10",
        ),
        "ns_div10": load_rows(
            ROOT / "data/v3/t17_downdose.jsonl", lambda r: r.get("condition") == "E1-down10"
        ),
    }
    by_pack = {k: count_buggy_m1_fail_spans(v) for k, v in packs.items()}
    total = sum(x["edited_target_spans_dose_regex"] for x in by_pack.values())
    payload = {
        "bug": "m1_canonical_mg_for_surface missing parse_decimal import (NameError swallowed)",
        "introduced": "dd98330",
        "fixed_before_non_na_m1_strong": True,
        "shared_m1_normalizer_unaffected": "src/quantity_norm.py imports parse_decimal from text_utils",
        "affected_code_path": "M1-strong gate only (m1_lib.m1_canonical_mg_for_surface → m1_gate)",
        "not_affected": [
            "results/raw_m1/* (apply_m1_pair / normalize_quantities)",
            "results/raw/lane_b/m1_t7_e1_unit/*",
            "Verifier score jsonl (M1 text rewrite at score time)",
        ],
        "artifact_superseded_if_generated_under_bug": [
            "results/tables/m1_strong.md",
            "notes/m1_strong_report.md",
            "notes/m1_strong_report.json",
            "results/cache/m1_strong_gate.json (partial runs)",
        ],
        "spans_false_m1_fail_under_bug_by_pack": by_pack,
        "total_dose_regex_edited_spans_affected": total,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
