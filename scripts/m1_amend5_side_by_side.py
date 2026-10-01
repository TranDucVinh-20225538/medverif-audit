#!/usr/bin/env python3
"""Side-by-side pre-amendment-5 vs amendment-5 M1-strong table (per checker x side)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "results/tables/m1_strong_final.md"
NEW = ROOT / "results/tables/m1_strong_final_amend5.md"
OUT = ROOT / "notes/m1_strong_amend5_side_by_side.md"


def _short(cell: str) -> str:
    m = re.match(r"([\d.]+)% \[[^\]]*\] \((\d+/\d+)\)", cell.strip())
    return f"{m.group(1)} ({m.group(2)})" if m else cell.strip()


def parse(path: Path) -> dict:
    out: dict = {"up": {}, "down": {}, "bind": {}}
    block = None
    for line in path.read_text().splitlines():
        if line.startswith("## V4 denominator"):
            break
        if line.startswith("### US_up"):
            block = "up"
        elif line.startswith("### US_down"):
            block = "down"
        elif line.startswith("### Bind?"):
            block = "bind"
        if not line.startswith("| ") or line.startswith("| Model") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if block in ("up", "down") and len(cells) == 9:
            model, side, ns, bef, aft, n, bc, _p, bind = cells
            out[block][(model, side)] = {
                "ns": _short(ns), "before": _short(bef), "after": _short(aft),
                "n": n.split(" / ")[0], "bc": bc, "bind": bind,
            }
        elif block == "bind" and len(cells) == 4:
            model, claim, evid, overall = cells
            for side, txt in (("CLAIM", claim), ("EVID", evid)):
                out["bind"][(model, side)] = txt.split("**")[1]
            out["bind"][(model, "Overall")] = overall.strip("*")
    return out


def pair(a: str, b: str) -> str:
    return a if a == b else f"{a} → **{b}**"


def main() -> None:
    old, new = parse(OLD), parse(NEW)
    lines = [
        "# M1-strong: pre-amendment-5 vs amendment-5 (side by side)",
        "",
        f"Sources: `{OLD.relative_to(ROOT)}` (pre-amendment-5) and `{NEW.relative_to(ROOT)}` (amendment 5). "
        "Each cell is `pre → **amend5**` when it changed, otherwise one value. Rates are % FAIL (k/n); "
        "95% cluster-bootstrap CIs are in the source tables. "
        "n = paired rows; b/c = PASS→FAIL / FAIL→PASS. MiniCheck-DeBERTa's pre-amendment-5 values are the "
        "node30 scores; amendment 5 uses the cpuverif scores (approved swap), so its NS and before cells move too.",
        "",
    ]
    for title, blk, nsname in (("US_up (×1000) vs NS_x10", "up", "NS_x10"),
                               ("US_down (unit-down) vs NS_div10", "down", "NS_div10")):
        lines += [f"## {title}", "",
                  f"| Checker | Side | {nsname} | before | after | n | b/c | Bind |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for key, nv in new[blk].items():
            ov = old[blk].get(key, {})
            lines.append("| " + " | ".join([
                key[0], key[1],
                *(pair(ov.get(f, "NA"), nv[f]) for f in ("ns", "before", "after", "n", "bc", "bind")),
            ]) + " |")
        lines.append("")
    lines += ["## Bind (up, down → side)", "",
              "| Checker | CLAIM | EVID | Overall |", "| --- | --- | --- | --- |"]
    models = list(dict.fromkeys(k[0] for k in new["bind"]))
    for m in models:
        lines.append("| " + " | ".join([m] + [
            pair(old["bind"].get((m, s), "NA"), new["bind"][(m, s)]) for s in ("CLAIM", "EVID", "Overall")
        ]) + " |")
    lines.append("")
    OUT.write_text("\n".join(lines))
    print(OUT.read_text())


if __name__ == "__main__":
    main()
