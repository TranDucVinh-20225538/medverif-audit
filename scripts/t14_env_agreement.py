#!/usr/bin/env python3
"""Rescore 30 main C0 instances per T14 checker env; compare to existing main scores."""

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
import t13_best_of_n_report as t13  # noqa: E402
from t13_best_of_n_report import merged_score_rows, score_from_row  # noqa: E402

# Same set as t14_score_small_checkers.py
CHECKERS: tuple[tuple[str, bool], ...] = (
    ("t6a_minicheck_roberta", False),
    ("t6a_minicheck_deberta", False),
    ("t6a_alignscore_base", False),
    ("v2a_minicheck", False),
    ("v3_alignscore", False),
    ("t6a_summac_zs", True),
    ("t6a_granite_guardian", False),
)

T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
MAIN = ROOT / "data/v3/instances_main.jsonl"
N_PROBE = 30
SEED = 42
THRESH = 0.95


def _conda_python(env_name: str) -> str:
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.check_output(
        ["conda", "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
        text=True,
        env=clean,
    ).strip()


def t14_score_env(cid: str, *, legacy: bool) -> tuple[str, dict]:
    if legacy:
        py = _conda_python(os.environ.get("MEDVERIF_LEGACY_CONDA", "cpuverif_legacy"))
        profile = "legacy"
        legacy_gpu = os.environ.get("MEDVERIF_LEGACY_GPU") == "1"
    else:
        py = _conda_python(os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif"))
        profile = "cpuverif"
        legacy_gpu = False
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
    return py, env


def verdict_from_row(row: dict) -> str | None:
    score, _ = score_from_row(row)
    if score is None:
        return None
    return "PASS" if score >= 0.5 else "FAIL"


def score_probe(cid: str, legacy: bool, rows: list[dict], outdir: Path) -> dict[str, dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    inst = outdir / "probe_c0.jsonl"
    with inst.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    py, env = t14_score_env(cid, legacy=legacy)
    if cid in ("v2a_minicheck", "v3_alignscore"):
        out = outdir / f"{cid}.jsonl"
        subprocess.run(
            [py, str(ROOT / "src/score_jsonl.py"), "--verifier", cid, "--instances", str(inst), "--out", str(out)],
            check=True,
            cwd=str(ROOT),
            env=env,
        )
        path = out
    else:
        subprocess.run(
            [
                py,
                str(ROOT / "scripts/t6a_score_instances.py"),
                "--instances",
                str(inst),
                "--outdir",
                str(outdir),
                "--checker",
                cid,
                "--force",
            ],
            check=True,
            cwd=str(ROOT),
            env=env,
        )
        id_to_jsonl = {c["id"]: c["jsonl"] for c in json.loads(T6_MANIFEST.read_text())["checkers"]}
        path = outdir / id_to_jsonl[cid]
    return {r["instance_id"]: r for r in read_jsonl(path)}


def main() -> None:
    c0_rows = [r for r in read_jsonl(MAIN) if r.get("valid", True) and r.get("condition") == "C0" and r.get("type") == "DOSE"]
    rng = random.Random(SEED)
    sample = rng.sample(c0_rows, min(N_PROBE, len(c0_rows)))
    results: list[dict] = []
    failed_any = False
    with tempfile.TemporaryDirectory(prefix="t14_env_probe_") as tmp:
        probe_root = Path(tmp)
        for cid, legacy in CHECKERS:
            existing = merged_score_rows(cid)
            probe = score_probe(cid, legacy, sample, probe_root / cid)
            agree = 0
            compared = 0
            dscores: list[float] = []
            missing_main = 0
            for row in sample:
                iid = row["instance_id"]
                old = existing.get(iid)
                new = probe.get(iid)
                if not old:
                    missing_main += 1
                    continue
                vo = verdict_from_row(old)
                vn = verdict_from_row(new)
                if vo is None or vn is None:
                    continue
                compared += 1
                if vo == vn:
                    agree += 1
                so, _ = score_from_row(old)
                sn, _ = score_from_row(new)
                if so is not None and sn is not None:
                    dscores.append(abs(so - sn))
            rate = agree / compared if compared else 0.0
            mean_d = sum(dscores) / len(dscores) if dscores else None
            ok = rate >= THRESH and compared >= 10
            if not ok:
                failed_any = True
            results.append(
                {
                    "checker": cid,
                    "legacy_env": legacy,
                    "n_sample": len(sample),
                    "n_compared": compared,
                    "missing_main_scores": missing_main,
                    "verdict_agreement": rate,
                    "mean_abs_delta_score": mean_d,
                    "pass_threshold": ok,
                }
            )
            print(json.dumps(results[-1]), flush=True)

    out = ROOT / "notes/t14_env_agreement.json"
    out.write_text(json.dumps({"threshold": THRESH, "checkers": results}, indent=2) + "\n")
    if failed_any:
        print(f"T14 env agreement FAILED (<{THRESH:.0%} on at least one checker)", flush=True)
        sys.exit(1)
    print("T14 env agreement OK", flush=True)


if __name__ == "__main__":
    main()
