#!/usr/bin/env python3
"""Append up to N textbook candidates; stage1 with spend cap; rebuild kept bases."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--max-new-candidates", type=int, default=1000)
    p.add_argument("--target-bases", type=int, default=60)
    p.add_argument("--budget-usd", type=float, default=1.0)
    args = p.parse_args()

    cand = ROOT / "data/main_ext/candidates_selected.jsonl"
    before_bases = sum(1 for _ in open(ROOT / "data/main_ext/stage1/base_pairs.jsonl"))

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/main_ext_select_candidates.py"),
            "--append",
            "--max-candidates",
            str(args.max_new_candidates),
            "--out",
            str(cand),
        ],
        check=True,
        cwd=str(ROOT),
    )
    env = {
        **os.environ,
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'scripts/expand'}",
        "MEDVERIF_USE_OPENROUTER": "1",
        "MEDVERIF_EXPAND_LEDGER": str(ROOT / "data/main_ext/stage1/api_spend_continue.jsonl"),
        "MEDVERIF_EXPAND_BUDGET_USD": str(args.budget_usd),
        "MEDVERIF_LANE_A_SYNC": "0",
    }
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/stage12_openrouter.py"),
            "--candidates",
            str(cand),
            "--outdir",
            str(ROOT / "data/main_ext/stage1"),
            "--template-note",
            str(ROOT / "notes/main_ext_chat_template.md"),
        ],
        cwd=str(ROOT),
        env=env,
    )
    after_bases = sum(1 for _ in open(ROOT / "data/main_ext/stage1/base_pairs.jsonl"))
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/main_ext_rebuild_kept.py"),
            "--target-bases",
            str(args.target_bases),
        ],
        check=True,
        cwd=str(ROOT),
    )
    subprocess.run([sys.executable, str(ROOT / "scripts/main_ext_funnel.py")], check=True, cwd=str(ROOT))
    print(
        json.dumps(
            {
                "stage12_exit": proc.returncode,
                "stage1_bases_before": before_bases,
                "stage1_bases_after": after_bases,
                "budget_usd": args.budget_usd,
            },
            indent=2,
        )
    )
    if proc.returncode not in (0, 1, 2):
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
