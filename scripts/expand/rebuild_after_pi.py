#!/usr/bin/env python3
"""Re-run expand QC v3 (main-parity), apply PI dose/unit overrides, refresh review packs."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from non_dose_targets import invalidate_non_dose_row  # noqa: E402

DOSE_LABELS = ROOT / "qc/dose_PI_ok_labels.csv"
EXPAND_UNIT = ROOT / "qc/expand_unit_natural.csv"
V3 = ROOT / "data/expand/v3"
EXPAND = ROOT / "data/expand"

# PI: no drug name in claim or evidence → still accept C0 (6 bases).
DOSE_C0_NO_DRUG_OK = frozenset({"D0002", "D0077", "D0081", "D0333", "D0351", "D0372"})


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")


def dose_pi_map() -> dict[str, str]:
    out: dict[str, str] = {}
    with DOSE_LABELS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            bid = row["base_id"]
            pi = (row.get("PI_ok") or "").strip()
            if bid in DOSE_C0_NO_DRUG_OK:
                pi = "Y"
            if pi in {"Y", "N"}:
                out[bid] = pi
    return out


def apply_dose_and_non_dose(audit: list[dict], dose_pi: dict[str, str]) -> list[dict]:
    out = []
    for row in audit:
        r = dict(row)
        bid = r.get("base_id") or ""
        invalidate_non_dose_row(r)
        pi = dose_pi.get(bid)
        if pi == "N" and r.get("type") == "DOSE":
            r["valid"] = False
            r["invalid_reason"] = r.get("invalid_reason") or "human_dose_pi_n"
        elif pi == "Y" and r.get("invalid_reason") == "human_dose_pi_n":
            r["valid"] = True
            r["invalid_reason"] = None
        out.append(r)
    return out


def refresh_main_outputs(audit: list[dict]) -> dict:
    main_rows = [r for r in audit if r.get("valid") and r.get("subset") == "main"]
    thr_rows = [r for r in audit if r.get("valid") and r.get("subset") == "threshold"]
    range_rows = [r for r in audit if r.get("valid") and r.get("subset") == "range"]
    write_jsonl(V3 / "instances_audit.jsonl", audit)
    write_jsonl(EXPAND / "instances_main.jsonl", main_rows)
    write_jsonl(V3 / "instances_main.jsonl", main_rows)
    write_jsonl(V3 / "instances_threshold.jsonl", thr_rows)
    write_jsonl(V3 / "instances_range.jsonl", range_rows)
    cpu_early = [r for r in main_rows + thr_rows if r.get("magnitude") != "paraphrase"]
    write_jsonl(EXPAND / "instances_cpu_early.jsonl", cpu_early)
    write_jsonl(V3 / "instances_cpu_early.jsonl", cpu_early)
    kept = {r["base_id"] for r in main_rows if r.get("condition") == "C0"}
    bases = [b for b in read_jsonl(EXPAND / "bases_main.jsonl") if b["id"] in kept]
    write_jsonl(EXPAND / "bases_main.jsonl", bases)
    by_type = Counter(b["type"] for b in bases)
    return {
        "bases_main": len(bases),
        "bases_by_type": dict(by_type),
        "instances_main_valid": len(main_rows),
        "instances_threshold_valid": len(thr_rows),
        "instances_range_valid": len(range_rows),
        "cpu_early": len(cpu_early),
    }


def main() -> None:
    os.environ["MEDVERIF_QC_V3_EXPAND"] = "1"
    if not (V3 / "instances_audit.jsonl").is_file():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/expand/prepare_expand_v3.py")],
            check=True,
            cwd=str(ROOT),
        )
    env = os.environ.copy()
    env.setdefault("MEDVERIF_QC_V3_RESET_PARA", "1")
    subprocess.run(
        [sys.executable, str(ROOT / "src/apply_qc_v3_decisions.py")],
        check=True,
        cwd=str(ROOT),
        env=env,
    )
    audit = read_jsonl(V3 / "instances_audit.jsonl")
    audit = apply_dose_and_non_dose(audit, dose_pi_map())
    stats = refresh_main_outputs(audit)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/expand/build_expand_scoring_packs.py"),
        ],
        check=True,
        cwd=str(ROOT),
    )
    seed = os.environ.get("MEDVERIF_EXPAND_DOSE_SAMPLE_SEED", "20260930")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/expand/build_review_packs.py"),
            "--seed",
            seed,
        ],
        check=True,
        cwd=str(ROOT),
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/report_unit_inv_counts.py"), "--expand"],
        check=False,
        cwd=str(ROOT),
    )
    stats["dose_pi_labeled"] = len(dose_pi_map())
    stats["analysis_gate"] = (
        "Expanded DOSE excluded: dose2 spot-check 34/54 Y (63%) < 85% gate "
        "(qc/dose2_PI_ok_labels.csv). POL expand pending qc/expand_pol_flips.csv PI_ok=Y."
    )
    out = ROOT / "notes/expand_rebuild_after_pi.json"
    out.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
