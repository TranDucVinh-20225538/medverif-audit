#!/usr/bin/env python3
"""(UNF-2) Score the UNF packs with the small checkers on CPU (resumable by instance_id).

  --pack orig   original text of the rows UNF changes (same-env "before"; also an env-agreement
                check against the paper's stored verdicts). MEDVERIF_UNF_ORIG_ALL=1 -> all cohort rows.
  --pack unf    only rows whose text UNF changed (unchanged rows reuse the orig score: identical input)
Checkers use the repo wrappers (src/verifiers/*: same chunking, thresholds and CPU patches as the
paper's cpuverif scoring): t6a_minicheck_roberta, t6a_minicheck_deberta, t6a_alignscore_base,
v2a_minicheck (MiniCheck-Flan-T5-Large), v3_alignscore (AlignScore-large).
Scores: results/journal2/unf/scores/<pack>/<checker>.jsonl   (row: instance_id, score, verdict, env)

Env: PYTHONPATH must contain src, MiniCheck and AlignScore/src; HF_HOME / HUGGINGFACE_HUB_CACHE set.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import small_checkers as SC  # noqa: E402  (shared loaders + AlignScore compat)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ["MEDVERIF_M1"] = "0"  # never stack M1 on top of UNF

DATA = ROOT / "data/journal2/unf"
OUT = ROOT / "results/journal2/unf/scores"
CHECKERS = SC.CHECKERS


def read_jsonl(p: Path) -> list:
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def env_tag() -> dict:
    return SC.env_tag(os.environ.get("MEDVERIF_UNF_ENV", "box_cpu"))


def paper_verdicts(slug: str) -> dict:
    for p in (ROOT / "scripts", ROOT / "analysis", ROOT / "scripts" / "journal"):
        if str(p) not in sys.path:
            sys.path.append(str(p))
    try:
        import jr_threshold_robustness as J

        return J.score_map(slug)[1]
    except Exception as exc:  # noqa: BLE001
        print("paper verdicts unavailable for %s (%s): scoring changed rows only" % (slug, exc))
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True, choices=["orig", "unf", "unf_si"])
    ap.add_argument("--checker", required=True, help="one id or 'all'")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--outdir", default=str(OUT), help="scores root (default results/journal2/unf/scores)")
    args = ap.parse_args()
    rows = read_jsonl(DATA / ("cohort_%s.jsonl" % args.pack))
    all_orig = list(rows) if args.pack == "orig" else []
    changed = {r["instance_id"] for r in read_jsonl(DATA / ("cohort_%s.jsonl" % ("unf" if args.pack == "orig" else args.pack)))
               if r.get("unf_changed")}
    if args.pack != "orig" or os.environ.get("MEDVERIF_UNF_ORIG_ALL", "0") != "1":
        # unchanged rows have identical input before/after -> one stored score serves both sides
        rows = [r for r in rows if r["instance_id"] in changed]
    checkers = CHECKERS if args.checker == "all" else [args.checker]
    try:
        import cpu_early as ce

        ce.ensure_nltk()
    except Exception as exc:  # noqa: BLE001
        print("nltk check:", exc)
    tag = env_tag()
    for ck in checkers:
        ck_rows = rows
        if args.pack == "orig" and os.environ.get("MEDVERIF_UNF_ORIG_ALL", "0") != "1":
            # unchanged rows normally reuse the paper's stored score; score those the paper lacks for this checker
            ck_rows = rows + [r for r in all_orig if r["instance_id"] not in changed
                              and paper_verdicts(ck).get(r["instance_id"]) not in ("PASS", "FAIL", "PARSE_FAIL")]
        SC.score_rows(ck_rows, ck, Path(args.outdir) / args.pack / (ck + ".jsonl"), batch=args.batch, limit=args.limit,
                      extra=dict(pack=args.pack, **tag), label=args.pack)


if __name__ == "__main__":
    main()
