#!/usr/bin/env python3
"""(UNF-HO-2) Real-dose (RD) pairs for the held-out UNF evaluation: every RD (claim = LLM answer, evidence = label
excerpt) pair whose text UNF v1 (src/unit_norm_fix.py) OR the frozen post-hoc v2 (src/unit_norm_fix_v2.py) changes.
Packs: orig (claim_orig/evidence_orig), unf (v1), unf_v2 (v2).  Unchanged rows keep the stored verdicts in the report.
CPU, stdlib, deterministic.  Output: results/journal2/unf_heldout/rd_pack.jsonl
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import unit_norm_fix as V1  # noqa: E402
import unit_norm_fix_v2 as V2  # noqa: E402

INST = ROOT / "results/journal2/real_dose/instances.jsonl"
OUT = ROOT / "results/journal2/unf_heldout/rd_pack.jsonl"
FREEZE = ROOT / "results/journal2/unf_v2_freeze.json"


def main() -> None:
    sha = hashlib.sha256((ROOT / "src/unit_norm_fix_v2.py").read_bytes()).hexdigest()
    frozen = json.loads(FREEZE.read_text())["sha256"]
    if sha != frozen:
        raise SystemExit("src/unit_norm_fix_v2.py differs from the frozen version (%s != %s)" % (sha, frozen))
    rows = [json.loads(l) for l in INST.open(encoding="utf-8") if l.strip()]
    pack = []
    for r in rows:
        c1, e1, i1 = V1.apply_unf_pair(r["claim"], r["evidence"])
        c2, e2, i2 = V2.apply_unf_pair(r["claim"], r["evidence"])
        ch1 = (c1, e1) != (r["claim"], r["evidence"])
        ch2 = (c2, e2) != (r["claim"], r["evidence"])
        if ch1 or ch2:
            pack.append({"instance_id": r["instance_id"], "base_id": r["drug"], "drug": r["drug"], "auto_class": r["auto_class"],
                         "generator": r["generator"], "answer_condition": r["answer_condition"],
                         "claim_orig": r["claim"], "evidence_orig": r["evidence"], "claim_unf": c1, "evidence_unf": e1,
                         "claim_unf_v2": c2, "evidence_unf_v2": e2, "v1_changed": ch1, "v2_changed": ch2,
                         "v1_edits": i1["edits"], "v2_edits": i2["edits"], "valid": True})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for p in pack:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(json.dumps({"rd_rows": len(rows), "changed_v1_or_v2": len(pack), "changed_v1": sum(p["v1_changed"] for p in pack),
                      "changed_v2": sum(p["v2_changed"] for p in pack),
                      "v2_only": sum(p["v2_changed"] and not p["v1_changed"] for p in pack),
                      "v1_only": sum(p["v1_changed"] and not p["v2_changed"] for p in pack),
                      "v1_v2_text_differs": sum((p["claim_unf"], p["evidence_unf"]) != (p["claim_unf_v2"], p["evidence_unf_v2"]) for p in pack),
                      "by_class": dict(Counter(p["auto_class"] for p in pack))}, indent=1))


if __name__ == "__main__":
    main()
