#!/usr/bin/env python3
"""Score missing M1-strong packs: NS (main×10 + T17÷10), M1 US_up, T17 unit-down."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from hf_token_env import sanitize_hf_token_env

sanitize_hf_token_env()

from analyze import read_jsonl  # noqa: E402
from lane_b_checker_routing import cpuverif_checkers, legacy_checkers, legacy_downstream_allowed  # noqa: E402
from review_filters import analysis_keep_row, flip_pi_ok_bases, inv_pi_ok_keys  # noqa: E402

T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
NS_INST = ROOT / "data/lane_b/m1_strong_ns.jsonl"
PACKS = (
    ("m1_strong_ns", NS_INST),
    ("m1_t7_e1_unit", ROOT / "data/lane_b/m1_t7_e1_unit.jsonl"),
    ("t17_downdose", ROOT / "data/v3/t17_downdose.jsonl"),
)
LEGACY_TARGET = ("t6a_summac_zs", "t6a_granite_guardian")
PRIMARY_CPU = (
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
    "t6a_summac_zs",
    "t6a_granite_guardian",
)

_FLIP = flip_pi_ok_bases()
_INV = inv_pi_ok_keys()


def n_lines(path: Path) -> int:
    return sum(1 for line in path.open() if line.strip())


def build_ns_instances() -> None:
    rows: list[dict] = []
    for path, pred in (
        (ROOT / "data/v3/instances_main.jsonl", lambda r: r.get("condition") in ("E1-claim", "E1-evid") and r.get("magnitude") == "x10"),
        (ROOT / "data/v3/t17_downdose.jsonl", lambda r: r.get("condition") == "E1-down10"),
    ):
        for r in read_jsonl(path):
            if not r.get("valid", True):
                continue
            if not analysis_keep_row(r, flip_y=_FLIP, inv_keys=_INV):
                continue
            if pred(r):
                rows.append(r)
    NS_INST.parent.mkdir(parents=True, exist_ok=True)
    with NS_INST.open("w") as handle:
        for r in rows:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"built_ns_pack": str(NS_INST), "n": len(rows)}))


def pack_complete(outdir: Path, jsonl_name: str, n_inst: int) -> bool:
    out = outdir / jsonl_name
    return out.is_file() and n_lines(out) >= n_inst


def _subprocess_env() -> dict[str, str]:
    env = {**os.environ}
    for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
        if env.get(key):
            env[key] = str(env[key]).strip()
    return env


def score_checker(cid: str, instances: Path, outdir: Path, *, legacy: bool) -> None:
    legacy_gpu = os.environ.get("MEDVERIF_LEGACY_GPU") == "1"
    if legacy:
        conda = os.environ.get("MEDVERIF_LEGACY_CONDA", "cpuverif_legacy")
        clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        py_path = subprocess.check_output(
            ["conda", "run", "-n", conda, "python", "-c", "import sys; print(sys.executable)"],
            text=True,
            env=clean,
        ).strip()
        profile = "legacy"
    else:
        py_path = sys.executable
        profile = "cpuverif"
    run_env = {
        **_subprocess_env(),
        "MEDVERIF_LANE_B_ENV_PROFILE": profile,
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'analysis'}:{ROOT / 'scripts'}",
    }
    if not (legacy and legacy_gpu):
        run_env["CUDA_VISIBLE_DEVICES"] = ""
    subprocess.run(
        [
            py_path,
            str(ROOT / "scripts/t6a_score_instances.py"),
            "--instances",
            str(instances),
            "--outdir",
            str(outdir),
            "--checker",
            cid,
        ],
        check=True,
        cwd=str(ROOT),
        env=run_env,
    )


def main() -> None:
    legacy_only = os.environ.get("MEDVERIF_LEGACY_ONLY") == "1"
    if not legacy_only:
        build_ns_instances()
    id_to_jsonl = {c["id"]: c["jsonl"] for c in json.loads(T6_MANIFEST.read_text())["checkers"]}
    allowed_legacy = legacy_downstream_allowed()
    cpu = set(cpuverif_checkers())

    for pack, inst in PACKS:
        if legacy_only and pack == "m1_strong_ns":
            continue
        if not inst.is_file():
            print(json.dumps({"skip_pack": pack, "reason": "missing instances"}))
            continue
        n_inst = n_lines(inst)
        outdir = ROOT / "results/raw/lane_b" / pack
        outdir.mkdir(parents=True, exist_ok=True)
        if pack == "m1_strong_ns":
            todo = [c for c in PRIMARY_CPU if c in cpu or c in legacy_checkers()]
        elif pack in ("m1_t7_e1_unit", "t17_downdose"):
            todo = [c for c in LEGACY_TARGET if c in legacy_checkers() and c in allowed_legacy]
        else:
            todo = []
        for cid in todo:
            if cid in LEGACY_TARGET and cid not in allowed_legacy:
                continue
            jname = id_to_jsonl[cid]
            if pack_complete(outdir, jname, n_inst):
                print(json.dumps({"skip": cid, "pack": pack, "reason": "complete"}))
                continue
            print(json.dumps({"score": cid, "pack": pack, "instances": n_inst}), flush=True)
            try:
                use_legacy = cid in legacy_checkers() and cid != "t6a_granite_guardian"
                score_checker(cid, inst, outdir, legacy=use_legacy)
            except subprocess.CalledProcessError as exc:
                print(json.dumps({"error": cid, "pack": pack, "exit": exc.returncode}))


if __name__ == "__main__":
    main()
