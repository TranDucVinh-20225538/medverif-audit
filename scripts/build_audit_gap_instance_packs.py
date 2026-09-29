#!/usr/bin/env python3
"""Write JSONL subsets for audit-gap rescoring."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _parsed, read_jsonl  # noqa: E402
from non_dose_targets import invalidate_non_dose_row  # noqa: E402
from review_filters import analysis_keep_row  # noqa: E402

INV11 = {
    "D0001__INV-claim__unit_conversion",
    "D0009__INV-claim__unit_conversion",
    "D0018__INV-claim__unit_conversion",
    "D0031__INV-claim__unit_conversion",
    "D0042__INV-claim__unit_conversion",
    "D0044__INV-claim__unit_conversion",
    "D0053__INV-claim__unit_conversion",
    "D0061__INV-claim__unit_conversion",
    "D0124__INV-claim__unit_conversion",
    "D0141__INV-claim__unit_conversion",
    "D0176__INV-claim__unit_conversion",
}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    main_rows = []
    inv11 = []
    for row in read_jsonl(ROOT / "data/v3/instances_main.jsonl"):
        row = dict(row)
        invalidate_non_dose_row(row)
        if not row.get("valid", True) or not analysis_keep_row(row):
            continue
        if row.get("subset") != "main":
            continue
        main_rows.append(row)
        if row["instance_id"] in INV11 and row.get("valid", True):
            inv11.append(row)

    write_jsonl(ROOT / "data/v3/instances_main_inv11_m1_gap.jsonl", inv11)

    v4_path = ROOT / "results/raw/v4_ragas_nli.llama.jsonl"
    id_list = ROOT / "notes/v4_unparsed_instance_ids.txt"
    unparsed_ids: list[str] = []
    if id_list.is_file() and id_list.read_text().strip():
        unparsed_ids = sorted(set(id_list.read_text().split()))
    else:
        for line in v4_path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            fake = {
                "verdict": row.get("verdict"),
                "score": row.get("score"),
                "raw_output": row.get("raw_output"),
            }
            if not _parsed(fake):
                unparsed_ids.append(row["instance_id"])
        unparsed_ids = sorted(set(unparsed_ids))
    by_id = {r["instance_id"]: r for r in main_rows}
    unparsed_rows = [by_id[i] for i in unparsed_ids if i in by_id]
    write_jsonl(ROOT / "data/v3/v4_llama_unparsed_rescore.jsonl", unparsed_rows)

    print(
        json.dumps(
            {
                "inv11": len(inv11),
                "v4_unparsed": len(unparsed_rows),
                "paths": [
                    "data/v3/instances_main_inv11_m1_gap.jsonl",
                    "data/v3/v4_llama_unparsed_rescore.jsonl",
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
