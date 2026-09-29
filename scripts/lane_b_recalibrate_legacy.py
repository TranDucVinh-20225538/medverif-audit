#!/usr/bin/env python3
"""200-row calibration for legacy checkers (SummaC×2, HHEM, Granite) in cpuverif_legacy."""

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

from lane_b_checker_routing import legacy_checkers, save_legacy_downstream_allowed  # noqa: E402

CAL_INST = ROOT / "data/lane_b/calibration_200.jsonl"
OUTDIR = ROOT / "results/raw/lane_b/calibration_200"
MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
LEGACY = legacy_checkers()
THRESH = 0.97
CONDA_ENV = os.environ.get("MEDVERIF_LEGACY_CONDA", "cpuverif_legacy")


def legacy_python() -> str:
    return subprocess.check_output(
        ["conda", "run", "-n", CONDA_ENV, "python", "-c", "import sys; print(sys.executable)"],
        text=True,
    ).strip()


def run_legacy(cmd: list[str]) -> None:
    py = legacy_python()
    subprocess.run([py, *cmd], check=True, cwd=str(ROOT), env=_legacy_env())


def _legacy_env() -> dict:
    align = ROOT / ".cache/src/AlignScore/src"
    py_path = f"{ROOT / 'src'}:{ROOT / 'analysis'}:{ROOT / 'scripts'}"
    if align.is_dir():
        py_path = f"{align}:{py_path}"
    return {
        **os.environ,
        "MEDVERIF_LANE_B_ENV_PROFILE": "legacy",
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONPATH": py_path,
        "HF_HOME": os.environ.get("HF_HOME", str(ROOT / ".cache/huggingface")),
        "HUGGINGFACE_HUB_CACHE": os.environ.get(
            "HUGGINGFACE_HUB_CACHE", str(ROOT / ".cache/huggingface/hub")
        ),
    }


def record_legacy_env() -> dict:
    run_legacy([str(ROOT / "scripts/lane_b_record_env.py"), "--legacy", "--reason", "legacy_cal"])
    return json.loads((ROOT / "notes/lane_b_env_legacy.json").read_text())


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--skip-archive", action="store_true")
    args = p.parse_args()

    env_doc = record_legacy_env()
    manifest = json.loads(MANIFEST.read_text())
    id_to_jsonl = {c["id"]: c["jsonl"] for c in manifest["checkers"]}

    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not args.skip_archive:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        arch = OUTDIR / f"_archive_legacy_pre_{stamp}"
        arch.mkdir(parents=True, exist_ok=True)
        for cid in LEGACY:
            f = OUTDIR / id_to_jsonl[cid]
            if f.is_file():
                shutil.move(str(f), str(arch / f.name))
        (arch / "lane_b_env_legacy_at_archive.json").write_text(json.dumps(env_doc, indent=2) + "\n")

    def cpuverif_python() -> str:
        return subprocess.check_output(
            ["conda", "run", "-n", "cpuverif", "python", "-c", "import sys; print(sys.executable)"],
            text=True,
        ).strip()

    for cid in LEGACY:
        cmd = [
            str(ROOT / "scripts/t6a_score_instances.py"),
            "--instances",
            str(CAL_INST),
            "--outdir",
            str(OUTDIR),
            "--checker",
            cid,
            "--force",
        ]
        if cid in ("t6a_hhem", "t6a_granite_guardian"):
            py = cpuverif_python()
            env = {
                **os.environ,
                "MEDVERIF_LANE_B_ENV_PROFILE": "legacy",
                "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'analysis'}:{ROOT / 'scripts'}",
                "HF_HOME": os.environ.get("HF_HOME", str(ROOT / ".cache/huggingface")),
                "HF_TOKEN": (os.environ.get("HF_TOKEN") or "").strip(),
            }
            subprocess.run([py, *cmd], check=True, cwd=str(ROOT), env=env)
        else:
            run_legacy(cmd)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/lane_b_calibration_report.py"),
            "--legacy",
        ],
        check=True,
        cwd=str(ROOT),
    )
    report = json.loads((ROOT / "notes/lane_b_calibration_agreement_legacy.json").read_text())
    allowed = [
        r["checker"]
        for r in report.get("checkers", [])
        if r.get("agreement") is not None and r["agreement"] >= THRESH
    ]
    save_legacy_downstream_allowed(allowed)
    blocked = [c for c in LEGACY if c not in allowed]
    print(
        json.dumps(
            {
                "legacy_calibration": "ok",
                "env_id": env_doc["env_id"],
                "legacy_downstream_allowed": allowed,
                "excluded_from_lane_b_packs": blocked,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
