"""Shared helpers for journal chain 2 (JHIR): real-world dose errors (RD) + attribution (AT).

Reuses scripts/journal/jr_common.py (pinned generators/judges, spec check, chat_pinned, price table,
jsonl helpers) but keeps its OWN markers and its OWN budget ledger so chain 1 (jobs 62055-62064)
is unaffected:

  results/journal2/markers/<stage>.done            resumable stage markers
  ledger = sum of api_cost_usd over results/journal2/real_dose/**.jsonl
  cap    = MEDVERIF_RD_CAP_USD (default $5), checked before EVERY API batch
Chain-1 spend (results/journal/) is never counted here and chain-2 rows never land there.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT / "src", ROOT / "scripts", ROOT / "analysis", ROOT / "scripts" / "journal", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import jr_common as J1  # noqa: E402
from jr_common import (GENERATORS, JUDGES, PRICES, append_jsonl, chat_pinned, est_cost, judge_spec,  # noqa: E402,F401
                       load_env, log, read_jsonl, spec_check, tokens, write_jsonl)

JR2 = Path(os.environ.get("MEDVERIF_JR2_DIR") or (ROOT / "results" / "journal2"))  # override only for smoke tests
MARKERS = JR2 / "markers"
RD = JR2 / "real_dose"
AT = JR2 / "attribution"
LABELS = ROOT / "data" / "real_labels" / "labels.jsonl"
RD_QC = Path(os.environ.get("MEDVERIF_RD_QC") or (ROOT / "qc" / "real_dose_errors_check.csv"))  # override only for smoke tests
RD_CAP_USD = float(os.environ.get("MEDVERIF_RD_CAP_USD", "5"))


def marker(stage: str) -> Path:
    return MARKERS / (stage + ".done")


def is_done(stage: str) -> bool:
    return marker(stage).is_file() and os.environ.get("MEDVERIF_JR2_FORCE", "") not in ("1", stage)


def mark_done(stage: str, **info) -> None:
    MARKERS.mkdir(parents=True, exist_ok=True)
    info = dict({"stage": stage, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "slurm_job": os.environ.get("SLURM_JOB_ID", "local")}, **info)
    marker(stage).write_text(json.dumps(info, indent=2, default=str) + "\n")


def rd_spent_usd() -> float:
    total = 0.0
    if not RD.is_dir():
        return 0.0
    for p in RD.rglob("*.jsonl"):
        for r in read_jsonl(p):
            c = r.get("api_cost_usd")
            if isinstance(c, (int, float)):
                total += float(c)
            elif r.get("api_prompt_tokens"):
                total += est_cost(r.get("api_model") or "", r.get("api_prompt_tokens") or 0, r.get("api_completion_tokens") or 0)
    return total


def rd_assert_budget(next_batch_usd: float = 0.0, what: str = "") -> Dict[str, float]:
    s = rd_spent_usd()
    if s + next_batch_usd > RD_CAP_USD:
        raise SystemExit("BUDGET STOP%s: spent $%.4f + next batch est $%.4f > cap $%.2f (real-dose ledger)" % (
            (" (" + what + ")") if what else "", s, next_batch_usd, RD_CAP_USD))
    return {"spent_usd": s, "cap_usd": RD_CAP_USD, "remaining_usd": RD_CAP_USD - s}


def rd_spec_check(need_key: bool = True) -> list:
    """jr_common.spec_check (judges in registry with pinned model/provider, generators pinned + priced,
    key present) -- the chain-1 question writer is not used here but stays in the check (harmless)."""
    return spec_check(JUDGES, need_key=need_key)


def wilson(k: int, n: int, z: float = 1.959964) -> tuple:
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def cluster_boot(groups: list, n_boot: int = 10000, seed: int = 20261001) -> tuple:
    """groups: list of (k, n) per cluster. Percentile CI of sum(k)/sum(n) over resampled clusters."""
    import random

    groups = [g for g in groups if g[1] > 0]
    if len(groups) < 2:
        return (None, None)
    rng = random.Random(seed)
    m = len(groups)
    vals = []
    for _ in range(n_boot):
        k = n = 0
        for _ in range(m):
            a, b = groups[rng.randrange(m)]
            k += a
            n += b
        vals.append(k / n if n else 0.0)
    vals.sort()
    return (vals[int(0.025 * (n_boot - 1))], vals[int(0.975 * (n_boot - 1))])
