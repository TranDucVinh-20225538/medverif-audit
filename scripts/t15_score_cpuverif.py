#!/usr/bin/env python3
"""Score base (stock MiniCheck-RoBERTa) or ft (T15) on a pack in the reference cpuverif env; resumable."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import read_jsonl  # noqa: E402
from t15_eval import _score_pack  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--leg", choices=("base", "ft"), required=True)
    args = ap.parse_args()
    _score_pack(read_jsonl(args.instances), args.out, use_t15=args.leg == "ft", progress_tag=f"{args.leg}_{args.out.stem}")


if __name__ == "__main__":
    main()
