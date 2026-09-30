#!/usr/bin/env python3
"""Score one Lane B pack: cpuverif trio (+ V2a/V3); legacy checkers via cpuverif_legacy job."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lane_b_checker_routing import cpuverif_checkers, legacy_checkers, legacy_downstream_allowed  # noqa: E402
NODE30 = ROOT / "results/raw_node30"
T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
API_CPU = ("v2a_minicheck", "v3_alignscore")


def node30_has(checker_jsonl: str, instance_id: str) -> bool:
    p = NODE30 / checker_jsonl
    if not p.is_file():
        return False
    for line in p.open():
        if not line.strip():
            continue
        if json.loads(line).get("instance_id") == instance_id:
            return True
    return False


def _first_row(path: Path) -> dict | None:
    if not path.is_file():
        return None
    for line in path.open():
        if line.strip():
            return json.loads(line)
    return None


def _single_env_id(path: Path) -> bool:
    ids: set[str] = set()
    for line in path.open():
        if not line.strip():
            continue
        eid = json.loads(line).get("lane_b_env_id")
        if eid:
            ids.add(str(eid))
    return len(ids) <= 1


def pack_complete(outdir: Path, jsonl_name: str, n_inst: int) -> bool:
    out = outdir / jsonl_name
    if not out.is_file():
        return False
    if sum(1 for _ in out.open()) < n_inst:
        return False
    return _single_env_id(out)


def score_cpuverif_checker(cid: str, instances: Path, outdir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
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
        env={**os.environ, "MEDVERIF_LANE_B_ENV_PROFILE": "cpuverif"},
    )


def score_legacy_checker(cid: str, instances: Path, outdir: Path) -> None:
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
            str(instances),
            "--outdir",
            str(outdir),
            "--checker",
            cid,
        ],
        check=True,
        cwd=str(ROOT),
        env={
            **os.environ,
            "MEDVERIF_LANE_B_ENV_PROFILE": "legacy",
            "CUDA_VISIBLE_DEVICES": "",
            "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'analysis'}:{ROOT / 'scripts'}",
        },
    )


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--pack", required=True, help="subdir under results/raw/lane_b/")
    p.add_argument("--instances", type=Path, required=True)
    p.add_argument(
        "--legacy-only",
        action="store_true",
        help="score only legacy-approved checkers in cpuverif_legacy",
    )
    args = p.parse_args()
    outdir = ROOT / "results/raw/lane_b" / args.pack
    outdir.mkdir(parents=True, exist_ok=True)
    n_inst = sum(1 for _ in args.instances.open() if _.strip())
    os.environ["MEDVERIF_SCORE_ENV"] = "hpc"

    manifest = json.loads(T6_MANIFEST.read_text())
    id_to_jsonl = {c["id"]: c["jsonl"] for c in manifest["checkers"]}

    allowed_legacy = legacy_downstream_allowed()

    if args.legacy_only:
        todo = [c for c in legacy_checkers() if c in allowed_legacy]
    else:
        todo = list(cpuverif_checkers())

    for cid in todo:
        jname = id_to_jsonl[cid]
        if pack_complete(outdir, jname, n_inst):
            print(json.dumps({"skip": cid, "reason": "complete"}))
            continue
        if cid in legacy_checkers():
            if cid not in allowed_legacy:
                print(json.dumps({"skip": cid, "reason": "legacy_cal_not_passed"}))
                continue
            score_legacy_checker(cid, args.instances, outdir)
        else:
            score_cpuverif_checker(cid, args.instances, outdir)

    if args.legacy_only:
        print(json.dumps({"pack": args.pack, "legacy": True, "instances": n_inst}))
        return

    sample_ids = []
    for line in args.instances.open():
        if line.strip():
            sample_ids.append(json.loads(line)["instance_id"])
            if len(sample_ids) >= 5:
                break
    for vid in API_CPU:
        out = outdir / f"{vid}.jsonl"
        if out.is_file() and sum(1 for _ in out.open()) >= n_inst:
            continue
        if vid == "v2a_minicheck":
            skip_all = all(node30_has("v2a_minicheck.jsonl", iid) for iid in sample_ids)
        else:
            skip_all = all(node30_has("v3_alignscore.jsonl", iid) for iid in sample_ids)
        if skip_all and sample_ids:
            print(json.dumps({"skip": vid, "reason": "node30_has_sample"}))
            continue
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "src/score_jsonl.py"),
                "--verifier",
                vid,
                "--instances",
                str(args.instances),
                "--out",
                str(out),
            ],
            check=True,
            cwd=str(ROOT),
            env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "MEDVERIF_LANE_B_ENV_PROFILE": "cpuverif"},
        )
    print(json.dumps({"pack": args.pack, "instances": n_inst, "outdir": str(outdir.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
