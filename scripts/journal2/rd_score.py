#!/usr/bin/env python3
"""(RD-4) Score every real-label answer (correct AND flagged) with the paper's checkers. Resumable.

  --part judges  the 2 API judges of chain 1 (registry-pinned: RAGAS-NLI x Llama-3.3-70B@DeepInfra,
                 MedScore x Mistral-Small-24B@DeepInfra) via src/score_jsonl.py, in chunks with a
                 real-dose budget projection before every chunk (separate $5 ledger). Spec check first.
  --part small   small checkers on CPU in the paper's cpuverif conda env: MiniCheck-RoBERTa,
                 MiniCheck-DeBERTa, AlignScore-base (t6a) + MiniCheck-Flan-T5, AlignScore-large.
Scores: results/journal2/real_dose/scores/<file>.jsonl
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr2_common import (JUDGES, RD, ROOT, est_cost, is_done, judge_spec, log, mark_done, rd_assert_budget,  # noqa: E402
                        rd_spec_check, read_jsonl, tokens)
from jr_common import done_ids  # noqa: E402

INST = RD / "instances.jsonl"
SCORES = RD / "scores"
T6A = ("t6a_minicheck_roberta", "t6a_minicheck_deberta", "t6a_alignscore_base")
LEGACY = ("v2a_minicheck", "v3_alignscore")
HERE = Path(__file__).resolve().parent


def conda_python(env_name: str) -> str:
    clean = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.check_output(["conda", "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
                                   text=True, env=clean).strip()


def pypath() -> str:
    return ":".join([str(ROOT / "src"), str(ROOT / ".cache/src/MiniCheck"), str(ROOT / ".cache/src/AlignScore/src"),
                     str(ROOT / "analysis"), str(ROOT / "scripts")] +
                    ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else []))


def run_judges(rows, inst: Path, chunk: int, dry: bool) -> None:
    probs = rd_spec_check(need_key=not dry)
    if probs:
        raise SystemExit("SPEC CHECK FAILED (no API call made): %s" % probs)
    py = os.environ.get("MEDVERIF_JR_API_PY", sys.executable)
    total_est = 0.0
    for vid in JUDGES:
        spec = judge_spec(vid)
        out = SCORES / (vid + ".jsonl")
        per_row = lambda r: est_cost(spec["openrouter_model"], tokens(r["claim"]) + tokens(r["evidence"]) + 900, 400) * 2  # noqa: E731
        todo = [r for r in rows if r["instance_id"] not in done_ids(out)]
        est = sum(per_row(r) for r in todo)
        total_est += est
        log("RD4_judges", judge=vid, model=spec["openrouter_model"], provider=spec["provider"], todo=len(todo),
            est_cost_usd=round(est, 4))
        if dry:
            continue
        # MEDVERIF_API_LEDGER=0: per-row api_cost_usd is the ledger; keeps results/api_cost.json (chain 1) untouched
        env = dict(os.environ, MEDVERIF_USE_OPENROUTER="1", MEDVERIF_API_LEDGER="0", CUDA_VISIBLE_DEVICES="",
                   PYTHONPATH=pypath())
        while todo:
            batch = todo[:chunk]
            rd_assert_budget(sum(per_row(r) for r in batch), "judge " + vid)
            subprocess.run([py, str(ROOT / "src/score_jsonl.py"), "--verifier", vid, "--instances", str(inst),
                            "--out", str(out), "--limit", str(len(batch))], check=True, cwd=str(ROOT), env=env)
            before = len(todo)
            todo = [r for r in rows if r["instance_id"] not in done_ids(out)]
            if len(todo) >= before:
                raise SystemExit("judge %s made no progress; stopping" % vid)
            log("RD4_judges", judge=vid, remaining=len(todo), spent=round(rd_assert_budget()["spent_usd"], 4))
        bad = [r for r in read_jsonl(out) if r.get("api_model") and r["api_model"] != spec["openrouter_model"]]
        if bad:
            raise SystemExit("judge %s: %d rows served by a different model" % (vid, len(bad)))
    log("RD4_judges", est_total_usd=round(total_est, 4))
    if not dry:
        mark_done("RD4_judges", judges=list(JUDGES))


def run_small(inst: Path, dry: bool) -> None:
    env_name = os.environ.get("MEDVERIF_CPUVERIF_CONDA", "cpuverif")
    if dry:
        log("RD4_small", plan=list(T6A + LEGACY), env=env_name)
        return
    py = os.environ.get("MEDVERIF_RD_SMALL_PY") or conda_python(env_name)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="", MEDVERIF_LANE_B_ENV_PROFILE="cpuverif", PYTHONPATH=pypath(),
               MEDVERIF_M1="0", NLTK_DATA=os.environ.get("NLTK_DATA", str(ROOT / ".cache/nltk")))
    env["MEDVERIF_SCORE_ENV_TAG"] = os.environ.get("MEDVERIF_SCORE_ENV_TAG", "hpc_cpuverif")
    SCORES.mkdir(parents=True, exist_ok=True)
    for cid in T6A + LEGACY:  # same in-process loaders as UNF (scripts/journal2/small_checkers.py)
        log("RD4_small", checker=cid)
        subprocess.run([py, str(HERE / "small_checkers.py"), "--instances", str(inst), "--outdir", str(SCORES),
                        "--checker", cid], check=True, cwd=str(ROOT), env=env)
    mark_done("RD4_small", checkers=list(T6A + LEGACY))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["judges", "small"])
    ap.add_argument("--chunk", type=int, default=100)
    ap.add_argument("--instances", default=str(INST))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    stage = {"judges": "RD4_judges", "small": "RD4_small"}[args.part]
    if is_done(stage) and not args.dry_run:
        log(stage, skipped="marker present")
        return
    inst = Path(args.instances)
    rows = [r for r in read_jsonl(inst) if r.get("valid", True)]
    if not rows:
        raise SystemExit("no instances in %s (run rd_extract.py first)" % inst)
    if args.part == "judges":
        run_judges(rows, inst, args.chunk, args.dry_run)
    else:
        run_small(inst, args.dry_run)


if __name__ == "__main__":
    main()
