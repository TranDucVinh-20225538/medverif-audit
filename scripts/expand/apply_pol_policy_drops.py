#!/usr/bin/env python3
"""Invalidate POL flip instances violating not_insert clause-final policy."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_CLAUSE_END = re.compile(r"[.!?]\s*$")

INSTANCE_GLOBS = (
    "instances_main.jsonl",
    "instances_cpu_early.jsonl",
    "instances_score_pending.jsonl",
    "instances_pending_node30.jsonl",
    "instances_pending_t6a.jsonl",
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def clause_final_not_insert(original_span: str, flipped_span: str, sentence: str) -> bool:
    if " not " not in f" {flipped_span.lower()} ":
        return False
    if " not " in f" {original_span.lower()} ":
        return False
    idx = sentence.lower().find(original_span.lower())
    if idx < 0:
        return False
    after = sentence[idx + len(original_span) :].strip()
    return bool(_CLAUSE_END.match(after)) or after == ""


def is_policy_violation(row: dict, bases: dict[str, dict]) -> bool:
    if row.get("type") != "POLARITY" or row.get("magnitude") != "flip":
        return False
    if row.get("condition") not in ("E1-evid", "E1-claim"):
        return False
    mech = row.get("flip_mechanism") or ""
    if mech == "lexical":
        return True
    if mech not in ("not_remove", "not_insert"):
        return True
    if mech != "not_insert":
        return False
    base = bases.get(row["base_id"], {})
    span = base.get("target_span_claim") or row.get("claim_span") or ""
    sent = base.get("target_sentence") or base.get("claim") or ""
    flipped = row.get("claim_span") or ""
    return not clause_final_not_insert(span, flipped, sent)


def main() -> None:
    bases = {b["id"]: b for b in read_jsonl(ROOT / "data" / "expand" / "bases_main.jsonl")}
    stats = Counter()
    for name in INSTANCE_GLOBS:
        path = ROOT / "data" / "expand" / name
        rows = read_jsonl(path)
        if not rows:
            continue
        n = 0
        for row in rows:
            if is_policy_violation(row, bases):
                row["valid"] = False
                row["invalid_reason"] = "policy_violation"
                n += 1
        if n:
            write_jsonl(path, rows)
        stats[name] = n

    inst = read_jsonl(ROOT / "data" / "expand" / "instances_main.jsonl")
    pol_bases_all = {b["id"] for b in bases.values() if b.get("type") == "POLARITY"}
    compliant_flip_bases = set()
    for row in inst:
        if row.get("type") != "POLARITY" or row.get("magnitude") != "flip":
            continue
        if row.get("valid") is False:
            continue
        if row.get("condition") in ("E1-evid", "E1-claim"):
            compliant_flip_bases.add(row["base_id"])

    report = {
        "invalidated_flip_rows_by_file": dict(stats),
        "invalidated_flip_rows_total": sum(stats.values()),
        "pol_bases_total": len(pol_bases_all),
        "pol_bases_with_compliant_flip": len(compliant_flip_bases),
    }
    out = ROOT / "notes" / "expand_pol_policy_drops.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
