#!/usr/bin/env python3
"""Pre-flight for journal chain 2 (login node; no API calls, no GPU, no model loading).

Checks committed inputs (FDA labels, UNF cohort), the real-dose API spec (pinned generators + judges,
key PRESENT -- never printed), a pessimistic cost estimate against the separate real-dose cap, the
cpuverif conda env, AlignScore/MiniCheck sources and the HF cache entries the CPU/GPU stages load.
Exit code 2 if anything blocks a selected stage (RD, UNF, AT)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr2_common import (GENERATORS, JUDGES, LABELS, RD_CAP_USD, ROOT, est_cost, judge_spec, rd_spec_check,  # noqa: E402
                        rd_spent_usd, read_jsonl)

HF_MODELS = {  # repo -> stages that load it
    "lytang/MiniCheck-RoBERTa-Large": "RD,UNF,AT", "lytang/MiniCheck-DeBERTa-v3-Large": "RD,UNF",
    "lytang/MiniCheck-Flan-T5-Large": "RD,UNF,AT", "yzha/AlignScore": "RD,UNF,AT", "roberta-large": "RD,UNF,AT",
    "roberta-base": "RD,UNF",
}


def hf_cached(repo: str) -> bool:
    hf = Path(os.environ.get("HF_HOME") or ROOT / ".cache/huggingface")
    hub = Path(os.environ.get("HUGGINGFACE_HUB_CACHE") or hf / "hub")
    name = "models--" + repo.replace("/", "--")
    return any((d / name / "snapshots").is_dir() and any((d / name / "snapshots").iterdir()) for d in (hub, hf))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="RD,UNF,AT")
    stages = set(ap.parse_args().stages.split(","))
    blockers, warnings = [], []
    need = {str(LABELS.relative_to(ROOT)): "RD", "data/journal2/unf/cohort_orig.jsonl": "UNF",
            "data/journal2/unf/cohort_unf.jsonl": "UNF", "data/v3/instances_main.jsonl": "UNF,AT",
            "data/t7/instances_e1_unit.jsonl": "UNF", "data/v3/t17_downdose.jsonl": "UNF"}
    for rel, st in need.items():
        if stages & set(st.split(",")) and not (ROOT / rel).is_file():
            blockers.append("missing " + rel)
    for rel in (".cache/src/AlignScore/src",):
        if stages & {"RD", "UNF"} and not (ROOT / rel).is_dir():
            blockers.append("missing %s (AlignScore source for the cpuverif small checkers)" % rel)
    if stages & {"RD", "UNF"}:
        if shutil.which("conda"):
            try:
                envs = subprocess.check_output(["conda", "env", "list"], text=True)
                if "cpuverif" not in envs and not os.environ.get("MEDVERIF_CPUVERIF_PY"):
                    blockers.append("conda env cpuverif not found (set MEDVERIF_CPUVERIF_PY to its python)")
            except Exception as exc:  # noqa: BLE001
                warnings.append("conda env list failed: %s" % exc)
        else:
            warnings.append("conda not on PATH here (sbatch scripts source the shared conda.sh)")
    for repo, st in HF_MODELS.items():
        if stages & set(st.split(",")) and not hf_cached(repo):
            warnings.append("HF cache has no %s (compute nodes may be offline: prefetch on the login node, e.g. "
                            "huggingface-cli download %s)" % (repo, repo))
    est, n_q = {}, 0
    if "RD" in stages:
        blockers += ["spec: " + p for p in rd_spec_check(need_key=True)]
        labels = read_jsonl(LABELS)
        n_q = min(2 * len(labels), 400)
        for g, spec in GENERATORS.items():
            est["RD2 generator " + g] = n_q * 2 * est_cost(spec["model"], 520, 160)
        n_inst = n_q * len(GENERATORS) * 2 * 0.9
        for j in JUDGES:
            est["RD4 judge " + j] = n_inst * est_cost(judge_spec(j)["openrouter_model"], 1300, 400) * 2
    tot = sum(est.values())
    rep = {"cap_usd_real_dose": RD_CAP_USD, "already_spent_real_dose_usd": round(rd_spent_usd(), 4),
           "n_questions_upper": n_q, "estimate_usd": {k: round(v, 3) for k, v in est.items()},
           "estimate_total_usd": round(tot, 3),
           "judges": {j: [judge_spec(j)["openrouter_model"], judge_spec(j)["provider"]] for j in JUDGES},
           "generators": GENERATORS, "python": sys.executable, "py_version": sys.version.split()[0],
           "api_ledger_chain1_untouched": "MEDVERIF_API_LEDGER=0 in jr2_env.sh", "blockers": blockers, "warnings": warnings}
    print(json.dumps(rep, indent=1))
    if tot > RD_CAP_USD:
        print("WARNING: estimate exceeds the real-dose cap; stages stop at the cap (budget check before every batch).")
    sys.exit(2 if blockers else 0)


if __name__ == "__main__":
    main()
