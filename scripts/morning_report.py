#!/usr/bin/env python3
"""Aggregate overnight status into notes/morning_report.md."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notes" / "morning_report.md"


def read_json(path: Path) -> dict | list | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def read_jsonl_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.open() if line.strip())


def qc_waiting() -> list[str]:
    waiting = []
    for path in sorted((ROOT / "qc").glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "PI_ok" not in reader.fieldnames:
                continue
            empty = sum(1 for row in reader if not (row.get("PI_ok") or "").strip())
            if empty:
                waiting.append(f"`{path.relative_to(ROOT)}` ({empty} rows w/ empty PI_ok)")
    return waiting


def v4_counts() -> dict:
    inst = ROOT / "data/v3/instances_cpu_main.jsonl"
    raw = ROOT / "results/raw/v4_ragas_nli.jsonl"
    n_inst = read_jsonl_count(inst)
    n_raw = read_jsonl_count(raw)
    scored = set()
    if raw.is_file():
        for line in raw.open():
            if line.strip():
                scored.add(json.loads(line)["instance_id"])
    pending = 0
    if inst.is_file():
        for line in inst.open():
            if line.strip():
                iid = json.loads(line)["instance_id"]
                if iid not in scored:
                    pending += 1
    dedupe = read_json(ROOT / "notes/dedupe_v4_ragas_nli.json") or {}
    return {"instances_cpu_main": n_inst, "raw_lines": n_raw, "unique_scored": len(scored), "pending_vs_main": pending, "dedupe": dedupe}


def expand_coverage() -> dict:
    manifest = read_json(ROOT / "notes/score_pending_manifest.json") or {}
    expand_pending = read_jsonl_count(ROOT / "data/expand/instances_score_pending.jsonl")
    return {"score_pending_manifest": manifest, "expand_pending_n": expand_pending}


def run_reports() -> None:
    cmds = [
        [sys.executable, str(ROOT / "scripts/t7_e1_unit_report.py")],
        [sys.executable, str(ROOT / "scripts/t4_eco_report.py")],
        [sys.executable, str(ROOT / "scripts/m1_before_after_report.py")],
        [sys.executable, str(ROOT / "scripts/build_score_pending.py")],
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, cwd=ROOT, check=False, timeout=600)
        except Exception:
            pass


def main() -> None:
    run_reports()
    credit = read_json(ROOT / "notes/openrouter_credit.json") or {}
    t7 = read_json(ROOT / "notes/t7_e1_unit_report.json") or {}
    t4 = read_json(ROOT / "notes/t4_eco_report.json") or {}
    t9m = read_json(ROOT / "data/t9/manifest.json") or {}
    overnight = read_json(ROOT / "notes/overnight_status.json") or {}

    lines = [
        f"# Morning report ({datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M %Z')})",
        "",
        "## Task status",
        "",
        "| Task | Status | Notes |",
        "|---|---|---|",
        f"| T7 E1-unit OR | {overnight.get('t7', 'see tmux/logs')} | `notes/t7_e1_unit_report.md` |",
        f"| T4 eco OR | {overnight.get('t4_eco', 'see tmux/logs')} | `notes/t4_eco_report.md` |",
        f"| V4 main resume | {overnight.get('v4_resume', 'see logs')} | dedupe: `notes/dedupe_v4_ragas_nli.json` |",
        f"| T6-B full | {overnight.get('t6b_full', 'see tmux/logs')} | |",
        f"| Expand OR score | {overnight.get('expand_score', 'see logs')} | v1b/v5 T2: `results/raw/t2_full/` |",
        f"| T9 prep | inputs n={t9m.get('groups', {}).get('all', '?')} | **node30 only** `jobs/run_t9_node30.sh` |",
        f"| T10 prep | {overnight.get('t10', 'conditional')} | HHEM on node30; open HHEM-2.1 framing |",
        "| T8 synthetic | **DEPRECATED** | do not score |",
        "| T8b | **blocked** | `qc/t8_mismatch_check.csv` |",
        "",
        f"**OpenRouter credit remaining:** {credit.get('limit_remaining', 'unknown')}",
        "",
        "## T7 (per verifier)",
        "",
    ]
    if t7.get("verifiers"):
        lines.append("| verifier | E1-unit fail | E1 x2/x10 fail | INV-unit pass |")
        lines.append("|---|---:|---:|---:|")
        for v, row in sorted(t7["verifiers"].items()):
            lines.append(
                f"| {v} | {row.get('e1_unit_fail_rate')} (n={row.get('e1_unit_n_scored')}) | "
                f"{row.get('e1_claim_x2_x10_fail_rate')} (n={row.get('e1_claim_n_scored')}) | "
                f"{row.get('inv_unit_pass_rate')} (n={row.get('inv_unit_n_scored')}) |"
            )
    else:
        lines.append("_Report not ready — run `scripts/t7_e1_unit_report.py`_")
    lines.extend(["", "## T4 eco false alarms (human-labeled correct answers)", ""])
    fa = (t4.get("false_alarm_by_verifier_category") or t4.get("false_alarms") or {})
    if fa:
        lines.append("See `notes/t4_eco_report.md` for full bootstrap CIs.")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(fa, indent=2)[:8000])
        lines.append("```")
    else:
        lines.append("_See `notes/t4_eco_report.md`_")

    lines.extend(["", "## V4 row counts", ""])
    lines.append("```json")
    lines.append(json.dumps(v4_counts(), indent=2))
    lines.append("```")

    lines.extend(["", "## Expand scoring coverage", ""])
    lines.append("```json")
    lines.append(json.dumps(expand_coverage(), indent=2))
    lines.append("```")

    m1_path = ROOT / "results/tables/m1_before_after.md"
    lines.extend(["", "## M1 before/after (4 verifiers)", ""])
    if m1_path.is_file():
        lines.append(f"Full table: `{m1_path.relative_to(ROOT)}`")
    else:
        lines.append("_Run `scripts/m1_before_after_report.py`_")

    lines.extend(["", "## T3", ""])
    t3_inv = read_jsonl_count(ROOT / "data/t3/instances_inv_families.jsonl")
    t3_scored = read_jsonl_count(ROOT / "results/raw/t3_t2/v1b_medscore.jsonl")
    lines.append(f"- INV families instances: **{t3_inv}**; t3_t2 v1b lines: **{t3_scored}**")

    lines.extend(["", "## QC files awaiting PI_ok review", ""])
    for item in qc_waiting():
        lines.append(f"- {item}")

    if overnight.get("budget_stop"):
        lines.extend(["", "## Budget stop", "", overnight["budget_stop"]])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
