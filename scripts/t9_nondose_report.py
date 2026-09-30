#!/usr/bin/env python3
"""T9 NeMo AlignScore rail after non-dose exclusion: blocked/total on unit errors (group d) and value errors (group c)."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from non_dose_targets import NON_DOSE_TARGET_BASES  # noqa: E402

INST = ROOT / "data/t9/instances_all.jsonl"
RAILS = (("AlignScore-base", "results/raw/t9/alignscore_rail.jsonl"), ("AlignScore-large", "results/raw/t9/alignscore_rail_large.jsonl"))
CELLS = (
    ("unit error ×1000 (claim+evid)", "d", None),
    ("unit error ×1000 claim", "d", "E1-unit-claim"),
    ("unit error ×1000 evid", "d", "E1-unit-evid"),
    ("value error ×2", "c", None),
)
OUT_MD = ROOT / "notes/t9_nondose.md"
OUT_JSON = ROOT / "notes/t9_nondose.json"


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open() if l.strip()]


def cluster_ci(vals: list[int], bases: list[str], n_boot: int = 1000, seed: int = 42) -> tuple[float, float]:
    rnd = random.Random(seed)
    by: dict[str, list[int]] = {}
    for v, b in zip(vals, bases):
        by.setdefault(b, []).append(v)
    ub = sorted(by)
    rates = []
    for _ in range(n_boot):
        s = [x for b in (rnd.choice(ub) for _ in ub) for x in by[b]]
        rates.append(sum(s) / len(s))
    rates.sort()
    return rates[int(0.025 * n_boot)], rates[int(0.975 * n_boot) - 1]


def main() -> None:
    inst = {r["instance_id"]: r for r in read_jsonl(INST)}
    out = []
    lines = ["# T9 — NeMo Guardrails AlignScore rail after non-dose exclusion", "",
             f"NeMo 0.24.1, block if AlignScore < 0.5. Non-dose bases excluded (`src/non_dose_targets.py`, {len(NON_DOSE_TARGET_BASES)} bases). "
             "CI: 95% cluster bootstrap by base (1000, seed 42). Env: vllm (NeMo AlignScore HTTP server).", "",
             "| rail | cell | blocked / total | rate [95% CI] | excluded non-dose rows |", "|---|---|---:|---|---:|"]
    for rail, path in RAILS:
        sc = {r["instance_id"]: r for r in read_jsonl(ROOT / path)}
        for label, grp, sub in CELLS:
            ids = [i for i, r in inst.items() if r["t9_group"] == grp and i in sc and (sub is None or f"__{sub}__" in i)]
            kept = [i for i in ids if inst[i]["base_id"] not in NON_DOSE_TARGET_BASES]
            blk = [int(bool(sc[i]["blocked"])) for i in kept]
            lo, hi = cluster_ci(blk, [inst[i]["base_id"] for i in kept])
            rec = {"rail": rail, "cell": label, "blocked": sum(blk), "total": len(kept), "rate": sum(blk) / len(kept),
                   "lo": lo, "hi": hi, "excluded_non_dose": len(ids) - len(kept), "source": path}
            out.append(rec)
            lines.append(f"| {rail} | {label} | {rec['blocked']}/{rec['total']} | {100*rec['rate']:.1f}% [{100*lo:.1f}, {100*hi:.1f}] | {rec['excluded_non_dose']} |")
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(out, indent=1) + "\n")
    print(OUT_MD.read_text())


if __name__ == "__main__":
    main()
