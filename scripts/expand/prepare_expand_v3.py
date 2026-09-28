#!/usr/bin/env python3
"""QC v3 rule pass for expansion (mirrors src/prepare_v3.py paths under data/expand)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from qc_v3 import (  # noqa: E402
    dose_kind_v3,
    domain_kind_rule,
    extra_hedges,
    flip_bad_term,
    focus_sentence,
    neighbor_text,
    ocr_hits,
)

V2 = ROOT / "data" / "expand"
OUT = ROOT / "data" / "expand" / "v3"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def index_bases() -> dict[str, dict]:
    found = {}
    for name in ("bases_main.jsonl", "bases_threshold.jsonl", "bases_scope_excluded.jsonl"):
        path = V2 / name
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            found[row["id"]] = row
    return found


def main() -> None:
    bases = index_bases()
    instances = read_jsonl(V2 / "instances_main_pre_v3.jsonl") + read_jsonl(
        V2 / "instances_threshold.jsonl"
    )
    stats = Counter()
    meta = {}
    for base_id, base in bases.items():
        claim = base.get("claim") or ""
        target_field = base.get("target_sentence") or ""
        span = base.get("target_span_claim") or base.get("target_span_evidence") or ""
        target = focus_sentence(target_field, span)
        evidence = base.get("evidence") or ""
        c0 = claim.find(span) if span else -1
        if c0 < 0:
            c0, c1 = base.get("claim_span_start", 0), base.get("claim_span_end", 0)
        else:
            c1 = c0 + len(span)
        t0 = target.find(span) if span else -1
        target_ocr = ocr_hits(target)
        neigh_ocr = ocr_hits(neighbor_text(evidence, target))
        bad = None
        info = {
            "base_id": base_id,
            "type": base["type"],
            "subset": base.get("subset") or "main",
            "ocr_target": target_ocr,
            "ocr_noise": bool(neigh_ocr) and not target_ocr,
            "c0_drift": bool(extra_hedges(claim, target)),
            "dose_kind": None,
            "domain_kind": None,
            "flip_exclude": None,
            "exclude_reason": None,
        }
        if base["type"] == "DOSE":
            info["dose_kind"] = dose_kind_v3(claim, target, c0, c1)
        else:
            info["domain_kind"] = domain_kind_rule(claim, target)
            bad = flip_bad_term(claim, c0, c1) or (
                flip_bad_term(target, t0, t0 + len(span)) if t0 >= 0 else None
            )
            info["flip_exclude"] = bad
        if info["subset"] == "excluded_scope":
            info["exclude_reason"] = "scope"
        elif target_ocr:
            info["exclude_reason"] = "ocr_target"
        elif bad:
            info["exclude_reason"] = "flip_scope:" + (bad or "")
        meta[base_id] = info
        stats["bases"] += 1
        if info.get("exclude_reason"):
            stats["exclude"] += 1

    audit = []
    for row in instances:
        info = meta.get(row["base_id"], {})
        item = dict(row)
        item["subset"] = info.get("subset") or item.get("subset") or "main"
        item["dose_kind"] = info.get("dose_kind") if item["type"] == "DOSE" else None
        item["domain_kind"] = info.get("domain_kind") if item["type"] == "POLARITY" else None
        item["ocr_noise"] = bool(info.get("ocr_noise"))
        item["c0_drift"] = bool(info.get("c0_drift"))
        item["valid"] = True
        item["invalid_reason"] = None
        if item["magnitude"] == "paraphrase":
            item["valid"] = False
            item["invalid_reason"] = "inv_paraphrase_v2"
        elif info.get("exclude_reason"):
            item["valid"] = False
            item["invalid_reason"] = info["exclude_reason"]
        audit.append(item)

    write_jsonl(OUT / "instances_audit.jsonl", audit)
    valid_main = [r for r in audit if r["valid"] and r.get("subset") == "main"]
    write_jsonl(V2 / "instances_main.jsonl", valid_main)
    kept_base_ids = {r["base_id"] for r in valid_main if r.get("condition") == "C0"}
    main_bases = [b for b in read_jsonl(V2 / "bases_main.jsonl") if b["id"] in kept_base_ids]
    write_jsonl(V2 / "bases_main.jsonl", main_bases)
    yield_stats = {
        "bases_main_after_v3": len(main_bases),
        "bases_main_by_type": dict(Counter(b["type"] for b in main_bases)),
        "instances_main_valid": len(valid_main),
        "invalid": sum(1 for r in audit if not r["valid"]),
        "prepare_counts": dict(stats),
    }
    (OUT / "prepare_stats.json").write_text(json.dumps(yield_stats, indent=2) + "\n")
    print(json.dumps(yield_stats, indent=2))


if __name__ == "__main__":
    main()
