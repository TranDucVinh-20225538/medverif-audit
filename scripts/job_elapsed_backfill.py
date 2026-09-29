#!/usr/bin/env python3
"""Backfill notes/job_elapsed.json from sacct since a start date."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Heuristic pack/verifier labels for known job names (H11 / cost tables).
JOB_HINTS: dict[str, dict[str, str]] = {
    "medverif-v3": {
        "pack": "data/v3/paraphrase_todo.jsonl (qc_v3)",
        "verifier": "generate_v3 (Qwen2.5-32B + Phi-4)",
    },
    "t19-llama32_1b": {
        "pack": "data/t19/instances_t19.jsonl",
        "verifier": "t19_ragas_local/llama32_1b",
    },
    "t19-llama32_3b": {
        "pack": "data/t19/instances_t19.jsonl",
        "verifier": "t19_ragas_local/llama32_3b",
    },
    "t19-llama31_8b_local": {
        "pack": "data/t19/instances_t19.jsonl",
        "verifier": "t19_ragas_local/llama31_8b_local",
    },
    "t19-report": {"pack": "notes/t19_scale_sweep.md", "verifier": "t19_report"},
    "medverif-s12": {"pack": "stage1/score", "verifier": "mixed"},
    "medverif-v2lab": {"pack": "v2 lab", "verifier": "v2"},
}


def _elapsed_seconds(elapsed: str) -> int | None:
    if not elapsed or elapsed in ("Unknown", "None"):
        return None
    m = re.match(r"(?:(\d+)-)?(\d+):(\d+):(\d+)", elapsed.strip())
    if not m:
        return None
    days, hh, mm, ss = m.groups()
    days = int(days or 0)
    return days * 86400 + int(hh) * 3600 + int(mm) * 60 + int(ss)


def sacct_rows(user: str, start: str) -> list[dict[str, str]]:
    fmt = "JobID,JobName%40,State,Elapsed,Timelimit,Start,End,NodeList,Partition"
    out = subprocess.check_output(
        ["sacct", "-u", user, f"--starttime={start}", "-n", "-P", "--format", fmt],
        text=True,
    )
    rows: list[dict[str, str]] = []
    for line in out.strip().splitlines():
        parts = line.split("|")
        if len(parts) < 9:
            continue
        job_id, name, state, elapsed, _tl, start_t, end_t, node, part = parts[:9]
        if "." in job_id and not job_id.endswith(".batch"):
            continue
        if job_id.endswith(".batch"):
            job_id = job_id.replace(".batch", "")
        if any(r["job_id"] == job_id for r in rows):
            continue
        rows.append(
            {
                "job_id": job_id,
                "job_name": name.strip(),
                "state": state.strip(),
                "wall": elapsed.strip(),
                "started": start_t.strip(),
                "ended": end_t.strip(),
                "node": node.strip(),
                "partition": part.strip(),
            }
        )
    return rows


def main() -> None:
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-09-28"
    user = subprocess.check_output(["id", "-un"], text=True).strip()
    sacct = sacct_rows(user, start)
    record = ROOT / "scripts" / "job_elapsed_record.py"
    for row in sacct:
        hint = JOB_HINTS.get(row["job_name"], {})
        subprocess.run(
            [
                sys.executable,
                str(record),
                "--job-id",
                row["job_id"],
                "--job-name",
                row["job_name"],
                "--state",
                row["state"],
                "--wall",
                row["wall"],
                "--started",
                row["started"],
                "--ended",
                row["ended"],
                "--node",
                row["node"],
                "--partition",
                row["partition"],
                "--pack",
                hint.get("pack", ""),
                "--verifier",
                hint.get("verifier", ""),
                "--skip-gpu-probe",
            ],
            check=False,
        )
    print(json.dumps({"backfill": len(sacct), "since": start}))


if __name__ == "__main__":
    main()
