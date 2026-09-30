#!/usr/bin/env python3
"""Apply PI review CSVs: main_ext cohort + T17 analysis filters."""

from __future__ import annotations

import csv
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from non_dose_targets import NON_DOSE_TARGET_BASES, invalidate_non_dose_row  # noqa: E402

MAIN_EXT_INST = ROOT / "data/main_ext/instances_main_ext.jsonl"
T17_INST = ROOT / "data/v3/t17_downdose.jsonl"
MAIN_EXT_LABELS = ROOT / "qc/main_ext_labels.csv"
T17_LABELS = ROOT / "qc/t17_labels.csv"
OUT_MANIFEST = ROOT / "notes/pi_review_filter_manifest.json"

EXCLUDE_WHOLE_BASE = frozenset(
    {"MEX0036", "MEX0130", "MEX0161", "MEX0199", "MEX0256", "MEX0391"}
)
EXCLUDE_INV_ONLY = frozenset({"MEX0075", "MEX0159", "MEX0420", "MEX0533"})
PI_REJECT_T17 = frozenset({"D0114", "D0071", "D0116", "D0158"})

BOUNDARY_RE = re.compile(r"(?:≤|>=|≥|<|up to|below|at most|no more than)", re.I)


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_main_ext_labels() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with MAIN_EXT_LABELS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            bid = (row.get("base_id") or "").strip()
            if bid:
                out[bid] = row
    return out


def load_t17_labels() -> dict[str, str]:
    """instance_id -> human_ok (Y/N)."""
    out: dict[str, str] = {}
    with T17_LABELS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            iid = (row.get("instance_id") or "").strip()
            ok = (row.get("human_ok") or "").strip().upper()
            if iid and ok in ("Y", "N"):
                out[iid] = ok
    return out


def _parse_number(span: str) -> tuple[Decimal | None, bool]:
    s = span.strip().replace(",", "")
    m = re.match(r"^([\d.]+)", s)
    if not m:
        return None, False
    try:
        val = Decimal(m.group(1))
    except InvalidOperation:
        return None, False
    return val, "." in m.group(1)


def t17_pack_filter(row: dict) -> str | None:
    """Return invalid_reason if row fails pack-wide T17 rules."""
    diff = row.get("diff") or {}
    side = row.get("edit_side") or "claim"
    block = diff.get(side) or {}
    before = (block.get("span_before") or "").strip()
    after = (block.get("span_after") or "").strip()
    ctx = f"{row.get('claim') or ''} {row.get('evidence') or ''}"
    if BOUNDARY_RE.search(ctx) and row.get("magnitude") in ("down2", "down10"):
        return "t17_boundary_down_edit"
    vb, frac_b = _parse_number(before)
    if vb is not None and vb >= 10 and not frac_b and after:
        va, frac_a = _parse_number(after)
        if va is not None and frac_a:
            return "t17_fractional_down_from_integer"
    return None


def apply_main_ext(rows: list[dict], labels: dict[str, dict]) -> dict:
    stats = {
        "rows_in": len(rows),
        "exclude_whole_base": sorted(EXCLUDE_WHOLE_BASE),
        "exclude_inv_only": sorted(EXCLUDE_INV_ONLY),
        "non_dose_bases": sorted(b for b in NON_DOSE_TARGET_BASES if b.startswith("MEX")),
    }
    natural_y_bases: set[str] = set()
    for bid, lab in labels.items():
        if (lab.get("natural") or "").strip().upper() == "Y":
            natural_y_bases.add(bid)

    removed_whole = inv_only_dropped = pi_natural = non_dose = 0
    for row in rows:
        bid = row.get("base_id") or row.get("id")
        row.setdefault("valid", True)
        if bid in EXCLUDE_WHOLE_BASE:
            row["valid"] = False
            row["invalid_reason"] = "pi_exclude_whole_base"
            removed_whole += 1
            continue
        if bid in NON_DOSE_TARGET_BASES:
            invalidate_non_dose_row(row)
            non_dose += 1
            continue
        cond = row.get("condition") or ""
        if bid in EXCLUDE_INV_ONLY and cond.startswith("INV"):
            row["valid"] = False
            row["invalid_reason"] = "pi_exclude_inv_row"
            inv_only_dropped += 1
            continue
        if cond.startswith("INV") and bid in natural_y_bases:
            row["pi_natural"] = True
            pi_natural += 1
    stats.update(
        {
            "valid_after": sum(1 for r in rows if r.get("valid", True)),
            "dropped_whole_base_rows": removed_whole,
            "dropped_inv_only_rows": inv_only_dropped,
            "non_dose_rows": non_dose,
            "inv_natural_y_rows": pi_natural,
            "natural_y_bases_in_labels": len(natural_y_bases),
        }
    )
    return stats


def apply_t17(rows: list[dict], labels: dict[str, str]) -> dict:
    stats = {"rows_in": len(rows), "pi_reject_ids": [], "pack_filter": 0, "pi_n": 0}
    for row in rows:
        iid = row.get("instance_id") or ""
        bid = row.get("base_id") or ""
        row.setdefault("valid", True)
        if iid in labels and labels[iid] == "N":
            row["valid"] = False
            row["invalid_reason"] = "pi_human_ok_n"
            stats["pi_n"] += 1
            stats["pi_reject_ids"].append(iid)
            continue
        if bid in PI_REJECT_T17 and row.get("condition") == "E1-down2":
            row["valid"] = False
            row["invalid_reason"] = "pi_base_down2_reject"
            stats["pi_n"] += 1
            continue
        reason = t17_pack_filter(row)
        if reason:
            row["valid"] = False
            row["invalid_reason"] = reason
            stats["pack_filter"] += 1
    stats["valid_after"] = sum(1 for r in rows if r.get("valid", True))
    return stats


def main() -> None:
    manifest: dict = {"main_ext": {}, "t17": {}}
    if MAIN_EXT_INST.is_file() and MAIN_EXT_LABELS.is_file():
        mx = read_jsonl(MAIN_EXT_INST)
        manifest["main_ext"] = apply_main_ext(mx, load_main_ext_labels())
        write_jsonl(MAIN_EXT_INST, mx)
    if T17_INST.is_file() and T17_LABELS.is_file():
        t17 = read_jsonl(T17_INST)
        manifest["t17"] = apply_t17(t17, load_t17_labels())
        write_jsonl(T17_INST, t17)
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
