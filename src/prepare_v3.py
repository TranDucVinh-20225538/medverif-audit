"""Mark v2 instances valid/invalid. Does not delete rows. Writes the GPU todo."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from qc_v3 import (
    dose_kind_v3,
    domain_kind_rule,
    extra_hedges,
    flip_bad_term,
    focus_sentence,
    neighbor_text,
    ocr_hits,
)

ROOT = Path("/data2/hpcshared/medverif-audit")
V2 = ROOT / "data" / "v2"
OUT = ROOT / "data" / "v3"


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
        if not path.exists():
            continue
        for row in read_jsonl(path):
            found[row["id"]] = row
    return found


def main() -> None:
    bases = index_bases()
    instances = read_jsonl(V2 / "instances_main.jsonl") + read_jsonl(V2 / "instances_threshold.jsonl")
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
        t1 = t0 + len(span) if t0 >= 0 else 0
        target_ocr = ocr_hits(target)
        neigh_ocr = ocr_hits(neighbor_text(evidence, target))
        if target_field != target:
            neigh_ocr = sorted(set(neigh_ocr + ocr_hits(target_field.replace(target, " ", 1))))
        info = {
            "base_id": base_id,
            "type": base["type"],
            "subset": base.get("subset") or "main",
            "ocr_target": target_ocr,
            "ocr_noise": bool(neigh_ocr) and not target_ocr,
            "ocr_neighbor": neigh_ocr,
            "c0_drift": bool(extra_hedges(claim, target)),
            "c0_drift_terms": extra_hedges(claim, target),
            "dose_kind": None,
            "domain_kind": None,
            "flip_exclude": None,
            "exclude_reason": None,
        }
        if base["type"] == "DOSE":
            info["dose_kind"] = dose_kind_v3(claim, target, c0, c1)
        else:
            info["domain_kind"] = domain_kind_rule(claim, target)
            bad = flip_bad_term(claim, c0, c1) or (flip_bad_term(target, t0, t1) if t0 >= 0 else None)
            info["flip_exclude"] = bad
        if info["subset"] == "excluded_scope":
            info["exclude_reason"] = "scope"
        elif target_ocr:
            info["exclude_reason"] = "ocr_target"
        elif bad if base["type"] == "POLARITY" else False:
            info["exclude_reason"] = "flip_scope:" + (info["flip_exclude"] or "")
        meta[base_id] = info
        stats["bases"] += 1
        if info["exclude_reason"]:
            stats["exclude_" + info["exclude_reason"].split(":")[0]] += 1
        if info["ocr_noise"]:
            stats["ocr_noise"] += 1
        if info["c0_drift"]:
            stats["c0_drift"] += 1
        if info["dose_kind"]:
            stats["dose_" + info["dose_kind"]] += 1
        if info["domain_kind"]:
            stats["domain_" + info["domain_kind"]] += 1

    audit = []
    for row in instances:
        info = meta.get(row["base_id"], {})
        item = dict(row)
        item["dose_kind"] = info.get("dose_kind") if item["type"] == "DOSE" else None
        item["domain_kind"] = info.get("domain_kind") if item["type"] == "POLARITY" else None
        item["ocr_noise"] = bool(info.get("ocr_noise"))
        item["c0_drift"] = bool(info.get("c0_drift"))
        item["valid"] = True
        item["invalid_reason"] = None
        if item["magnitude"] == "paraphrase":
            item["valid"] = False
            item["invalid_reason"] = "inv_paraphrase_v2"
            stats["invalid_paraphrase_v2"] += 1
        elif info.get("exclude_reason"):
            item["valid"] = False
            item["invalid_reason"] = info["exclude_reason"]
            stats["invalid_excluded"] += 1
        audit.append(item)

    todo = []
    for base_id, info in meta.items():
        if info.get("exclude_reason"):
            continue
        if info["subset"] not in {"main", "threshold"}:
            continue
        base = bases[base_id]
        todo.append({
            "base_id": base_id,
            "type": base["type"],
            "subset": info["subset"],
            "claim": base["claim"],
            "span": base["target_span_claim"],
            "dose_kind": info["dose_kind"],
            "domain_kind": info["domain_kind"],
            "need_dose_kind": info["dose_kind"] == "unclear",
            "need_domain": info["domain_kind"] == "unclear",
        })
        stats["todo_" + info["subset"]] += 1

    flips = []
    seen = set()
    for item in audit:
        if not item["valid"] or item["type"] != "POLARITY" or item["condition"] != "E1-claim":
            continue
        if item["base_id"] in seen:
            continue
        seen.add(item["base_id"])
        flips.append({
            "base_id": item["base_id"],
            "claim": item["claim"],
            "span": item.get("claim_span") or "",
        })

    write_jsonl(OUT / "instances_audit.jsonl", audit)
    write_jsonl(OUT / "paraphrase_todo.jsonl", todo)
    write_jsonl(OUT / "flip_fluency_todo.jsonl", flips)
    (OUT / "prepare_stats.json").write_text(json.dumps({
        "counts": dict(stats),
        "note": "v2 files were not deleted. paraphrase rows are valid=false.",
    }, indent=2) + "\n")
    print(json.dumps(dict(stats), indent=2))


if __name__ == "__main__":
    main()
