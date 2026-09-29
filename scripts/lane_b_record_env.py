#!/usr/bin/env python3
"""Write notes/lane_b_env.json from active cpuverif session."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lane_b_env import ENV_JSON, record_lane_b_env  # noqa: E402


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--reason", default="lane_b_record_env")
    args = p.parse_args()
    doc = record_lane_b_env(reason=args.reason)
    print(json.dumps({"written": str(ENV_JSON.relative_to(ROOT)), "env_id": doc["env_id"]}, indent=2))


if __name__ == "__main__":
    main()
