"""Apply the PI label fixes to kept bases and rebuild instances.

Paraphrase YES/NO labels are read from data/v2/paraphrase_labels.jsonl when present.
Unclear dose_kind labels are read from data/v2/dose_kind_labels.jsonl when present.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from perturb import perturb_one
from qc_rules import dose_kind_rule, paraphrase_candidates, scope_hit, threshold_governed

ROOT = Path("/data2/hpcshared/medverif-audit")
BASES = ROOT / "data" / "base_pairs.jsonl"
OUT = ROOT / "data" / "v2"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
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


def main() -> None:
    bases = read_jsonl(BASES)
    para_yes = {}
    for row in read_jsonl(OUT / "paraphrase_labels.jsonl"):
        if row.get("label") == "YES":
            para_yes.setdefault(row["base_id"], row)
    kind_override = {row["base_id"]: row["dose_kind"] for row in read_jsonl(OUT / "dose_kind_labels.jsonl")}
    main_bases = []
    threshold = []
    scope_ex = []
    pending_para = []
    pending_kind = []
    stats = Counter()
    for base in bases:
        row = dict(base)
        claim = row["claim"]
        c0, c1 = row["claim_span_start"], row["claim_span_end"]
        if row["type"] == "DOSE":
            quant = threshold_governed(claim, c0, c1) or threshold_governed(
                row.get("target_sentence") or claim,
                (row.get("target_sentence") or claim).find(row["target_span_claim"]),
                (row.get("target_sentence") or claim).find(row["target_span_claim"]) + len(row["target_span_claim"]),
            )
            kind = dose_kind_rule(claim + " " + (row.get("target_sentence") or ""))
            if kind == "unclear":
                if row["id"] in kind_override:
                    kind = kind_override[row["id"]]
                else:
                    pending_kind.append({
                        "base_id": row["id"],
                        "text": claim + "\n" + (row.get("target_sentence") or ""),
                    })
            row["dose_kind"] = kind
            row["threshold_quantifier"] = quant
            if quant:
                row["subset"] = "threshold"
                threshold.append(row)
                stats["dose_threshold"] += 1
            else:
                row["subset"] = "main"
                main_bases.append(row)
                stats["dose_main"] += 1
                stats["dose_kind_" + kind] += 1
        else:
            hit = scope_hit(claim, c0, c1)
            if hit:
                row["subset"] = "excluded_scope"
                row["scope_term"] = hit
                scope_ex.append(row)
                stats["polarity_scope_" + hit] += 1
                stats["polarity_scope"] += 1
                continue
            row["subset"] = "main"
            main_bases.append(row)
            stats["polarity_main"] += 1
        chosen = para_yes.get(row["id"])
        if chosen:
            row["paraphrases"] = [chosen]
            stats["paraphrase_yes"] += 1
        else:
            cands = paraphrase_candidates(claim, row["target_span_claim"])
            row["paraphrase_candidates"] = cands
            if cands:
                pending_para.append({"base_id": row["id"], "original": claim, "span": row["target_span_claim"], "candidates": cands})
            else:
                stats["paraphrase_no_candidate"] += 1
        got, failed = perturb_one(row)
        row["_instances"] = got
        row["_failed"] = failed
        if failed:
            stats["perturb_fail"] += 1

    instances_main = []
    instances_threshold = []
    for row in main_bases:
        instances_main.extend(row.pop("_instances"))
        row.pop("_failed", None)
    for row in threshold:
        instances_threshold.extend(row.pop("_instances"))
        row.pop("_failed", None)
    mech = Counter(row.get("flip_mechanism") for row in instances_main if row["type"] == "POLARITY" and row["condition"] == "C0")
    unit = sum(1 for row in instances_main if row["magnitude"] == "unit_conversion")
    no_unit = sum(1 for row in main_bases if row["type"] == "DOSE") - unit
    summary = {
        "bases_in": len(bases),
        "dose_main": stats["dose_main"],
        "dose_threshold": stats["dose_threshold"],
        "polarity_main": stats["polarity_main"],
        "polarity_scope_excluded": stats["polarity_scope"],
        "scope_terms": {key.split("_", 2)[-1]: stats[key] for key in stats if key.startswith("polarity_scope_")},
        "flip_mechanism_main": dict(mech),
        "dose_kind_main": {key.split("_", 2)[-1]: stats[key] for key in stats if key.startswith("dose_kind_")},
        "unit_inv_main": unit,
        "dose_main_without_unit_inv": no_unit,
        "instances_main": len(instances_main),
        "instances_threshold": len(instances_threshold),
        "paraphrase_pending": len(pending_para),
        "dose_kind_pending": len(pending_kind),
        "paraphrase_yes": stats["paraphrase_yes"],
    }
    write_jsonl(OUT / "bases_main.jsonl", main_bases)
    write_jsonl(OUT / "bases_threshold.jsonl", threshold)
    write_jsonl(OUT / "bases_scope_excluded.jsonl", scope_ex)
    write_jsonl(OUT / "instances_main.jsonl", instances_main)
    write_jsonl(OUT / "instances_threshold.jsonl", instances_threshold)
    write_jsonl(OUT / "paraphrase_pending.jsonl", pending_para)
    write_jsonl(OUT / "dose_kind_pending.jsonl", pending_kind)
    (OUT / "rebuild_stats.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
