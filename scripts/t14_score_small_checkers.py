#!/usr/bin/env python3
"""Score T14 pack with small fine-tuned checkers (+ V2a/V3); resume-friendly."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from hf_token_env import sanitize_hf_token_env

sanitize_hf_token_env()

from analyze import read_jsonl  # noqa: E402
from lane_b_checker_routing import legacy_checkers, legacy_downstream_allowed  # noqa: E402
from non_dose_targets import NON_DOSE_TARGET_BASES  # noqa: E402

INST = ROOT / "data/t14/instances_t14.jsonl"
OUT = ROOT / "results/raw/t14"
T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"

T6A_CPU = (
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
)
T6A_LEGACY_GPU = ("t6a_summac_zs",)
T6A_GRANITE_CPU = ("t6a_granite_guardian",)
API_CPU = ("v2a_minicheck", "v3_alignscore")


def n_lines(path: Path) -> int:
    return sum(1 for line in path.open() if line.strip()) if path.is_file() else 0


def _conda_python(env_name: str) -> str:
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.check_output(
        ["conda", "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
        text=True,
        env=clean,
    ).strip()


def pack_complete(out: Path, n_inst: int) -> bool:
    return out.is_file() and n_lines(out) >= n_inst


def filter_rows() -> list[dict]:
    rows = read_jsonl(INST)
    return [
        r
        for r in rows
        if r.get("valid", True)
        and r.get("type") == "DOSE"
        and r.get("base_id") not in NON_DOSE_TARGET_BASES
    ]


def score_t6a(cid: str, pending: Path, *, legacy: bool) -> None:
    legacy_gpu = os.environ.get("MEDVERIF_LEGACY_GPU") == "1"
    if legacy:
        conda = os.environ.get("MEDVERIF_LEGACY_CONDA", "cpuverif_legacy")
        py = _conda_python(conda)
        profile = "legacy"
    else:
        conda = os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif")
        py = _conda_python(conda)
        profile = "cpuverif"
    env = {
        **os.environ,
        "MEDVERIF_LANE_B_ENV_PROFILE": profile,
        "PYTHONPATH": ":".join(
            [
                str(ROOT / ".cache/src/MiniCheck"),
                str(ROOT / "src"),
                str(ROOT / "analysis"),
                str(ROOT / "scripts"),
                str(ROOT / ".cache/src/AlignScore/src"),
            ]
        ),
        "NLTK_DATA": os.environ.get("NLTK_DATA", str(ROOT / ".cache/nltk")),
    }
    if not (legacy and legacy_gpu):
        env["CUDA_VISIBLE_DEVICES"] = ""
    subprocess.run(
        [
            py,
            str(ROOT / "scripts/t6a_score_instances.py"),
            "--instances",
            str(pending),
            "--outdir",
            str(OUT),
            "--checker",
            cid,
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )


def score_api(vid: str, pending: Path) -> None:
    out = OUT / f"{vid}.jsonl"
    conda = os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif")
    py = _conda_python(conda)
    subprocess.run(
        [
            py,
            str(ROOT / "src/score_jsonl.py"),
            "--verifier",
            vid,
            "--instances",
            str(pending),
            "--out",
            str(out),
        ],
        check=True,
        cwd=str(ROOT),
        env={
            **os.environ,
            "CUDA_VISIBLE_DEVICES": "",
            "MEDVERIF_LANE_B_ENV_PROFILE": "cpuverif",
            "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / '.cache/src/MiniCheck'}:{ROOT / '.cache/src/AlignScore/src'}",
        },
    )


def main() -> None:
    rows = filter_rows()
    pending = ROOT / "data/t14/instances_t14_small_checkers_pending.jsonl"
    pending.parent.mkdir(parents=True, exist_ok=True)
    with pending.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    n_inst = len(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    id_to_jsonl = {c["id"]: c["jsonl"] for c in json.loads(T6_MANIFEST.read_text())["checkers"]}
    allowed = legacy_downstream_allowed()

    for cid in T6A_CPU:
        jname = id_to_jsonl[cid]
        if pack_complete(OUT / jname, n_inst):
            print(json.dumps({"skip": cid, "reason": "complete"}))
            continue
        print(json.dumps({"score": cid, "n": n_inst}), flush=True)
        score_t6a(cid, pending, legacy=False)

    for cid in T6A_LEGACY_GPU:
        if cid in legacy_checkers() and cid not in allowed:
            print(json.dumps({"skip": cid, "reason": "legacy_cal_not_passed"}))
            continue
        jname = id_to_jsonl[cid]
        if pack_complete(OUT / jname, n_inst):
            print(json.dumps({"skip": cid, "reason": "complete"}))
            continue
        print(json.dumps({"score": cid, "legacy": True, "n": n_inst}), flush=True)
        os.environ["MEDVERIF_LEGACY_GPU"] = "1"
        score_t6a(cid, pending, legacy=True)

    for cid in T6A_GRANITE_CPU:
        jname = id_to_jsonl[cid]
        if pack_complete(OUT / jname, n_inst):
            print(json.dumps({"skip": cid, "reason": "complete"}))
            continue
        print(json.dumps({"score": cid, "cpuverif_gpu": True, "n": n_inst}), flush=True)
        os.environ["MEDVERIF_LEGACY_GPU"] = "1"
        score_t6a(cid, pending, legacy=False)

    for vid in API_CPU:
        if pack_complete(OUT / f"{vid}.jsonl", n_inst):
            print(json.dumps({"skip": vid, "reason": "complete"}))
            continue
        print(json.dumps({"score": vid, "n": n_inst}), flush=True)
        score_api(vid, pending)

    report = subprocess.run(
        [sys.executable, str(ROOT / "scripts/t14_c0_conditional_report.py")],
        cwd=str(ROOT),
        check=False,
    )
    print(json.dumps({"pending": str(pending), "n_instances": n_inst, "report_rc": report.returncode}))


if __name__ == "__main__":
    main()
