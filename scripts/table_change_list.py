#!/usr/bin/env python3
"""List every changed Markdown-table cell between a snapshot directory and the repo (old → new).

Usage: table_change_list.py SNAPSHOT_ROOT OUT_MD [--only a.md,b.md] [--title TEXT]
SNAPSHOT_ROOT mirrors the repo layout (e.g. /tmp/pre_swap/tables ↔ results/tables).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = (("tables", ROOT / "results/tables"), ("notes", ROOT / "notes"))


def tables(path: Path) -> dict[tuple, dict[str, str]]:
    out: dict[tuple, dict[str, str]] = {}
    header: list[str] | None = None
    section = ""
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            section = line.lstrip("#").strip()
            header = None
            continue
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        key = (section, *cells[:2])
        out[key] = dict(zip(header, cells))
    return out


def main() -> None:
    snap, out_md = Path(sys.argv[1]), Path(sys.argv[2])
    only = set()
    title = "Changed table cells"
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    lines = [f"# {title}", "", f"Snapshot: `{snap}` vs working tree. Script: `scripts/table_change_list.py`.", ""]
    n_changes = 0
    for sub, live in PAIRS:
        for old_path in sorted((snap / sub).glob("*.md")):
            if only and old_path.name not in only:
                continue
            new_path = live / old_path.name
            if not new_path.is_file():
                continue
            old, new = tables(old_path), tables(new_path)
            rows = []
            for key in old.keys() | new.keys():
                o, n = old.get(key), new.get(key)
                if o == n:
                    continue
                if o is None or n is None:
                    rows.append(f"| {' / '.join(k for k in key if k)} | (row) | {'—' if o is None else 'present'} | {'—' if n is None else 'present'} |")
                    continue
                for col in n:
                    if o.get(col) != n.get(col):
                        rows.append(f"| {' / '.join(k for k in key if k)} | {col} | {o.get(col)} | {n.get(col)} |")
            if rows:
                n_changes += len(rows)
                rel = f"{'results/tables' if sub == 'tables' else 'notes'}/{new_path.name}"
                lines += [f"## `{rel}`", "", "| Row | Column | Old | New |", "| --- | --- | --- | --- |", *sorted(rows), ""]
    if not n_changes:
        lines.append("No table cell changed.")
    out_md.write_text("\n".join(lines) + "\n")
    print(f"{n_changes} changed cells → {out_md}")


if __name__ == "__main__":
    main()
