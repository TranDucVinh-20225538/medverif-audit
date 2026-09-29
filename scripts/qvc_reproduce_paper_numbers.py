#!/usr/bin/env python3
"""Regenerate qvc/paper_numbers.json via the canonical pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    script = ROOT / "scripts/compute_paper_numbers.py"
    rc = subprocess.call([sys.executable, str(script)])
    if rc != 0:
        raise SystemExit(rc)
    print(ROOT / "qvc/paper_numbers.json")


if __name__ == "__main__":
    main()
