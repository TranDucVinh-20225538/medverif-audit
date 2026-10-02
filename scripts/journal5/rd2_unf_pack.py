#!/usr/bin/env python3
"""(RD2-5b) UNF packs for the transfer analysis: every RD2 (answer, excerpt) pair changed by UNF v1
(src/unit_norm_fix.py) or the FROZEN UNF v2 (src/unit_norm_fix_v2.py, sha256 in results/journal2/unf_v2_freeze.json).
Same construction as scripts/journal2/unf_heldout_rdpack.py (RD), applied to RD2.  CPU, stdlib, deterministic.

Outputs (results/journal5/rd2/real_dose/unf/):
  rd_pack.jsonl            chain-3 FT pack format (claim_orig/evidence_orig, claim_unf/evidence_unf, claim_unf_v2/...)
  instances_unf_v1.jsonl   instance schema, claim/evidence replaced by the UNF v1 texts (changed rows only)
  instances_unf_v2.jsonl   same for UNF v2  -> scored by scripts/journal2/small_checkers.py into scores_unf_v1/_v2
Unchanged rows keep their raw verdicts in the report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import INSTANCES, RD2, ROOT, log, read_jsonl, sha256_file, write_jsonl  # noqa: E402
import unit_norm_fix as V1  # noqa: E402
import unit_norm_fix_v2 as V2  # noqa: E402

OUTD = RD2 / "unf"


def main() -> None:
    frozen = json.loads((ROOT / "results/journal2/unf_v2_freeze.json").read_text())["sha256"]
    cur = sha256_file(ROOT / "src/unit_norm_fix_v2.py")
    if cur != frozen:
        raise SystemExit("src/unit_norm_fix_v2.py differs from the frozen version (%s != %s)" % (cur, frozen))
    rows = read_jsonl(INSTANCES)
    if not rows:
        raise SystemExit("no instances in %s" % INSTANCES)
    pack, i1, i2 = [], [], []
    for r in rows:
        c1, e1, x1 = V1.apply_unf_pair(r["claim"], r["evidence"])
        c2, e2, x2 = V2.apply_unf_pair(r["claim"], r["evidence"])
        ch1 = (c1, e1) != (r["claim"], r["evidence"])
        ch2 = (c2, e2) != (r["claim"], r["evidence"])
        if not (ch1 or ch2):
            continue
        pack.append({"instance_id": r["instance_id"], "base_id": r["drug"], "drug": r["drug"], "auto_class": r["auto_class"],
                     "generator": r["generator"], "answer_condition": r["answer_condition"],
                     "claim_orig": r["claim"], "evidence_orig": r["evidence"], "claim_unf": c1, "evidence_unf": e1,
                     "claim_unf_v2": c2, "evidence_unf_v2": e2, "v1_changed": ch1, "v2_changed": ch2,
                     "v1_edits": x1["edits"], "v2_edits": x2["edits"], "valid": True})
        if ch1:
            i1.append(dict(r, claim=c1, evidence=e1, unf="v1"))
        if ch2:
            i2.append(dict(r, claim=c2, evidence=e2, unf="v2"))
    write_jsonl(OUTD / "rd_pack.jsonl", pack)
    write_jsonl(OUTD / "instances_unf_v1.jsonl", i1)
    write_jsonl(OUTD / "instances_unf_v2.jsonl", i2)
    log("RD2_unf_pack", instances=len(rows), changed_v1_or_v2=len(pack), changed_v1=len(i1), changed_v2=len(i2),
        unf_v2_sha256=cur[:12])


if __name__ == "__main__":
    main()
