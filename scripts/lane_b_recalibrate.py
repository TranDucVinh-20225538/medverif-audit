#!/usr/bin/env python3
"""Force 200-row calibration for all 7 T6-A checkers in current cpuverif env."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lane_b_env import record_lane_b_env  # noqa: E402

CAL_INST = ROOT / "data/lane_b/calibration_200.jsonl"
OUTDIR = ROOT / "results/raw/lane_b/calibration_200"
MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
CPU = [
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
    "t6a_summac_zs",
    "t6a_summac_conv",
    "t6a_hhem",
    "t6a_granite_guardian",
]


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
        first = next((json.loads(l) for l in p.open() if l.strip()), None)
        if not first or first.get("lane_b_env_id") != env_id:
            return True
    return False


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

    env_doc = record_lane_b_env(reason="calibration_force_rescore")
    if args.if_stale and not calibration_stale(env_doc["env_id"]):
        print(json.dumps({"calibration": "fresh", "env_id": env_doc["env_id"]}))
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/lane_b_calibration_report.py")],
            check=True,
            cwd=str(ROOT),
        )
        report = json.loads((ROOT / "notes/lane_b_calibration_agreement.json").read_text())
        blocked = [
            r["checker"]
            for r in report.get("checkers", [])
            if r.get("agreement") is not None and r["agreement"] < 0.97
        ]
        if blocked:
            raise SystemExit(3)
        return
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not args.skip_archive:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        arch = OUTDIR / f"_archive_pre_{stamp}"
        arch.mkdir(parents=True, exist_ok=True)
        for f in OUTDIR.glob("t6_*.jsonl"):
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
        )

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/lane_b_calibration_report.py")],
        check=True,
        cwd=str(ROOT),
    )
    hold = ROOT / "notes/lane_b_calibration_hold.json"
    report = json.loads((ROOT / "notes/lane_b_calibration_agreement.json").read_text())
    blocked = [
        r["checker"]
        for r in report.get("checkers", [])
        if r.get("agreement") is not None and r["agreement"] < 0.97
    ]
    if blocked:
        hold.write_text(
            json.dumps(
                {
                    "pause_downstream": True,
                    "threshold": 0.97,
                    "blocked_checkers": blocked,
                    "env_id": env_doc["env_id"],
                },
                indent=2,
            )
            + "\n"
        )
        print(json.dumps({"PAUSE": blocked}, indent=2))
        raise SystemExit(3)
    if hold.is_file():
        hold.unlink()
    print(json.dumps({"calibration": "ok", "env_id": env_doc["env_id"]}, indent=2))


if __name__ == "__main__":
    main()
