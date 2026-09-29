#!/usr/bin/env python3
"""Apply NON_DOSE_TARGET_BASES across packs; headline before/after."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from non_dose_targets import NON_DOSE_TARGET_BASES, invalidate_non_dose_row  # noqa: E402


def reconcile_non_dose_row(row: dict) -> dict:
    """Apply current NON_DOSE set; clear stale non_dose_target invalidations."""
    bid = row.get("base_id") or row.get("id")
    if bid in NON_DOSE_TARGET_BASES:
        return invalidate_non_dose_row(row)
    if row.get("invalid_reason") == "non_dose_target":
        row["valid"] = True
        row.pop("invalid_reason", None)
    return row

import t14_headline_metrics as hm  # noqa: E402

V3 = ROOT / "data/v3"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
T14 = ROOT / "data/t14/instances_t14.jsonl"
T17 = V3 / "t17_downdose.jsonl"
OUT = ROOT / "notes/non_dose_pack_apply.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def invalidate_pack(path: Path, label: str) -> dict:
    rows = read_jsonl(path)
    if not rows:
        return {"pack": label, "path": str(path.relative_to(ROOT)), "missing": True}
    before_valid = sum(1 for r in rows if r.get("valid", True))
    touched_bases: set[str] = set()
    for r in rows:
        bid = r.get("base_id") or r.get("id")
        if bid in NON_DOSE_TARGET_BASES:
            touched_bases.add(bid)
            reconcile_non_dose_row(r)
    write_jsonl(path, rows)
    after_valid = sum(1 for r in rows if r.get("valid", True))
    return {
        "pack": label,
        "path": str(path.relative_to(ROOT)),
        "rows": len(rows),
        "non_dose_bases_hit": sorted(touched_bases),
        "valid_before": before_valid,
        "valid_after": after_valid,
        "removed_valid": before_valid - after_valid,
    }


def refresh_main_from_audit() -> None:
    audit = read_jsonl(V3 / "instances_audit.jsonl")
    for r in audit:
        reconcile_non_dose_row(r)
    write_jsonl(V3 / "instances_audit.jsonl", audit)
    main_rows = [r for r in audit if r.get("valid") and r.get("subset") == "main"]
    write_jsonl(V3 / "instances_main.jsonl", main_rows)
    cpu_main = [r for r in main_rows if r.get("magnitude") != "paraphrase"]
    write_jsonl(V3 / "instances_cpu_main.jsonl", cpu_main)


def t13_derived_note() -> str:
    return "T13 cohort is derived from valid main DOSE + T7 ×1000 (no separate jsonl pack)."


def main() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/t13_best_of_n_report.py")], cwd=ROOT, check=False)
    before_metrics = hm.filter_metrics()
    before_cohort = hm.cohort_snapshot()

    refresh_main_from_audit()
    packs = [
        (V3 / "instances_main.jsonl", "main_DOSE"),
        (T7, "T7_e1_unit"),
        (T14, "T14_repr_pre_rebuild"),
        (T17, "T17_downdose"),
    ]
    pack_stats = [invalidate_pack(p, label) for p, label in packs]

    subprocess.run([sys.executable, str(ROOT / "scripts/t13_best_of_n_report.py")], cwd=ROOT, check=False)
    after_metrics = hm.filter_metrics()
    after_cohort = hm.cohort_snapshot()
    flags = hm.compare(before_metrics, after_metrics)

    report = {
        "non_dose_target_bases": sorted(NON_DOSE_TARGET_BASES),
        "newly_listed": ["D0077", "D0164"],
        "packs": pack_stats,
        "t13_note": t13_derived_note(),
        "cohort_before": before_cohort,
        "cohort_after": after_cohort,
        "headlines_before": before_metrics,
        "headlines_after": after_metrics,
        "headline_flags_delta_gt_1pt": flags,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
