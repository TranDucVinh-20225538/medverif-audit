#!/usr/bin/env python3
"""Rule-classify ecological answer vs evidence target dose."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t4_eco_compare import (  # noqa: E402
    apply_pi_override,
    classify_answer,
    default_pi_label_paths,
    load_pi_label_paths,
)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="inp", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--pi-labels",
        type=Path,
        action="append",
        default=None,
        help="Repeatable; default: qc/eco_PI_ok_labels.csv + qc/eco_review2.csv (labeled rows only)",
    )
    args = parser.parse_args()

    if args.pi_labels:
        label_paths = args.pi_labels
    else:
        label_paths = default_pi_label_paths(ROOT)
    labels = load_pi_label_paths(label_paths)
    rows = []
    for line in args.inp.open():
        if not line.strip():
            continue
        row = json.loads(line)
        cat = classify_answer(
            row.get("answer") or "",
            row.get("evidence") or "",
            row.get("target_span_evidence") or row.get("evidence_span") or "",
        )
        row["eco_category"] = cat
        row["eco_category_final"] = apply_pi_override(
            row["task_id"],
            row["answerer_id"],
            cat,
            labels,
        )
        rows.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    dist = Counter(r["eco_category_final"] for r in rows)
    dist_raw = Counter(r["eco_category"] for r in rows)
    print(
        json.dumps(
            {
                "n": len(rows),
                "eco_category_final": dict(dist),
                "eco_category_classifier": dict(dist_raw),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
