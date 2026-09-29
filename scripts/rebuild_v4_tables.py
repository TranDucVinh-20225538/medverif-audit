#!/usr/bin/env python3
"""Rebuild headline tables/reports that consume V4 scores."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [sys.executable, str(ROOT / "scripts/build_cpu_prelim.py")],
    [sys.executable, str(ROOT / "scripts/dose3_robustness_report.py")],
    [sys.executable, str(ROOT / "scripts/t7_e1_unit_report.py")],
    [sys.executable, str(ROOT / "scripts/build_polarity_all_verifiers.py")],
    [sys.executable, str(ROOT / "scripts/t4_eco_report.py")],
    [sys.executable, str(ROOT / "scripts/t4c_eco_report.py")],
    [sys.executable, str(ROOT / "scripts/m1_before_after_report.py")],
    [
        sys.executable,
        str(ROOT / "analysis/analyze.py"),
        "--instances",
        str(ROOT / "data/v3/instances_cpu_early.jsonl"),
        "--verdicts",
        str(ROOT / "results/raw"),
        "--outdir",
        str(ROOT / "results/tables/stage4_cpu_early"),
    ],
]


def main() -> None:
    failed = []
    for cmd in COMMANDS:
        if not Path(cmd[-1] if "analyze" in cmd[1] else cmd[1]).parent.exists() and cmd[1].endswith(".py"):
            if not Path(cmd[1]).is_file():
                continue
        print("RUN", " ".join(cmd), flush=True)
        rc = subprocess.call(cmd, cwd=ROOT)
        if rc != 0:
            failed.append((cmd, rc))
    print({"rebuilt": len(COMMANDS) - len(failed), "failed": len(failed)})


if __name__ == "__main__":
    main()
