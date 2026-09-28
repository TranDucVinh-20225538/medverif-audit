#!/usr/bin/env python3
"""T4c: PI-labeled human-correct eco answers → sentence-level claim, evidence unchanged."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from non_dose_targets import NON_DOSE_TARGET_BASES  # noqa: E402
from t4_eco_compare import apply_pi_override, load_pi_label_paths  # noqa: E402
from t4c_sentence_claim import extract_claim_sentence  # noqa: E402

CLASSIFIED = ROOT / "data/t4/eco_classified.jsonl"
DEV_LABELS = ROOT / "qc/eco_PI_ok_labels.csv"
HELD_LABELS = ROOT / "qc/eco2_PI_ok_labels.csv"
OUT = ROOT / "data/t4/eco_instances_t4c.jsonl"
MANIFEST = ROOT / "data/t4/manifest_t4c.json"

EXCLUDE = {
    ("D0122__eco", "deepseek_chat"),
    ("D0077__eco", "command_r"),
}
CORRECT_CATS = frozenset(
    {"exact_verbatim", "exact_surface_variant", "frequency_rephrased"}
)


def instance_key(row: dict) -> tuple[str, str]:
    return (row["task_id"], row["answerer_id"])


def final_category(row: dict, labels: dict) -> str:
    cat = row.get("eco_category") or ""
    return apply_pi_override(row["task_id"], row["answerer_id"], cat, labels)


def main() -> None:
    labels = load_pi_label_paths([DEV_LABELS, HELD_LABELS])
    labeled_keys = set(labels.keys())
    rows_out = []
    rules = {}
    for line in CLASSIFIED.open():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("base_id") in NON_DOSE_TARGET_BASES:
            continue
        key = instance_key(row)
        if key not in labeled_keys or key in EXCLUDE:
            continue
        cat = final_category(row, labels)
        if cat not in CORRECT_CATS:
            continue
        claim, rule = extract_claim_sentence(
            row.get("answer") or "",
            row.get("target_span_claim") or "",
        )
        rules[rule] = rules.get(rule, 0) + 1
        iid = f"{row['task_id']}__{row['answerer_id']}__eco_t4c"
        rows_out.append(
            {
                "instance_id": iid,
                "base_id": row["base_id"],
                "type": "DOSE",
                "condition": "ECO-answer-t4c",
                "magnitude": cat,
                "eco_category_final": cat,
                "claim": claim,
                "evidence": row["evidence"],
                "expected_verdict": "PASS",
                "claim_span": row.get("target_span_claim"),
                "evidence_span": row.get("target_span_evidence"),
                "claim_c0": row.get("claim_c0"),
                "evidence_c0": row["evidence"],
                "answer_full": row.get("answer"),
                "t4c_rule": rule,
                "answerer_id": row["answerer_id"],
                "openrouter_model": row.get("openrouter_model"),
                "valid": True,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows_out) + "\n")
    manifest = {
        "task": "T4c sentence-level claim on PI-labeled correct eco answers",
        "instances": str(OUT.relative_to(ROOT)),
        "n": len(rows_out),
        "rules": rules,
        "node30_job": "jobs/run_t4c_eco_node30.sh",
        "hpc_job": "jobs/run_t4c_eco_hpc.sh",
        "raw_dir": "results/raw/t4c_eco",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
