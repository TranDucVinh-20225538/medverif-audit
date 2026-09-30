#!/usr/bin/env python3
"""200-row calibration for cpuverif trio (MiniCheck×2 + AlignScore-base)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lane_b_checker_routing import cpuverif_checkers  # noqa: E402
from lane_b_env import record_lane_b_env  # noqa: E402

CAL_INST = ROOT / "data/lane_b/calibration_200.jsonl"
OUTDIR = ROOT / "results/raw/lane_b/calibration_200"
MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
CPU = cpuverif_checkers()
THRESH = 0.97


def _sub_env() -> dict:
    align = ROOT / ".cache/src/AlignScore/src"
    py_path = f"{ROOT / 'src'}:{ROOT / 'analysis'}:{ROOT / 'scripts'}"
    if align.is_dir():
        py_path = f"{align}:{py_path}"
    return {
        **os.environ,
        "MEDVERIF_LANE_B_ENV_PROFILE": "cpuverif",
        "PYTHONPATH": py_path,
    }


def _single_env_id(path: Path) -> bool:
    ids: set[str] = set()
    for line in path.open():
        if not line.strip():
            continue
        eid = json.loads(line).get("lane_b_env_id")
        if eid:
            ids.add(str(eid))
    return len(ids) <= 1


def calibration_stale(env_id: str) -> bool:
    if not OUTDIR.is_dir():
        return True
    manifest = json.loads(MANIFEST.read_text())
    id_to_jsonl = {c["id"]: c["jsonl"] for c in manifest["checkers"]}
    n_cal = sum(1 for _ in CAL_INST.open() if _.strip())
    for cid in CPU:
        p = OUTDIR / id_to_jsonl[cid]
        if not p.is_file() or sum(1 for _ in p.open()) < n_cal:
            return True
        if not _single_env_id(p):
            return True
    return False


def update_hold(blocked_cpu: list[str]) -> None:
    hold = ROOT / "notes/lane_b_calibration_hold.json"
    env_doc = json.loads((ROOT / "notes/lane_b_env.json").read_text())
    doc = {
        "pause_downstream": bool(blocked_cpu),
        "pause_downstream_cpuverif": bool(blocked_cpu),
        "threshold_agreement": THRESH,
        "blocked_checkers_cpuverif": blocked_cpu,
        "legacy_hold_checkers": [
            "t6a_summac_zs",
            "t6a_summac_conv",
            "t6a_hhem",
            "t6a_granite_guardian",
        ],
        "reason": (
            "cpuverif trio must be ≥97% vs node30; SummaC/HHEM/Granite run in cpuverif_legacy."
        ),
        "lane_b_env_id": env_doc.get("env_id"),
    }
    hold.write_text(json.dumps(doc, indent=2) + "\n")


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--skip-archive", action="store_true")
    p.add_argument(
        "--if-stale",
        action="store_true",
        help="skip rescoring when calibration_200 matches current lane_b_env_id",
    )
    args = p.parse_args()

    os.environ["MEDVERIF_LANE_B_ENV_PROFILE"] = "cpuverif"
    env_doc = record_lane_b_env(reason="calibration_force_rescore")
    if args.if_stale and not calibration_stale(env_doc["env_id"]):
        print(json.dumps({"calibration": "fresh", "env_id": env_doc["env_id"]}))
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/lane_b_calibration_report.py")],
            check=True,
            cwd=str(ROOT),
        )
        report = json.loads((ROOT / "notes/lane_b_calibration_agreement.json").read_text())
        blocked_cpu = [
            r["checker"]
            for r in report.get("checkers", [])
            if r["checker"] in CPU
            and r.get("agreement") is not None
            and r["agreement"] < THRESH
        ]
        update_hold(blocked_cpu)
        if blocked_cpu:
            raise SystemExit(3)
        return

    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not args.skip_archive:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        arch = OUTDIR / f"_archive_pre_{stamp}"
        arch.mkdir(parents=True, exist_ok=True)
        manifest = json.loads(MANIFEST.read_text())
        id_to_jsonl = {c["id"]: c["jsonl"] for c in manifest["checkers"]}
        for cid in CPU:
            f = OUTDIR / id_to_jsonl[cid]
            if f.is_file():
                shutil.move(str(f), str(arch / f.name))
        (arch / "lane_b_env_at_archive.json").write_text(json.dumps(env_doc, indent=2) + "\n")

    for cid in CPU:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/t6a_score_instances.py"),
                "--instances",
                str(CAL_INST),
                "--outdir",
                str(OUTDIR),
                "--checker",
                cid,
                "--force",
            ],
            check=True,
            cwd=str(ROOT),
            env=_sub_env(),
        )

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/lane_b_calibration_report.py")],
        check=True,
        cwd=str(ROOT),
    )
    report = json.loads((ROOT / "notes/lane_b_calibration_agreement.json").read_text())
    blocked_cpu = [
        r["checker"]
        for r in report.get("checkers", [])
        if r["checker"] in CPU
        and r.get("agreement") is not None
        and r["agreement"] < THRESH
    ]
    update_hold(blocked_cpu)
    if blocked_cpu:
        print(json.dumps({"PAUSE_cpuverif": blocked_cpu}, indent=2))
        raise SystemExit(3)
    print(json.dumps({"calibration": "ok", "env_id": env_doc["env_id"]}, indent=2))


if __name__ == "__main__":
    main()
