#!/usr/bin/env python3
"""(B4) Score the real-RAG pack with the paper's checkers. Resumable (score files are appended by id).

  --part judges   API judges (registry-pinned; same pair as T24b) in chunks of --chunk rows with a
                  budget projection before every chunk (shared $5 chain cap). Spec check first.
  --part small    small checkers on CPU in the `cpuverif` conda env (the paper's scoring env):
                  MiniCheck-RoBERTa / -DeBERTa / AlignScore-base (t6a) + MiniCheck-FT5 / AlignScore-large.
  --part bespoke  Bespoke-MiniCheck-7B (GPU, vllm env), as jobs/run_t24b_bespoke_gpu.sbatch.
Scores: results/journal/rag/scores/<verifier>.jsonl
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import (JUDGES, RAG_DIR, ROOT, assert_budget, done_ids, est_cost, is_done, judge_spec, log,  # noqa: E402
                       mark_done, read_jsonl, spec_check, tokens)

INST = ROOT / "data/journal/instances_rag.jsonl"
SCORES = RAG_DIR / "scores"
T6A = ("t6a_minicheck_roberta", "t6a_minicheck_deberta", "t6a_alignscore_base")
LEGACY = ("v2a_minicheck", "v3_alignscore")


def conda_python(env_name: str) -> str:
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.check_output(["conda", "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
                                   text=True, env=clean).strip()


def pypath(*extra) -> str:
    return ":".join([str(ROOT / "src"), str(ROOT / ".cache/src/MiniCheck"), str(ROOT / ".cache/src/AlignScore/src"),
                     str(ROOT / "analysis"), str(ROOT / "scripts")] + list(extra))


def run_judges(rows, chunk: int, dry: bool) -> None:
    probs = spec_check(need_key=not dry)
    if probs:
        raise SystemExit("SPEC CHECK FAILED (no API call made): %s" % probs)
    py = os.environ.get("MEDVERIF_JR_API_PY", sys.executable)
    for vid in JUDGES:
        spec = judge_spec(vid)
        out = SCORES / (vid + ".jsonl")
        per_row = lambda r: est_cost(spec["openrouter_model"], tokens(r["claim"]) + tokens(r["evidence"]) + 900, 400) * 2
        todo = [r for r in rows if r["instance_id"] not in done_ids(out)]
        log("B4_judges", judge=vid, model=spec["openrouter_model"], provider=spec["provider"], todo=len(todo),
            est_cost_usd=round(sum(per_row(r) for r in todo), 4))
        if dry:
            continue
        env = dict(os.environ, MEDVERIF_USE_OPENROUTER="1", MEDVERIF_API_LEDGER="1", CUDA_VISIBLE_DEVICES="",
                   PYTHONPATH=pypath())
        while todo:
            batch = todo[:chunk]
            assert_budget(sum(per_row(r) for r in batch), "judge " + vid)
            subprocess.run([py, str(ROOT / "src/score_jsonl.py"), "--verifier", vid, "--instances", str(INST),
                            "--out", str(out), "--limit", str(len(batch))], check=True, cwd=str(ROOT), env=env)
            before = len(todo)
            todo = [r for r in rows if r["instance_id"] not in done_ids(out)]
            if len(todo) >= before:
                raise SystemExit("judge %s made no progress; stopping" % vid)
            log("B4_judges", judge=vid, remaining=len(todo), spent=round(assert_budget()["spent_usd"], 4))
        bad = [r for r in read_jsonl(out) if r.get("api_model") and r["api_model"] != spec["openrouter_model"]]
        if bad:
            raise SystemExit("judge %s: %d rows served by a different model" % (vid, len(bad)))
    if not dry:
        mark_done("B4_judges", judges=list(JUDGES))


def run_small(dry: bool) -> None:
    env_name = os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif")
    if dry:
        log("B4_small", plan=list(T6A + LEGACY), env=env_name)
        return
    py = conda_python(env_name)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="", MEDVERIF_LANE_B_ENV_PROFILE="cpuverif", PYTHONPATH=pypath(),
               NLTK_DATA=os.environ.get("NLTK_DATA", str(ROOT / ".cache/nltk")))
    SCORES.mkdir(parents=True, exist_ok=True)
    for cid in T6A:
        log("B4_small", checker=cid)
        subprocess.run([py, str(ROOT / "scripts/t6a_score_instances.py"), "--instances", str(INST), "--outdir", str(SCORES),
                        "--checker", cid], check=True, cwd=str(ROOT), env=env)
    for vid in LEGACY:
        log("B4_small", checker=vid)
        subprocess.run([py, str(ROOT / "src/score_jsonl.py"), "--verifier", vid, "--instances", str(INST),
                        "--out", str(SCORES / (vid + ".jsonl"))], check=True, cwd=str(ROOT), env=env)
    mark_done("B4_small", checkers=list(T6A + LEGACY))


def run_bespoke(dry: bool) -> None:
    if dry:
        log("B4_bespoke", plan="v2b_bespoke via src/score_jsonl.py (vllm env, GPU)")
        return
    env = dict(os.environ, PYTHONPATH=pypath(), MEDVERIF_BESPOKE_BATCH=os.environ.get("MEDVERIF_BESPOKE_BATCH", "8"))
    subprocess.run([sys.executable, str(ROOT / "src/score_jsonl.py"), "--verifier", "v2b_bespoke", "--instances", str(INST),
                    "--out", str(SCORES / "v2b_bespoke.jsonl")], check=True, cwd=str(ROOT), env=env)
    mark_done("B4_bespoke")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["judges", "small", "bespoke"])
    ap.add_argument("--chunk", type=int, default=100)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--instances", default=str(ROOT / "data/journal/instances_rag.jsonl"))
    args = ap.parse_args()
    globals()["INST"] = Path(args.instances)
    stage = {"judges": "B4_judges", "small": "B4_small", "bespoke": "B4_bespoke"}[args.part]
    if is_done(stage) and not args.dry_run:
        log(stage, skipped="marker present")
        return
    rows = [r for r in read_jsonl(INST) if r.get("valid", True)]
    if not rows:
        raise SystemExit("no instances in %s (run jr_rag_instances.py first)" % INST)
    {"judges": lambda: run_judges(rows, args.chunk, args.dry_run), "small": lambda: run_small(args.dry_run),
     "bespoke": lambda: run_bespoke(args.dry_run)}[args.part]()


if __name__ == "__main__":
    main()
