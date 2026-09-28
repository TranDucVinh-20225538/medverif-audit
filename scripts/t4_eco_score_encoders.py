#!/usr/bin/env python3
"""Deprecated alias: use scripts/t4_eco_score_node30.py on node30."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "t4_eco_score_node30.py"),
        run_name="__main__",
    )
