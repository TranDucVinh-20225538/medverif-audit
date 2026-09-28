#!/usr/bin/env python3
"""Build T3 INV-family instance set (frequency / route / numerals / format)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "data" / "v3" / "instances_main.jsonl"
OUT = ROOT / "data" / "t3" / "instances_inv_families.jsonl"
MANIFEST = ROOT / "data" / "t3" / "manifest_inv_families.json"

# Canonical magnitude ids (DOSE INV-claim); aliases map legacy names.
FAMILIES = {
    "inv_frequency": ("inv_frequency", "frequency"),
    "inv_route": ("inv_route", "route"),
    "inv_numerals": ("inv_numerals", "numerals"),
    "inv_format": ("inv_format", "format"),
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    selected: list[dict] = []
    counts: dict[str, int] = {k: 0 for k in FAMILIES}
    for row in read_jsonl(MAIN):
        if not row.get("valid", True):
            continue
        if row.get("type") != "DOSE" or row.get("condition") != "INV-claim":
            continue
        mag = str(row.get("magnitude") or "")
        for label, aliases in FAMILIES.items():
            if mag in aliases:
                selected.append(row)
                counts[label] += 1
                break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "path": str(OUT.relative_to(ROOT)),
        "n_instances": len(selected),
        "by_family": counts,
        "ready_for_scoring": len(selected) > 0,
    }
    MANIFEST.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
