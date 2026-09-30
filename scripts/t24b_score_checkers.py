#!/usr/bin/env python3
"""Score T24b pack: cpuverif small checkers + capped OpenRouter API pair."""

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

INST = ROOT / "data/t24/instances_t24b.jsonl"
OUT = ROOT / "results/raw/t24b"
T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"

CPU_T6A = (
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
)
API = ("v2a_minicheck", "v3_alignscore", "v4_ragas_nli", "v1_medscore")


def _conda_python(env_name: str) -> str:
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.check_output(
        ["conda", "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
        text=True,
        env=clean,
    ).strip()


def score_t6a(cid: str) -> None:
    py = _conda_python(os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif"))
    env = {
        **os.environ,
        "CUDA_VISIBLE_DEVICES": "",
        "MEDVERIF_LANE_B_ENV_PROFILE": "cpuverif",
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
    subprocess.run(
        [
            py,
            str(ROOT / "scripts/t6a_score_instances.py"),
            "--instances",
            str(INST),
            "--outdir",
            str(OUT),
            "--checker",
            cid,
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )


def score_api(vid: str) -> None:
    py = _conda_python(os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif"))
    out = OUT / f"{vid}.jsonl"
    env = {
        **os.environ,
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / '.cache/src/MiniCheck'}:{ROOT / '.cache/src/AlignScore/src'}",
    }
    if vid in ("v4_ragas_nli", "v1_medscore"):
        os.environ.setdefault("MEDVERIF_USE_OPENROUTER", "1")
        env["MEDVERIF_USE_OPENROUTER"] = "1"
        from t24_openrouter_budget import assert_under_cap  # noqa: E402

        # T24b API sub-cap $1 incremental on baseline file
        cap = float(os.environ.get("MEDVERIF_T24B_OR_CAP_USD", "1"))
        os.environ["MEDVERIF_T24_CAP_USD"] = str(cap)
        assert_under_cap()
    subprocess.run(
        [py, str(ROOT / "src/score_jsonl.py"), "--verifier", vid, "--instances", str(INST), "--out", str(out)],
        check=True,
        cwd=str(ROOT),
        env=env,
    )


def main() -> None:
    if not INST.is_file():
        raise SystemExit(f"missing {INST}; run t24b_build_instances.py first")
    OUT.mkdir(parents=True, exist_ok=True)
    id_to_jsonl = {c["id"]: c["jsonl"] for c in json.loads(T6_MANIFEST.read_text())["checkers"]}
    for cid in CPU_T6A:
        print(json.dumps({"score": cid}), flush=True)
        score_t6a(cid)
    for vid in API:
        print(json.dumps({"score": vid}), flush=True)
        try:
            score_api(vid)
        except RuntimeError as exc:
            print(json.dumps({"error": vid, "msg": str(exc)}))
    print(json.dumps({"outdir": str(OUT)}))


if __name__ == "__main__":
    main()
