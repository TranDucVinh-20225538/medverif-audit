#!/usr/bin/env python3
"""Count valid DOSE unit INV instances under rule-based natural conversion."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    main_path = ROOT / "data" / "v3" / "instances_main.jsonl"
    rows = read_jsonl(main_path)
    unit = [
        r
        for r in rows
        if r.get("valid")
        and r.get("type") == "DOSE"
        and r.get("condition") == "INV-claim"
        and r.get("magnitude") == "unit_conversion"
    ]
    bases = {r["base_id"] for r in unit}
    print(json.dumps({"natural_unit_inv_instances": len(unit), "natural_unit_inv_bases": len(bases)}))


if __name__ == "__main__":
    main()
