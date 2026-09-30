#!/usr/bin/env python3
"""T24b CPU-only extra checkers (no OpenRouter): FT5, AlignScore-large, Bespoke-7B."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hf_token_env import sanitize_hf_token_env

sanitize_hf_token_env()

INST = ROOT / "data/t24/instances_t24b.jsonl"
OUT = ROOT / "results/raw/t24b"

# Resume-friendly: only score checkers missing from OUT (typically v2b_bespoke first add).
EXTRA = ("v2a_minicheck", "v3_alignscore", "v2b_bespoke")


def _n_scored(path: Path, n_inst: int) -> bool:
    if not path.is_file():
        return False
    return sum(1 for _ in path.open() if _.strip()) >= n_inst


def _conda_python(env_name: str) -> str:
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.check_output(
        ["conda", "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
        text=True,
        env=clean,
    ).strip()


def score_one(vid: str) -> None:
    py = _conda_python(os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif"))
    out = OUT / f"{vid}.jsonl"
    env = {
        **os.environ,
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / '.cache/src/MiniCheck'}:{ROOT / '.cache/src/AlignScore/src'}",
        "NLTK_DATA": os.environ.get("NLTK_DATA", str(ROOT / ".cache/nltk")),
    }
    subprocess.run(
        [py, str(ROOT / "src/score_jsonl.py"), "--verifier", vid, "--instances", str(INST), "--out", str(out)],
        check=True,
        cwd=str(ROOT),
        env=env,
    )


def main() -> None:
    if not INST.is_file():
        raise SystemExit(f"missing {INST}")
    OUT.mkdir(parents=True, exist_ok=True)
    n_inst = sum(1 for _ in INST.open() if _.strip())
    for vid in EXTRA:
        out = OUT / f"{vid}.jsonl"
        if _n_scored(out, n_inst):
            print(f"skip {vid} (complete)", flush=True)
            continue
        print(f"score {vid}", flush=True)
        score_one(vid)
    print("done")


if __name__ == "__main__":
    main()
