#!/usr/bin/env python3
"""Rescore Granite in cpuverif; compare to canonical node30 Granite scores (≥95%)."""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import read_jsonl  # noqa: E402
from review_filters import analysis_keep_row  # noqa: E402
from t13_best_of_n_report import score_from_row  # noqa: E402

MAIN = ROOT / "data/v3/instances_main.jsonl"
REFERENCE = ROOT / "results/raw_node30/t6_granite_guardian.jsonl"
T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
OUT = ROOT / "notes/m1_granite_cpuverif_agreement.json"
CID = "t6a_granite_guardian"
N_C0 = 30
N_E1 = 30
SEED = 42
THRESH = 0.95


def _conda_python(env_name: str) -> str:
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.check_output(
        ["conda", "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
        text=True,
        env=clean,
    ).strip()


def score_probe(rows: list[dict], outdir: Path) -> dict[str, dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    inst = outdir / "probe.jsonl"
    with inst.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    py = _conda_python(os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif"))
    env = {
        **os.environ,
        "MEDVERIF_LANE_B_ENV_PROFILE": "cpuverif",
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'analysis'}:{ROOT / 'scripts'}",
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", "0"),
    }
    subprocess.run(
        [
            py,
            str(ROOT / "scripts/t6a_score_instances.py"),
            "--instances",
            str(inst),
            "--outdir",
            str(outdir),
            "--checker",
            CID,
            "--force",
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )
    id_to = {c["id"]: c["jsonl"] for c in json.loads(T6_MANIFEST.read_text())["checkers"]}
    path = outdir / id_to[CID]
    return {r["instance_id"]: r for r in read_jsonl(path)}


def verdict(row: dict) -> str | None:
    score, _ = score_from_row(row)
    if score is None:
        return None
    return "PASS" if score >= 0.5 else "FAIL"


def compare(sample: list[dict], probe: dict[str, dict], existing: dict[str, dict]) -> dict:
    agree = compared = 0
    for row in sample:
        iid = row["instance_id"]
        old = existing.get(iid)
        new = probe.get(iid)
        if not old or not new:
            continue
        vo, vn = verdict(old), verdict(new)
        if vo is None or vn is None:
            continue
        compared += 1
        if vo == vn:
            agree += 1
    rate = agree / compared if compared else 0.0
    return {"n_sample": len(sample), "n_compared": compared, "verdict_agreement": rate}


def main() -> None:
    rows = [
        r
        for r in read_jsonl(MAIN)
        if r.get("valid", True)
        and analysis_keep_row(r)
        and r.get("type") == "DOSE"
        and r.get("subset") == "main"
    ]
    existing = {r["instance_id"]: r for r in read_jsonl(REFERENCE)}
    c0 = [r for r in rows if r.get("condition") == "C0" and r["instance_id"] in existing]
    e1 = [r for r in rows if str(r.get("condition", "")).startswith("E1") and r["instance_id"] in existing]
    rng = random.Random(SEED)
    sample_c0 = rng.sample(c0, min(N_C0, len(c0)))
    sample_e1 = rng.sample(e1, min(N_E1, len(e1)))
    sample = sample_c0 + sample_e1

    with tempfile.TemporaryDirectory(prefix="granite_probe_") as tmp:
        probe = score_probe(sample, Path(tmp))

    c0_stat = compare(sample_c0, probe, existing)
    e1_stat = compare(sample_e1, probe, existing)
    all_agree = c0_stat.get("n_compared", 0) + e1_stat.get("n_compared", 0)
    all_match = int(
        c0_stat["verdict_agreement"] * c0_stat["n_compared"]
        + e1_stat["verdict_agreement"] * e1_stat["n_compared"]
    )
    overall = all_match / all_agree if all_agree else 0.0
    ok = (
        overall >= THRESH
        and c0_stat["n_compared"] >= 20
        and e1_stat["n_compared"] >= 20
        and c0_stat["verdict_agreement"] >= THRESH
        and e1_stat["verdict_agreement"] >= THRESH
    )
    payload = {
        "checker": CID,
        "env": "cpuverif",
        "reference_scores": str(REFERENCE.relative_to(ROOT)),
        "threshold": THRESH,
        "overall_verdict_agreement": overall,
        "pass": ok,
        "c0_probe": c0_stat,
        "e1_probe": e1_stat,
        "na_reason": None
        if ok
        else "Granite cpuverif vs canonical scores <95% or insufficient probes (legacy KeyError granite in cpuverif_legacy)",
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
