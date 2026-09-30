#!/usr/bin/env python3
"""T17 NS: FAIL rate on value ÷2 and ÷10 (claim / evidence), conditional on C0 PASS on main DOSE."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ("analysis", "scripts", "src"):
    sys.path.insert(0, str(ROOT / p))

from analyze import _c0_pass_bases, _parsed, bootstrap_rate  # noqa: E402
import m1_strong_run as m1s  # noqa: E402
from t13_best_of_n_report import merged_score_rows  # noqa: E402
from t15_card_report import T17, fmt_stat, join_extra, join_rows, load_main_dose_instances  # noqa: E402
from verifier_labels import CANONICAL_VERIFIERS, FAMILY_ORDER, verifier_display_name, verifier_family  # noqa: E402

OUT_MD = ROOT / "results/tables/t17_ns.md"
OUT_JSON = ROOT / "notes/t17_ns.json"
CELLS = (
    ("div2_claim", "E1-down2", "__claim__"),
    ("div2_evid", "E1-down2", "__evid__"),
    ("div10_claim", "E1-down10", "__claim__"),
    ("div10_evid", "E1-down10", "__evid__"),
)


def verdicts(rows: dict[str, dict]) -> dict[str, str]:
    out = {}
    for iid, r in rows.items():
        v = r.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[iid] = v
        elif r.get("score") is not None:
            out[iid] = "PASS" if float(r["score"]) >= 0.5 else "FAIL"
    return out


def main() -> None:
    main_inst = load_main_dose_instances()
    res: dict[str, dict] = {}
    for slug in CANONICAL_VERIFIERS:
        c0_block = [r for r in join_rows(main_inst, verdicts(merged_score_rows(slug))) if r.get("condition") == "C0"]
        c0p = _c0_pass_bases(c0_block)
        t17 = join_extra(main_inst, m1s.merge_verdicts(slug, m1s.T17_DIRS), T17)
        cells = {}
        for key, cond, sub in CELLS:
            by: dict[str, list[str]] = defaultdict(list)
            for r in t17:
                if r["base_id"] in c0p and r.get("condition") == cond and sub in r["instance_id"] and _parsed(r):
                    by[r["base_id"]].append(r["verdict"])
            cells[key] = bootstrap_rate([(sum(v == "FAIL" for v in g), len(g)) for g in by.values()])
        res[slug] = {"display_name": verifier_display_name(slug), "family": verifier_family(slug),
                     "n_c0_bases_scored": len({r["base_id"] for r in c0_block}), "n_c0_pass_bases": len(c0p), "cells": cells}
    lines = [
        "# T17 — NS on value ÷2 / ÷10 (FAIL | C0 PASS)",
        "",
        "Main DOSE bases (non-dose excluded, `analysis_keep_row`); C0 PASS from main-pack scores; "
        "T17 scores from `results/raw/t17` then `results/raw/lane_b/t17_downdose` (last wins). "
        "Cells: FAIL rate [95% cluster bootstrap by base, 1000, seed 42] (n rows, q bases). Higher = better.",
        "",
        "| model | family | C0 PASS bases | ÷2 claim | ÷2 evid | ÷10 claim | ÷10 evid |",
        "|---|---|---:|---|---|---|---|",
    ]
    for slug, d in sorted(res.items(), key=lambda t: (FAMILY_ORDER.get(t[1]["family"], 9), t[1]["display_name"])):
        if not any(c.get("den") for c in d["cells"].values()):
            continue
        lines.append(f"| {d['display_name']} | {d['family']} | {d['n_c0_pass_bases']}/{d['n_c0_bases_scored']} | "
                     + " | ".join(fmt_stat(d["cells"][k]) for k, _, _ in CELLS) + " |")
    missing = [d["display_name"] for d in res.values() if not any(c.get("den") for c in d["cells"].values())]
    if missing:
        lines += ["", "No T17 scores: " + ", ".join(missing)]
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(res, indent=1) + "\n")
    print(OUT_MD.read_text())


if __name__ == "__main__":
    main()
