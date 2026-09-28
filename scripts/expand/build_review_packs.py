#!/usr/bin/env python3
"""QC review CSVs for the expanded set (empty PI_ok column)."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import flip_mechanism, inv_cue, natural_unit_conversion_label  # noqa: E402


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, default=ROOT / "data" / "expand" / "instances_main.jsonl")
    parser.add_argument("--bases", type=Path, default=ROOT / "data" / "expand" / "bases_main.jsonl")
    parser.add_argument("--qc-dir", type=Path, default=ROOT / "qc")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    args.qc_dir.mkdir(parents=True, exist_ok=True)

    inst = read_jsonl(args.instances)
    bases = {r["id"]: r for r in read_jsonl(args.bases)}

    pol_flips = []
    for row in inst:
        if row.get("type") != "POLARITY" or row.get("magnitude") != "flip":
            continue
        base = bases.get(row["base_id"], {})
        span = row.get("claim_span") or base.get("target_span_claim") or ""
        inv_span = ""
        inv_claim = ""
        try:
            inv_span = inv_cue(span)
            inv_claim = (row.get("claim_c0") or row.get("claim") or "").replace(span, inv_span, 1)
        except ValueError:
            pass
        pol_flips.append(
            {
                "base_id": row["base_id"],
                "flip_mechanism": row.get("flip_mechanism") or flip_mechanism(span),
                "condition": row.get("condition"),
                "original_span": span,
                "flipped_span": row.get("claim_span") if row.get("condition") == "E1-claim" else "",
                "inv_template_span": inv_span,
                "inv_template_claim": inv_claim,
                "PI_ok": "",
            }
        )
    with (args.qc_dir / "expand_pol_flips.csv").open("w", newline="", encoding="utf-8") as handle:
        if pol_flips:
            writer = csv.DictWriter(handle, fieldnames=list(pol_flips[0].keys()))
            writer.writeheader()
            writer.writerows(pol_flips)

    dose_bases = sorted({r["base_id"] for r in inst if r.get("type") == "DOSE" and r.get("condition") == "C0"})
    rng = random.Random(args.seed)
    sample_n = max(1, (len(dose_bases) + 3) // 4) if dose_bases else 0
    sample_ids = set(rng.sample(dose_bases, min(sample_n, len(dose_bases))))
    dose_rows = []
    by_id = {(r["base_id"], r.get("condition")): r for r in inst}
    for bid in sorted(sample_ids):
        c0 = by_id.get((bid, "C0"), {})
        e1 = by_id.get((bid, "E1-claim"), by_id.get((bid, "E1-evid"), {}))
        dose_rows.append(
            {
                "base_id": bid,
                "claim_c0": c0.get("claim", ""),
                "evidence_c0": c0.get("evidence", ""),
                "e1_condition": e1.get("condition", ""),
                "e1_claim": e1.get("claim", ""),
                "e1_evidence": e1.get("evidence", ""),
                "PI_ok": "",
            }
        )
    with (args.qc_dir / "expand_dose_sample.csv").open("w", newline="", encoding="utf-8") as handle:
        if dose_rows:
            writer = csv.DictWriter(handle, fieldnames=list(dose_rows[0].keys()))
            writer.writeheader()
            writer.writerows(dose_rows)

    unit_rows = []
    for row in inst:
        if row.get("condition") != "INV-claim" or row.get("magnitude") != "unit_conversion":
            continue
        span = row.get("claim_span") or ""
        label = natural_unit_conversion_label(span) or ""
        unit_rows.append(
            {
                "base_id": row["base_id"],
                "original_span": bases.get(row["base_id"], {}).get("target_span_claim", span),
                "converted_span": span,
                "natural_rule": label,
                "suggested_natural": "Y" if label else "",
                "PI_ok": "",
            }
        )
    with (args.qc_dir / "expand_unit_natural.csv").open("w", newline="", encoding="utf-8") as handle:
        if unit_rows:
            writer = csv.DictWriter(handle, fieldnames=list(unit_rows[0].keys()))
            writer.writeheader()
            writer.writerows(unit_rows)

    print(
        json.dumps(
            {
                "expand_pol_flips": len(pol_flips),
                "expand_dose_sample": len(dose_rows),
                "expand_unit_natural": len(unit_rows),
            }
        )
    )


if __name__ == "__main__":
    main()
