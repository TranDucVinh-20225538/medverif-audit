#!/usr/bin/env python3
"""Append/update one Slurm job record and refresh notes/batch_oct_status job table."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "notes" / "job_elapsed.json"
STATUS_PATH = ROOT / "notes" / "batch_oct_status.md"
MARKER = "<!-- job-elapsed-table -->"


def _sacct_field(job_id: str, field: str) -> str:
    try:
        out = subprocess.check_output(
            [
                "sacct",
                "-j",
                job_id,
                "-n",
                "-P",
                "--format",
                f"JobID,{field}",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    for line in out.strip().splitlines():
        if line.startswith(f"{job_id}|"):
            parts = line.split("|", 1)
            return parts[1] if len(parts) > 1 else ""
        if line.startswith(f"{job_id}.batch|"):
            continue
    return ""


def _gpu_type(node: str) -> str:
    node = (node or "").split(",")[0].strip("[]")
    if not node or node.startswith("("):
        return ""
    try:
        out = subprocess.check_output(
            ["srun", "-w", node, "--overlap", "nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=45,
        )
        return out.strip().split("\n")[0].strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _elapsed_seconds(elapsed: str) -> int | None:
    if not elapsed or elapsed in ("Unknown", "None"):
        return None
    m = re.match(r"(?:(\d+)-)?(\d+):(\d+):(\d+)", elapsed.strip())
    if not m:
        return None
    days, hh, mm, ss = m.groups()
    days = int(days or 0)
    return days * 86400 + int(hh) * 3600 + int(mm) * 60 + int(ss)


def load_store() -> dict:
    if JSON_PATH.exists():
        return json.loads(JSON_PATH.read_text())
    return {"updated": None, "jobs": []}


def save_store(store: dict) -> None:
    store["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n")
    refresh_status_md(store)


def refresh_status_md(store: dict) -> None:
    jobs = store.get("jobs", [])

    def _rank(j: dict) -> tuple:
        name = j.get("job_name") or ""
        pri = 0 if name.startswith(("medverif", "t19-")) else 1
        t = j.get("ended") or j.get("started") or ""
        return (pri, t)

    jobs = sorted(jobs, key=_rank, reverse=True)
    rows = jobs[:12]
    lines = [
        MARKER,
        "",
        "## Job wall times (auto)",
        "",
        "| JobID | Name | Pack / task | Verifier | Rows | Wall | GPU | State |",
        "|------:|------|-------------|----------|-----:|------|-----|-------|",
    ]
    for j in rows:
        lines.append(
            "| {job_id} | {job_name} | {pack} | {verifier} | {n_rows} | {wall} | {gpu} | {state} |".format(
                job_id=j.get("job_id", ""),
                job_name=j.get("job_name", ""),
                pack=(j.get("pack") or "—")[:40],
                verifier=(j.get("verifier") or "—")[:28],
                n_rows=j.get("n_rows") if j.get("n_rows") is not None else "",
                wall=j.get("wall") or "—",
                gpu=(j.get("gpu_type") or "—")[:24],
                state=j.get("state") or "",
            )
        )
    lines.append("")
    block = "\n".join(lines)
    if STATUS_PATH.exists():
        text = STATUS_PATH.read_text()
        if MARKER in text:
            head = text.split(MARKER)[0].rstrip()
            STATUS_PATH.write_text(head + "\n\n" + block + "\n")
        else:
            STATUS_PATH.write_text(text.rstrip() + "\n\n" + block + "\n")
    else:
        STATUS_PATH.write_text("# Batch Oct status (HPC)\n\n" + block + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--job-id", required=True)
    p.add_argument("--job-name", default="")
    p.add_argument("--partition", default="")
    p.add_argument("--node", default="")
    p.add_argument("--pack", default="")
    p.add_argument("--verifier", default="")
    p.add_argument("--machine", default="hpc")
    p.add_argument("--n-rows", default="")
    p.add_argument("--started", default="")
    p.add_argument("--api-usd", default="")
    p.add_argument("--state", default="")
    p.add_argument("--wall", default="")
    p.add_argument("--ended", default="")
    p.add_argument("--gpu-type", default="")
    p.add_argument("--skip-gpu-probe", action="store_true")
    args = p.parse_args()

    state = args.state or _sacct_field(args.job_id, "State") or "UNKNOWN"
    wall = args.wall or _sacct_field(args.job_id, "Elapsed") or ""
    ended = args.ended or _sacct_field(args.job_id, "End") or ""
    started = args.started or _sacct_field(args.job_id, "Start") or ""
    node = args.node or _sacct_field(args.job_id, "NodeList") or ""
    gpu = args.gpu_type
    if not gpu and not args.skip_gpu_probe:
        gpu = _gpu_type(node)

    n_rows: int | None = None
    if str(args.n_rows).strip().isdigit():
        n_rows = int(args.n_rows)

    api = args.api_usd.strip()
    api_f: float | None = float(api) if api else None

    rec = {
        "job_id": str(args.job_id),
        "job_name": args.job_name,
        "machine": args.machine,
        "partition": args.partition,
        "node": node,
        "pack": args.pack or None,
        "verifier": args.verifier or None,
        "n_rows": n_rows,
        "wall": wall or None,
        "wall_s": _elapsed_seconds(wall),
        "gpu_type": gpu or None,
        "api_spend_usd": api_f,
        "state": state.split()[0] if state else None,
        "started": started or None,
        "ended": ended or None,
    }

    store = load_store()
    jobs = [j for j in store.get("jobs", []) if str(j.get("job_id")) != str(args.job_id)]
    jobs.append(rec)
    store["jobs"] = jobs
    save_store(store)
    print(json.dumps({"recorded": rec["job_id"], "wall": rec["wall"], "state": rec["state"]}))


if __name__ == "__main__":
    main()
