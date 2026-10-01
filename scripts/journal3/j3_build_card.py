#!/usr/bin/env python3
"""(J3-P) Freeze the main DOSE card cohort for chain 3 -> results/journal3/packs/card.jsonl (run on a CLEAN checkout).

The paper's card definitions live in scripts/t15_card_report.py + analysis/ helpers, several of which are locally
modified on the HPC copy.  To keep chain 3 independent of those files, this builder is run once on a clean checkout
(git HEAD) and its output is committed; chain-3 jobs only READ the frozen file.

Rows = exactly what the paper's card uses (t15_card_report.load_main_dose_instances() + join_extra(T7)), plus the
T17 unit-down rows (data/v3/t17_downdose.jsonl, condition E1-unit-down, valid, analysis_keep_row, main bases) so that
US_claim_down / US_evid_down can be computed (the T19 scale-sweep cohort uses the same T17 rows).
Per row: instance_id, base_id, condition, magnitude, natural_inv (paper's _natural_inv), claim, evidence, card_src.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "analysis", ROOT / "scripts", ROOT / "src"):
    sys.path.insert(0, str(p))
OUT = ROOT / "results/journal3/packs/card.jsonl"
# conditions the card metrics use (E2 rows of instances_main are not part of any card cell -> not scored)
USED = {"C0", "INV-claim", "E1-claim", "E1-evid", "E1-unit-claim", "E1-unit-evid", "E1-unit-down"}
T17 = ROOT / "data/v3/t17_downdose.jsonl"
DEPS = ["scripts/t15_card_report.py", "analysis/analyze.py", "analysis/review_filters.py", "scripts/t14_t3_filter_report.py",
        "data/v3/instances_main.jsonl", "data/t7/instances_e1_unit.jsonl", "data/v3/t17_downdose.jsonl"]


def main() -> None:
    dirty = subprocess.run(["git", "status", "--porcelain", "--"] + DEPS, cwd=ROOT, capture_output=True, text=True).stdout
    if dirty.strip():
        raise SystemExit("card dependencies modified vs HEAD; build on a clean checkout:\n" + dirty)
    import t15_card_report as T
    from review_filters import analysis_keep_row

    inst = T.load_main_dose_instances()
    main_bases = {r["base_id"] for r in inst}
    rows = [dict(r, card_src="main") for r in inst]
    for r in T.read_jsonl(T.T7):
        if r.get("valid", True) and analysis_keep_row(r) and r["base_id"] in main_bases:
            rows.append(dict(r, card_src="t7"))
    for r in T.read_jsonl(T17):
        if r.get("condition") == "E1-unit-down" and r.get("valid", True) and analysis_keep_row(r) and r["base_id"] in main_bases:
            rows.append(dict(r, card_src="t17"))
    out = []
    for r in rows:
        if r["condition"] not in USED:
            continue
        out.append({"instance_id": r["instance_id"], "base_id": r["base_id"], "condition": r["condition"],
                    "magnitude": r.get("magnitude"), "natural_inv": bool(T._natural_inv(r)) if r["condition"] == "INV-claim" else False,
                    "edit_side": r.get("edit_side"), "claim": r["claim"], "evidence": r["evidence"], "card_src": r["card_src"]})
    ids = [r["instance_id"] for r in out]
    assert len(ids) == len(set(ids)), "duplicate ids"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    man = {"built_from_commit": head, "n_rows": len(out), "n_bases": len(main_bases),
           "by_src_condition": {"%s|%s|%s" % (r["card_src"], r["condition"], r["magnitude"]): n
                                for r, n in ((dict(zip(("card_src", "condition", "magnitude"), k)), n) for k, n in
                                             Counter((x["card_src"], x["condition"], x["magnitude"]) for x in out).items())},
           "n_natural_inv": sum(r["natural_inv"] for r in out), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()}
    (OUT.parent / "card_manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
