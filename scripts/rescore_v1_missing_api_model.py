#!/usr/bin/env python3
"""Drop v1_medscore rows lacking registry api_model and re-score those instance_ids."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_OUT = ROOT / "results/raw/v1_medscore.jsonl"
INST = ROOT / "data/v3/instances_main.jsonl"
MISSING = ROOT / "data/scratch/v1_rescore_missing_api_model.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    rows = read_jsonl(V1_OUT)
    bad_ids = {r["instance_id"] for r in rows if not r.get("api_model")}
    if not bad_ids:
        print(json.dumps({"status": "ok", "bad": 0}))
        return
    kept = [r for r in rows if r["instance_id"] not in bad_ids]
    V1_OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in kept) + ("\n" if kept else ""))
    inst_map = {r["instance_id"]: r for r in read_jsonl(INST)}
    todo = [inst_map[iid] for iid in sorted(bad_ids) if iid in inst_map]
    if len(todo) != len(bad_ids):
        missing = bad_ids - set(inst_map)
        raise SystemExit(f"instances missing from {INST}: {missing}")
    MISSING.parent.mkdir(parents=True, exist_ok=True)
    MISSING.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in todo) + "\n")
    cmd = [
        sys.executable,
        str(ROOT / "src/score_jsonl.py"),
        "--verifier",
        "v1_medscore",
        "--instances",
        str(MISSING),
        "--out",
        str(V1_OUT),
    ]
    env = {**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src"), "MEDVERIF_USE_OPENROUTER": "1"}
    rc = subprocess.call(cmd, cwd=ROOT, env=env)
    if rc != 0:
        raise SystemExit(rc)
    still = [r["instance_id"] for r in read_jsonl(V1_OUT) if not r.get("api_model")]
    print(json.dumps({"rescored": len(todo), "still_missing_api_model": still}, indent=2))
    if still:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
