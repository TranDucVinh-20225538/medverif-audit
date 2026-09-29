#!/usr/bin/env python3
"""Run any scoring command under (verifier, out) flock. Prefer score_jsonl (lock built-in)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scoring_lock import exclusive_score_lock  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a scoring command under (verifier, out) flock.")
    parser.add_argument("--verifier", required=True, help="Registry verifier / job id for lock key")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path for lock key")
    parser.add_argument(
        "remainder",
        nargs=argparse.REMAINDER,
        help="Command after '--' (default: score_jsonl with --verifier/--instances/--out)",
    )
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else (ROOT / args.out)
    cmd = args.remainder
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print(json.dumps({"error": "missing command; pass -- then argv"}), file=sys.stderr)
        sys.exit(2)

    with exclusive_score_lock(args.verifier, out) as acquired:
        if not acquired:
            try:
                out_rel = str(out.relative_to(ROOT))
            except ValueError:
                out_rel = str(out)
            print(
                json.dumps(
                    {
                        "skipped": "already_running",
                        "verifier": args.verifier,
                        "out": out_rel,
                    }
                )
            )
            sys.exit(0)
        proc = subprocess.run(cmd, cwd=ROOT)
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
