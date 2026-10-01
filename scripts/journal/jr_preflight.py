#!/usr/bin/env python3
"""Pre-flight for the journal chain (login node, no API calls, no GPU): input files, environments,
API spec check (registry + pinned generators + key present -- the key is never printed) and a cost
estimate for every API stage against the shared cap. Exit code 2 if anything blocks the chain."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import (CAP_USD, GENERATORS, JUDGES, QUESTION_WRITER, ROOT, est_cost, judge_spec, log, spec_check,  # noqa: E402
                       spent_usd)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="A,B,C")
    stages = set(ap.parse_args().stages.split(","))
    blockers, warnings = [], []
    need = {"data/v3/instances_main.jsonl": "ABC", "data/t7/instances_e1_unit.jsonl": "AC", "data/t15/train.jsonl": "C",
            "data/t15/dev.jsonl": "C", "data/t24/instances_t24b.jsonl": "C", "notes/openrouter_verifiers.json": "B"}
    for rel, st in need.items():
        if not (ROOT / rel).is_file() and stages & set(st):
            blockers.append("missing " + rel)
    if not (ROOT / "data/t8/aggrefact/test.jsonl").is_file():
        warnings.append("data/t8/aggrefact/test.jsonl missing -> AggreFact eval skipped (run scripts/t8_download_aggrefact.py)")
    from jr_rag_questions import default_corpus_dirs  # noqa: E402

    dirs = default_corpus_dirs()
    if not dirs and "B" in stages:
        blockers.append("MedRAG textbooks chunk dir not found under .cache/huggingface/hub/datasets--MedRAG--textbooks")
    for rel in (".cache/src/MiniCheck", ".cache/src/AlignScore/src"):
        if not (ROOT / rel).is_dir() and stages & {"B", "C"}:
            blockers.append("missing " + rel)
    if shutil.which("conda"):
        try:
            envs = subprocess.check_output(["conda", "env", "list"], text=True)
            if "cpuverif" not in envs and stages & {"B", "C"}:
                blockers.append("conda env cpuverif not found (small-checker scoring)")
        except Exception as exc:
            warnings.append("conda env list failed: %s" % exc)
    else:
        warnings.append("conda not on PATH here (sbatch scripts source the shared conda.sh)")
    if "B" in stages:
        blockers += ["spec: " + p for p in spec_check()]
    # cost estimate (pessimistic token counts)
    n_q, n_cand = 200, 280
    est = {
        "B1 question writer": n_cand * est_cost(QUESTION_WRITER["model"], 650, 40),
        "B3a generators": sum(n_q * est_cost(g["model"], 1300, 180) for g in GENERATORS.values()),
    }
    n_inst = n_q * len(GENERATORS) * 6 * 0.75
    for j in JUDGES:
        est["B4 judge " + j] = n_inst * est_cost(judge_spec(j)["openrouter_model"], 1200, 250) * 2
    tot = sum(est.values())
    rep = {"cap_usd": CAP_USD, "already_spent_in_chain_usd": round(spent_usd(), 4),
           "estimate_usd": {k: round(v, 3) for k, v in est.items()}, "estimate_total_usd": round(tot, 3),
           "judges": {j: [judge_spec(j)["openrouter_model"], judge_spec(j)["provider"]] for j in JUDGES},
           "generators": GENERATORS, "question_writer": QUESTION_WRITER, "corpus_dirs": [str(d) for d in dirs],
           "python": sys.executable, "py_version": sys.version.split()[0], "blockers": blockers, "warnings": warnings}
    print(json.dumps(rep, indent=1))
    if tot > CAP_USD:
        print("WARNING: estimate exceeds the cap; stages stop at the cap (budget check before every batch).")
    sys.exit(2 if blockers else 0)


if __name__ == "__main__":
    main()
