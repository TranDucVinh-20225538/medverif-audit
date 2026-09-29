#!/usr/bin/env python3
"""Drop expanded DOSE cohort from analysis after human spot-check gate (<85% Y)."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

V3 = ROOT / "data/expand/v3"
EXPAND = ROOT / "data/expand"
AUDIT = V3 / "instances_audit.jsonl"
GATE_REASON = "expand_dose_spotcheck_fail"
GATE_THRESHOLD = 0.85


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")


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


def apply_exclusion(audit: list[dict]) -> tuple[list[dict], int]:
    n = 0
    out = []
    for row in audit:
        r = dict(row)
        if r.get("type") == "DOSE":
            r["valid"] = False
            r["invalid_reason"] = GATE_REASON
            n += 1
        out.append(r)
    return out, n


def main() -> None:
    audit = read_jsonl(AUDIT)
    if not audit:
        raise SystemExit(f"missing audit: {AUDIT}")
    audit, n_marked = apply_exclusion(audit)
    stats = refresh_main_outputs(audit)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/expand/build_expand_scoring_packs.py")],
        check=True,
        cwd=str(ROOT),
    )
    manifest = {
        "gate_threshold_pct": int(GATE_THRESHOLD * 100),
        "invalid_reason": GATE_REASON,
        "expand_dose_instances_marked_invalid": n_marked,
        **stats,
    }
    out = ROOT / "notes/expand_dose_spotcheck_gate.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
