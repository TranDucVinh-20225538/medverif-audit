#!/usr/bin/env python3
"""Amendment 5: rebuild only the off-spec after-M1 rows with the spec normalizer (score with MEDVERIF_M1=0)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from m1_provenance_check import FINAL_COMMIT, PACKS, git_jsonl, sources_for  # noqa: E402
from quantity_norm import M1_DOSE_RE_SPEC, apply_m1_pair  # noqa: E402

OUT = {
    "us_up_local": ROOT / "data/lane_b/m1_t7_e1_unit_amend5.jsonl",
    "us_up_api": ROOT / "data/t7/instances_e1_unit_m1_amend5.jsonl",
}


def main() -> None:
    prov = json.loads((ROOT / "notes/m1_provenance.json").read_text())
    summary = {}
    for name, out in OUT.items():
        off = set(prov["packs"][name]["off_spec"])
        src = sources_for(name)
        rows = []
        for row in git_jsonl(PACKS[name][0], FINAL_COMMIT):
            if row["instance_id"] not in off:
                continue
            s = src[row["instance_id"]]
            claim, evidence = apply_m1_pair(s["claim"], s["evidence"], M1_DOSE_RE_SPEC)
            rows.append({
                **row,
                "claim": claim,
                "evidence": evidence,
                "content_sha1": hashlib.sha1(f"{claim}\n{evidence}".encode()).hexdigest(),
                "m1_preapplied": True,
                "m1_spec": "amendment5",
            })
        with out.open("w") as handle:
            for row in sorted(rows, key=lambda r: r["instance_id"]):
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        summary[name] = {"rows": len(rows), "out": str(out.relative_to(ROOT))}
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
