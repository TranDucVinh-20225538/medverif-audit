#!/usr/bin/env python3
"""Score instances with one T6-A checker (resume by instance_id)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("MEDVERIF_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "src"))

import cpu_early as ce
from lane_b_env import append_stamped
from verifiers.io_utils import done_ids, read_jsonl

MANIFEST = ROOT / "notes" / "t6a_eco_checkers.json"

MINICHECK_IDS = frozenset(
    {
        "t6a_minicheck_roberta",
        "t6a_minicheck_deberta",
        "t6a_granite_guardian",
    }
)
SUMMAC_IDS = frozenset({"t6a_summac_zs", "t6a_summac_conv"})


def score_checker(checker_id: str, rows: list[dict], out_path: Path) -> None:
    todo = [r for r in rows if r["instance_id"] not in done_ids(out_path)]
    if not todo:
        print(f"{checker_id}: complete ({len(done_ids(out_path))} lines)")
        return

    if checker_id in MINICHECK_IDS:
        from verifiers import t6a_minicheck as mc

        model, _ = mc.load(checker_id)
        step = 1 if checker_id == "t6a_granite_guardian" else 4
        for offset in range(0, len(todo), step):
            chunk = todo[offset : offset + step]
            append_stamped(out_path, mc.score_batch(model, chunk, checker_id))
    elif checker_id == "t6a_alignscore_base":
        from verifiers import t6a_alignscore_base as asb

        model, _ = asb.load()
        step = 4
        for offset in range(0, len(todo), step):
            chunk = todo[offset : offset + step]
            append_stamped(out_path, asb.score_batch(model, chunk))
    elif checker_id in SUMMAC_IDS:
        from verifiers import t6a_summac as sm

        model, _ = sm.load(checker_id)
        for row in todo:
            append_stamped(out_path, sm.score_batch(model, [row], checker_id))
    elif checker_id == "t6a_hhem":
        from verifiers import t6a_hhem as hhem

        bundle, _ = hhem.load()
        step = 8
        for offset in range(0, len(todo), step):
            chunk = todo[offset : offset + step]
            append_stamped(out_path, hhem.score_batch(bundle, chunk))
    else:
        raise SystemExit(f"unknown T6-A checker: {checker_id}")

    print(f"{checker_id}: {len(done_ids(out_path))} scored → {out_path}")


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--instances", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--checker", required=True, help="T6-A id or 'all'")
    p.add_argument("--out-suffix", default="", help="e.g. t8b → t6a_*_t8b.jsonl")
    p.add_argument(
        "--force",
        action="store_true",
        help="truncate output jsonl for selected checker(s) before scoring",
    )
    args = p.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    ids = [c["id"] for c in manifest["checkers"]]
    if args.checker != "all":
        if args.checker not in ids:
            raise SystemExit(f"checker must be one of {ids} or all")
        ids = [args.checker]

    rows = read_jsonl(args.instances)
    args.outdir.mkdir(parents=True, exist_ok=True)
    ce.ensure_nltk()
    for cid in ids:
        jsonl = next(c["jsonl"] for c in manifest["checkers"] if c["id"] == cid)
        out_name = jsonl
        if args.out_suffix:
            out_name = jsonl.replace(".jsonl", f"_{args.out_suffix}.jsonl")
        out_path = args.outdir / out_name
        if args.force and out_path.is_file():
            out_path.unlink()
        score_checker(cid, rows, out_path)


if __name__ == "__main__":
    main()
