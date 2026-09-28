"""Attach v3 labels. Keeps invalid rows in the audit file."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
OUT = ROOT / "data" / "v3"


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
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    audit = [row for row in read_jsonl(OUT / "instances_audit.jsonl") if row.get("magnitude") != "paraphrase" or row.get("invalid_reason") == "inv_paraphrase_v2"]
    audit = [row for row in audit if not str(row.get("instance_id", "")).endswith("paraphrase_v3")]
    dose = {row["base_id"]: row["dose_kind"] for row in read_jsonl(OUT / "dose_kind_phi.jsonl")}
    domain = {row["base_id"]: row["domain_kind"] for row in read_jsonl(OUT / "domain_phi.jsonl")}
    fluent = {row["base_id"]: row for row in read_jsonl(OUT / "flip_fluency.jsonl")}
    best = {}
    attempts = Counter()
    for row in read_jsonl(OUT / "para_attempts.jsonl"):
        attempts[row["base_id"]] += 1
        if row.get("passed") and row["base_id"] not in best:
            best[row["base_id"]] = row
    for row in audit:
        if row["base_id"] in dose and row["type"] == "DOSE":
            row["dose_kind"] = dose[row["base_id"]]
        if row["base_id"] in domain and row["type"] == "POLARITY":
            row["domain_kind"] = domain[row["base_id"]]
        verdict = fluent.get(row["base_id"])
        if row["valid"] and verdict and verdict.get("fluency") != "YES":
            row["valid"] = False
            row["invalid_reason"] = "flip_ungrammatical"
    c0 = {}
    for row in audit:
        if row["condition"] == "C0":
            c0[row["base_id"]] = row
    added = []
    for base_id, para in best.items():
        source = c0.get(base_id)
        if source is None or not source["valid"]:
            continue
        item = dict(source)
        item["instance_id"] = f"{base_id}__INV-claim__paraphrase_v3"
        item["condition"] = "INV-claim"
        item["magnitude"] = "paraphrase"
        item["claim"] = para["text"]
        item["evidence"] = source.get("evidence_c0") or source["evidence"]
        item["expected_verdict"] = "PASS"
        item["valid"] = True
        item["invalid_reason"] = None
        item["diff"] = {"where": "paraphrase_v3", "attempt": para.get("attempt")}
        added.append(item)
    audit.extend(added)
    write_jsonl(OUT / "instances_audit.jsonl", audit)
    main_rows = [row for row in audit if row["valid"] and row.get("subset") == "main"]
    thr_rows = [row for row in audit if row["valid"] and row.get("subset") == "threshold"]
    write_jsonl(OUT / "instances_main.jsonl", main_rows)
    write_jsonl(OUT / "instances_threshold.jsonl", thr_rows)
    bases = [row for row in audit if row["condition"] == "C0" and row["valid"] and row.get("subset") == "main"]
    cross = Counter((row["type"], row.get("flip_mechanism") or "-", row.get("dose_kind") or "-") for row in bases)
    todo_ids = [row["base_id"] for row in read_jsonl(OUT / "paraphrase_todo.jsonl")]
    asked_valid = [base_id for base_id in todo_ids if c0.get(base_id) and c0[base_id]["valid"]]
    got = [base_id for base_id in asked_valid if base_id in best]
    summary = {
        "valid_main_bases": len(bases),
        "valid_main_by_type": dict(Counter(row["type"] for row in bases)),
        "valid_main_cross": {f"{a}|{b}|{c}": n for (a, b, c), n in sorted(cross.items())},
        "valid_threshold_bases": sum(1 for row in audit if row["condition"] == "C0" and row["valid"] and row.get("subset") == "threshold"),
        "paraphrase_bases_asked": len(todo_ids),
        "paraphrase_bases_passed": sum(1 for base_id in todo_ids if base_id in best),
        "paraphrase_pass_rate": (sum(1 for base_id in todo_ids if base_id in best) / len(todo_ids)) if todo_ids else None,
        "paraphrase_missing": sorted(set(asked_valid) - set(got)),
        "flip_ungrammatical_bases": sum(1 for row in audit if row["condition"] == "C0" and row.get("invalid_reason") == "flip_ungrammatical"),
        "instances_main_valid": len(main_rows),
        "instances_threshold_valid": len(thr_rows),
        "dose_kind_main": dict(Counter(row.get("dose_kind") for row in bases if row["type"] == "DOSE")),
        "flip_mechanism_main": dict(Counter(row.get("flip_mechanism") for row in bases if row["type"] == "POLARITY")),
        "domain_kind_main": dict(Counter(row.get("domain_kind") for row in bases if row["type"] == "POLARITY")),
        "c0_drift_main": sum(1 for row in bases if row.get("c0_drift")),
        "ocr_noise_main": sum(1 for row in bases if row.get("ocr_noise")),
    }
    (OUT / "apply_stats.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in summary if k != "paraphrase_missing"}, indent=2))
    print("missing_paraphrase", len(summary["paraphrase_missing"]))


if __name__ == "__main__":
    main()
