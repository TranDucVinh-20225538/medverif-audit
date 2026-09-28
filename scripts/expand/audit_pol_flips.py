#!/usr/bin/env python3
"""Audit expand POL flip mechanisms (not_remove / not_insert only; no lexical)."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_CLAUSE_END = re.compile(r"[.!?]\s*$")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def clause_final_not_insert(original_span: str, flipped_span: str, sentence: str) -> bool:
    """Heuristic: flip adds ' not ' and the edited cue sits at end of its clause."""
    if " not " not in f" {flipped_span.lower()} ":
        return False
    if " not " in f" {original_span.lower()} ":
        return False
    idx = sentence.lower().find(original_span.lower())
    if idx < 0:
        return False
    after = sentence[idx + len(original_span) :].strip()
    return bool(_CLAUSE_END.match(after)) or after == ""


def main() -> None:
    inst = read_jsonl(ROOT / "data" / "expand" / "instances_cpu_early.jsonl")
    bases = {b["id"]: b for b in read_jsonl(ROOT / "data" / "expand" / "bases_main.jsonl")}
    flips = [
        r
        for r in inst
        if r.get("type") == "POLARITY"
        and r.get("magnitude") == "flip"
        and r.get("condition") in ("E1-evid", "E1-claim")
    ]
    mech_counts = Counter(r.get("flip_mechanism") for r in flips)
    bad = []
    for row in flips:
        mech = row.get("flip_mechanism") or ""
        base = bases.get(row["base_id"], {})
        span = base.get("target_span_claim") or row.get("claim_span") or ""
        sent = base.get("target_sentence") or base.get("claim") or ""
        flipped = row.get("claim_span") or ""
        if mech == "lexical":
            bad.append({"base_id": row["base_id"], "reason": "lexical"})
        elif mech == "not_insert" and not clause_final_not_insert(span, flipped, sent):
            bad.append({"base_id": row["base_id"], "reason": "not_insert_not_clause_final"})
        elif mech not in ("not_remove", "not_insert"):
            bad.append({"base_id": row["base_id"], "reason": f"unexpected_mechanism:{mech}"})
    report = {
        "pol_flip_instances": len(flips),
        "flip_mechanism_counts": dict(mech_counts),
        "policy_ok": len(bad) == 0,
        "violations": bad[:50],
        "n_violations": len(bad),
    }
    out = ROOT / "notes" / "expand_pol_flip_audit.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
