#!/usr/bin/env python3
"""Build T2 pilot (100 stratified DOSE) or full-scope pending JSONL."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from review_filters import (  # noqa: E402
    effective_unit_natural_y,
    flip_pi_ok_bases,
    inv_pi_ok_keys,
    inv_mechanism,
    unit_natural_labels,
)
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

MAIN = ROOT / "data" / "v3" / "instances_main.jsonl"
EXPAND = ROOT / "data" / "expand" / "instances_cpu_early.jsonl"
OUT_DIR = ROOT / "data" / "t2"
PILOT_SEED = 2026


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def inv_span_before(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    return str(claim.get("span_before") or row.get("claim_span") or "")


def build_pilot(rows: list[dict]) -> tuple[list[dict], dict]:
    dose = [r for r in rows if r.get("valid") and r.get("type") == "DOSE" and r.get("subset") == "main"]
    by_key: dict[tuple, list[dict]] = {}
    for r in dose:
        by_key.setdefault((r["condition"], r.get("magnitude")), []).append(r)

    c0 = by_key.get(("C0", "none"), [])
    e1x2 = [r for r in by_key.get(("E1-claim", "x2"), [])]
    inv = by_key.get(("INV-claim", "unit_conversion"), [])

    rng = random.Random(PILOT_SEED)
    # Bases with full trio preferred
    c0_by_base = {r["base_id"]: r for r in c0}
    e1_by_base = {r["base_id"]: r for r in e1x2}
    inv_by_base = {r["base_id"]: r for r in inv}
    shared = sorted(set(c0_by_base) & set(e1_by_base))
    rng.shuffle(shared)
    pick_bases = shared[:30]
    if len(pick_bases) < 30:
        extra = [b for b in c0_by_base if b not in pick_bases]
        rng.shuffle(extra)
        pick_bases.extend(extra[: 30 - len(pick_bases)])

    selected: list[dict] = []
    selected.extend(c0_by_base[b] for b in pick_bases[:30] if b in c0_by_base)
    selected.extend(e1_by_base[b] for b in pick_bases[:30] if b in e1_by_base)

    # INV: prefer natural mix, 40 rows
    inv_nat = []
    inv_other = []
    labels = unit_natural_labels()
    for r in inv:
        orig = inv_span_before(r)
        rule_y = bool(rule_natural_unit_conversion_label(orig))
        if effective_unit_natural_y(r["base_id"], rule_y):
            inv_nat.append(r)
        else:
            inv_other.append(r)
    rng.shuffle(inv_nat)
    rng.shuffle(inv_other)
    inv_pick = inv_nat[:25] + inv_other[:15]
    if len(inv_pick) < 40:
        seen = {r["instance_id"] for r in inv_pick}
        for r in inv_nat + inv_other:
            if len(inv_pick) >= 40:
                break
            if r["instance_id"] not in seen:
                inv_pick.append(r)
                seen.add(r["instance_id"])
    selected.extend(inv_pick[:40])

    # Dedupe by instance_id
    seen_ids: set[str] = set()
    final = []
    for r in selected:
        if r["instance_id"] in seen_ids:
            continue
        seen_ids.add(r["instance_id"])
        final.append(r)

    meta = {
        "mode": "pilot",
        "seed": PILOT_SEED,
        "n_instances": len(final),
        "n_bases_shared": len(pick_bases),
        "strata": {
            "C0": sum(1 for r in final if r["condition"] == "C0"),
            "E1-claim_x2": sum(1 for r in final if r["condition"] == "E1-claim" and r.get("magnitude") == "x2"),
            "INV-unit": sum(1 for r in final if r["condition"] == "INV-claim" and r.get("magnitude") == "unit_conversion"),
        },
        "inv_natural_in_pilot": sum(
            1
            for r in final
            if r["condition"] == "INV-claim"
            and effective_unit_natural_y(
                r["base_id"], bool(rule_natural_unit_conversion_label(inv_span_before(r)))
            )
        ),
    }
    return final, meta


def t2_full_eligible(row: dict, *, expand: bool) -> bool:
    if not row.get("valid", True):
        return False
    if row.get("subset") != "main":
        if not (expand and str(row.get("base_id", "")).startswith(("E", "X", "EXP"))):
            return False
    cond = row.get("condition")
    if cond in ("E1-evid", "E2"):
        return False
    typ = row.get("type")
    mag = row.get("magnitude")
    if typ == "DOSE":
        if cond == "C0":
            return True
        if cond == "E1-claim" and mag in ("x2", "x10"):
            return True
        if cond == "INV-claim" and mag == "unit_conversion":
            return True
        if cond == "INV-claim" and mag and mag.startswith("inv_"):
            return True
        return False
    if typ == "POLARITY":
        flip_y = flip_pi_ok_bases()
        inv_keys = inv_pi_ok_keys()
        if cond == "C0":
            return True
        if cond == "E1-claim":
            return row["base_id"] in flip_y
        if cond == "INV-claim":
            mech = inv_mechanism(row)
            if mech == "unit":
                return True
            return (row["base_id"], typ, mech) in inv_keys
    return False


def build_full(main_rows: list[dict], expand_rows: list[dict]) -> tuple[list[dict], dict]:
    main_elig = [r for r in main_rows if t2_full_eligible(r, expand=False)]
    expand_elig = [r for r in expand_rows if t2_full_eligible(r, expand=True)]
    combined = main_elig + expand_elig
    approve = ROOT / "notes" / "t2_full_approved"
    approved = approve.is_file()
    meta = {
        "mode": "full_pending",
        "approved": approved,
        "note": (
            "Scoring allowed (PI OK)."
            if approved
            else "Do not score until notes/t2_full_approved exists (PI OK)."
        ),
        "n_instances": len(combined),
        "n_main": len(main_elig),
        "n_expand": len(expand_elig),
    }
    return combined, meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("pilot", "full"), required=True)
    args = parser.parse_args()
    main_rows = read_jsonl(MAIN)
    if args.mode == "pilot":
        rows, meta = build_pilot(main_rows)
        out = OUT_DIR / "instances_pilot_100.jsonl"
    else:
        rows, meta = build_full(main_rows, read_jsonl(EXPAND))
        out = OUT_DIR / "instances_full_pending.jsonl"
    write_jsonl(out, rows)
    meta["path"] = str(out.relative_to(ROOT))
    (OUT_DIR / f"manifest_{args.mode}.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
