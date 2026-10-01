#!/usr/bin/env python3
"""(UNF-1) Build the scoring packs for the unit-normalization fix (stdlib, no models).

Cohort = the paper's main DOSE card cohort (scripts/t15_card_report.load_main_dose_instances: C0,
E1-claim/E1-evid x2/x10, E2 x2/x10, INV-claim unit conversion) + T7 E1-unit (x1000, claim/evid side)
+ T17 E1-unit-down (claim/evid side), valid rows only.

  data/journal2/unf/cohort_orig.jsonl   original claim/evidence (box re-score = same-env "before")
  data/journal2/unf/cohort_unf.jsonl    UNF-normalized claim/evidence (src/unit_norm_fix.py), with
                                        `unf_changed` and the span edit log
  results/journal2/unf/build_manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("src", "analysis", "scripts"):
    sys.path.insert(0, str(ROOT / p))

from t15_card_report import T7, T17, load_main_dose_instances  # noqa: E402
from unit_norm_fix import apply_unf_pair  # noqa: E402
from analyze import read_jsonl  # noqa: E402

OUTD = ROOT / "data/journal2/unf"
RES = ROOT / "results/journal2/unf"


def cohort() -> list:
    rows = list(load_main_dose_instances())
    main_bases = {r["base_id"] for r in rows}
    for path, conds in ((T7, {"E1-unit-claim", "E1-unit-evid"}), (T17, {"E1-unit-down"})):
        for r in read_jsonl(path):
            if r.get("valid", True) and r.get("condition") in conds and r["base_id"] in main_bases:
                rows.append(r)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="evidence", choices=["evidence", "si"])
    ap.add_argument("--outdir", default=str(OUTD))
    args = ap.parse_args()
    outd = Path(args.outdir)
    outd.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    rows = cohort()
    keep = ("instance_id", "base_id", "type", "condition", "magnitude", "expected_verdict", "claim_span", "evidence_span")
    orig, unf, stats = [], [], Counter()
    for r in rows:
        base = {k: r.get(k) for k in keep}
        orig.append(dict(base, claim=r["claim"], evidence=r["evidence"], valid=True))
        c2, e2, info = apply_unf_pair(r["claim"], r["evidence"], mode=args.mode)
        ch = (c2 != r["claim"]) or (e2 != r["evidence"])
        stats[(r["condition"], "changed" if ch else "same")] += 1
        unf.append(dict(base, claim=c2, evidence=e2, valid=True, unf_changed=ch, unf_claim_changed=c2 != r["claim"],
                        unf_evidence_changed=e2 != r["evidence"], unf_edits=info["edits"], unf_mode=args.mode))
    suffix = "" if args.mode == "evidence" else "_" + args.mode
    for name, data in (("cohort_orig.jsonl", orig), ("cohort_unf%s.jsonl" % suffix, unf)):
        with (outd / name).open("w", encoding="utf-8") as fh:
            for r in data:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    man = {"mode": args.mode, "rows": len(rows), "bases": len({r["base_id"] for r in rows}),
           "changed": sum(1 for r in unf if r["unf_changed"]),
           "by_condition": {"%s|%s" % k: v for k, v in sorted(stats.items())}}
    (RES / ("build_manifest%s.json" % suffix)).write_text(json.dumps(man, indent=1) + "\n")
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
