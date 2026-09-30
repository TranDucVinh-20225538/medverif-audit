#!/usr/bin/env python3
"""Score filtered main_ext with Lane B CPU/GPU checkers (not OpenRouter judges)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

INST = ROOT / "data/main_ext/instances_main_ext.jsonl"
OUT = ROOT / "results/raw/main_ext"
MANIFEST = ROOT / "notes/t6a_eco_checkers.json"

CPU_T6 = (
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
)
LEGACY_T6 = ("t6a_summac_zs", "t6a_granite_guardian")
SCORE_JSONL = (
    ("v3_alignscore", "v3_alignscore.jsonl"),
    ("t15_minicheck_roberta", "t15_minicheck_roberta.jsonl"),
)


def n_valid(path: Path) -> int:
    return sum(1 for line in path.open() if line.strip() and json.loads(line).get("valid", True))


def run_t6(checker: str, legacy: bool) -> None:
    env = {
        **os.environ,
        "MEDVERIF_ROOT": str(ROOT),
        "MEDVERIF_SCORE_ENV": "hpc",
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'analysis'}:{ROOT / 'scripts'}",
        "HF_HOME": str(ROOT / ".cache/huggingface"),
    }
    if not legacy:
        env["MEDVERIF_LANE_B_ENV_PROFILE"] = "cpuverif"
        env["ALIGNScore_SRC"] = str(ROOT / ".cache/src/AlignScore/src")
        env["PYTHONPATH"] = f"{env['ALIGNScore_SRC']}:{env['PYTHONPATH']}"
    else:
        conda = os.environ.get("MEDVERIF_LEGACY_CONDA", "cpuverif_legacy")
        py = subprocess.check_output(
            ["conda", "run", "-n", conda, "python", "-c", "import sys; print(sys.executable)"],
            text=True,
        ).strip()
        subprocess.run(
            [
                py,
                str(ROOT / "scripts/t6a_score_instances.py"),
                "--instances",
                str(INST),
                "--outdir",
                str(OUT),
                "--checker",
                checker,
            ],
            check=True,
            cwd=str(ROOT),
            env={**env, "MEDVERIF_LANE_B_ENV_PROFILE": "legacy"},
        )
        return
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/t6a_score_instances.py"),
            "--instances",
            str(INST),
            "--outdir",
            str(OUT),
            "--checker",
            checker,
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )


def run_score_jsonl(verifier: str, out_name: str, *, gpu: bool) -> None:
    env = {
        **os.environ,
        "MEDVERIF_SCORE_ENV": "hpc",
        "PYTHONPATH": str(ROOT / "src"),
        "HF_HOME": str(ROOT / ".cache/huggingface"),
    }
    if not gpu:
        env["CUDA_VISIBLE_DEVICES"] = ""
    out = OUT / out_name
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/score_jsonl.py"),
            "--verifier",
            verifier,
            "--instances",
            str(INST),
            "--out",
            str(out),
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = n_valid(INST)
    print(json.dumps({"main_ext_checkers": "start", "valid_instances": n}), flush=True)
    for cid in CPU_T6:
        print(json.dumps({"checker": cid}), flush=True)
        run_t6(cid, legacy=False)
    for cid in LEGACY_T6:
        print(json.dumps({"checker": cid, "legacy": True}), flush=True)
        run_t6(cid, legacy=True)
    run_score_jsonl("v3_alignscore", "v3_alignscore.jsonl", gpu=False)
    run_score_jsonl("t15_minicheck_roberta", "t15_minicheck_roberta.jsonl", gpu=False)
    print(json.dumps({"main_ext_checkers": "done", "outdir": str(OUT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
