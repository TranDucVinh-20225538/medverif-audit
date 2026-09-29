#!/usr/bin/env python3
"""Merge T17 into T19 pack; score only new instance_ids (resume-safe)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T17 = ROOT / "data/v3/t17_downdose.jsonl"
INST = ROOT / "data/t19/instances_t19.jsonl"
RAW = ROOT / "results/raw/t19"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    if not T17.is_file():
        print(json.dumps({"status": "skip", "reason": "t17 missing", "path": str(T17)}))
        return
    before = {r["instance_id"] for r in read_jsonl(INST)}
    subprocess.run([sys.executable, str(ROOT / "scripts/t19_build_instances.py")], check=True)
    after_rows = read_jsonl(INST)
    new_ids = [r for r in after_rows if r["instance_id"] not in before]
    manifest = {
        "t17_path": str(T17),
        "instances_before": len(before),
        "instances_after": len(after_rows),
        "new_instance_ids": len(new_ids),
    }
    (ROOT / "notes/t19_t17_refresh.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if not new_ids:
        print(json.dumps(manifest))
        return
    todo = ROOT / "data/t19/instances_t17_new.jsonl"
    with todo.open("w") as handle:
        for row in new_ids:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    for slug, out in (
        ("llama32_1b", "llama32_1b_instruct.jsonl"),
        ("llama32_3b", "llama32_3b_instruct.jsonl"),
        ("llama31_8b_local", "llama31_8b_instruct.jsonl"),
    ):
        path = RAW / out
        if not path.is_file():
            continue
        env = {**dict(**{"MEDVERIF_T19_SLUG": slug}), }
    print(json.dumps({**manifest, "todo_file": str(todo.relative_to(ROOT))}))
    print("Score new rows: MEDVERIF_T19_SLUG=... MEDVERIF_T19_HF_MODEL=... python3 scripts/t19_score_jsonl.py "
          f"--instances {todo} --out results/raw/t19/<model>.jsonl (appends/resumes)")


if __name__ == "__main__":
    main()
