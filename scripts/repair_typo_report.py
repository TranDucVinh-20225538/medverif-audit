#!/usr/bin/env python3
"""Repair: before-M1 PASS explanations on T7 E1-unit-evid ×1000 that call the evidence unit a typo/error.

Keyword screen, then every hit hand-classified (MANUAL below) by which side the explanation blames."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JUDGES = (
    ("MedScore × Mistral-Small-24B", "results/raw/t7/v1_medscore.jsonl"),
    ("RAGAS × Llama-3.3-70B", "results/raw/t7/v4_ragas_nli.llama.jsonl"),
)
KW = re.compile(
    r"\b(typo|typographical|mistake|misprint|error|erroneous|incorrect(ly)?|likely (meant|intended|a)|probably (meant|intended)|"
    r"should (be|read)|meant to (be|say)|presumably|unrealistic|implausible|not plausible|unusually high|too high|extremely high)\b",
    re.I,
)
# evidence = explanation says the evidence/context unit is a typo or error; claim = blames the claim's unit;
# unspecified = "typo or discrepancy" without saying which side; none = keyword matched unrelated wording.
MANUAL = {
    "v1_medscore": {
        "D0038__E1-unit-evid__x1000": "evidence", "D0103__E1-unit-evid__x1000": "evidence",
        "D0114__E1-unit-evid__x1000": "evidence", "D0180__E1-unit-evid__x1000": "evidence",
    },
    "v4_ragas_nli": {
        "D0032__E1-unit-evid__x1000": "evidence", "D0048__E1-unit-evid__x1000": "evidence",
        "D0092__E1-unit-evid__x1000": "evidence", "D0116__E1-unit-evid__x1000": "evidence",
        "D0063__E1-unit-evid__x1000": "unspecified", "D0127__E1-unit-evid__x1000": "unspecified",
        "D0038__E1-unit-evid__x1000": "claim", "D0040__E1-unit-evid__x1000": "claim",
        "D0046__E1-unit-evid__x1000": "claim", "D0062__E1-unit-evid__x1000": "claim",
        "D0061__E1-unit-evid__x1000": "none", "D0180__E1-unit-evid__x1000": "none",
    },
}
OUT_MD = ROOT / "notes/repair_typo_explanations.md"
OUT_JSON = ROOT / "notes/repair_typo_explanations.json"


def main() -> None:
    lines = ["# Repair — judges calling the evidence unit a typo (before M1)", "",
             "Rows: T7 `E1-unit-evid` ×1000 with an API-logged verdict; N = PASS explanations. Keyword screen, every hit hand-classified.", "",
             "| judge | PASS / rows | keyword hits | evidence unit called typo/error | unspecified side | blames claim unit | false hit |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    out, examples = {}, []
    for name, path in JUDGES:
        slug = "v1_medscore" if "v1_" in path else "v4_ragas_nli"
        rows = [json.loads(l) for l in (ROOT / path).open() if l.strip()]
        ev = [r for r in rows if "__E1-unit-evid__" in r["instance_id"] and r.get("api_model")]
        ps = [r for r in ev if r["verdict"] == "PASS"]
        hits = [r for r in ps if KW.search(r.get("raw_output") or "")]
        unlabelled = [r["instance_id"] for r in hits if r["instance_id"] not in MANUAL[slug]]
        if unlabelled:
            raise SystemExit(f"hand-classify new keyword hits for {slug}: {unlabelled}")
        lab = [MANUAL[slug][r["instance_id"]] for r in hits]
        cnt = {k: lab.count(k) for k in ("evidence", "unspecified", "claim", "none")}
        out[name] = {"n_rows": len(ev), "n_pass": len(ps), "n_hits": len(hits), **cnt, "source": path,
                     "evidence_ids": [r["instance_id"] for r in hits if MANUAL[slug][r["instance_id"]] == "evidence"]}
        lines.append(f"| {name} | {len(ps)}/{len(ev)} | {len(hits)} | **{cnt['evidence']}/{len(ps)}** | {cnt['unspecified']} | {cnt['claim']} | {cnt['none']} |")
        for r in [r for r in hits if MANUAL[slug][r["instance_id"]] == "evidence"][:3]:
            examples.append((name, r["instance_id"], " ".join(r["raw_output"].split())))
    lines += ["", "## Verbatim examples (evidence unit called a typo)", ""]
    for name, iid, text in examples:
        lines.append(f"- **{name}** `{iid}`: {text[:900]}")
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(out, indent=1) + "\n")
    print(OUT_MD.read_text())


if __name__ == "__main__":
    main()
