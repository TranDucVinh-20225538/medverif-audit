#!/usr/bin/env python3
"""Every changed m1_strong_final cell, split into (1) DeBERTa → cpuverif and (2) amendment 5.

Usage: m1_strong_amend5_changes.py ORIGINAL_MD DEBERTA_ONLY_MD
ORIGINAL_MD = results/tables/m1_strong_final.md as accepted (8939e6c); DEBERTA_ONLY_MD = --final rerun
after the DeBERTa swap without --amend5. Amendment-5 table: results/tables/m1_strong_final_amend5.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from table_change_list import tables  # noqa: E402

OUT = ROOT / "notes/m1_strong_amend5_changes.md"
AMEND5 = ROOT / "results/tables/m1_strong_final_amend5.md"
BIND = "Bind? (criterion uses AFTER values only)"


def cell_changes(old: dict, new: dict) -> list[str]:
    rows = []
    for key in sorted(old.keys() & new.keys(), key=str):
        if key[0] == BIND or old[key] == new[key]:
            continue
        for col, val in new[key].items():
            if old[key].get(col) != val:
                rows.append(f"| {key[0].split(' vs ')[0]} | {key[1]} | {key[2]} | {col} | {old[key].get(col)} | {val} |")
    return rows


def bind_rows(t: dict) -> dict[str, dict[str, str]]:
    return {v["Model"]: v for k, v in t.items() if k[0] == BIND}


def main() -> None:
    orig, deb, a5 = (tables(Path(p)) for p in (sys.argv[1], sys.argv[2], AMEND5))
    head = ["| Block | Model | Side | Column | Old | New |", "| --- | --- | --- | --- | --- | --- |"]
    lines = [
        "# m1_strong_final: every changed cell (old → new)",
        "",
        "Original = accepted `m1_strong_final` (`8939e6c`). Corrected table: `results/tables/m1_strong_final_amend5.md` "
        "(`scripts/m1_strong_run.py --final --amend5`). Script: `scripts/m1_strong_amend5_changes.py`.",
        "",
        "## Overall binding verdict (criterion on AFTER values)",
        "",
        "| Model | CLAIM old → new | EVID old → new | Overall old → new |",
        "| --- | --- | --- | --- |",
    ]
    ob, nb = bind_rows(orig), bind_rows(a5)
    cols = [c for c in next(iter(nb.values())) if c != "Model"]
    for model, n in nb.items():
        o = ob.get(model, {})
        lines.append(f"| {model} | " + " | ".join(f"{o.get(c, '—')} → {n[c]}" for c in cols) + " |")
    lines += ["", "## 1. MiniCheck-DeBERTa scores → cpuverif (reference env)", "", *head, *cell_changes(orig, deb), ""]
    lines += ["## 2. Amendment 5 (84 off-spec after-M1 rows rescored with spec M1 text)", "", *head, *cell_changes(deb, a5), ""]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
