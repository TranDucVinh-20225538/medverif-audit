#!/usr/bin/env python3
"""Per-pack V4 Llama coverage: instance ids vs v4_ragas_nli.llama.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "notes/v4_llama_rescore_packs.json"
VERIFIER = "v4_ragas_nli"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def pack_status(pack: dict) -> dict:
    inst_p = ROOT / pack["instances"]
    llama_p = ROOT / pack["score_dir"] / f"{VERIFIER}.llama.jsonl"
    want = {
        r["instance_id"]
        for r in read_jsonl(inst_p)
        if r.get("valid", True) and r.get("instance_id")
    }
    have: set[str] = set()
    for row in read_jsonl(llama_p):
        if row.get("instance_id") and row.get("api_model") and row.get("verdict"):
            have.add(row["instance_id"])
    missing = sorted(want - have)
    return {
        "id": pack["id"],
        "instances": str(inst_p.relative_to(ROOT)),
        "llama": str(llama_p.relative_to(ROOT)),
        "expected": len(want),
        "scored": len(want & have),
        "missing": len(missing),
        "complete": len(missing) == 0 and len(want) > 0,
        "missing_sample": missing[:5],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 if all packs complete, else 1",
    )
    args = parser.parse_args()
    data = json.loads(MANIFEST.read_text())
    rows = [pack_status(p) for p in data["packs"]]
    payload = {"packs": rows, "all_complete": all(r["complete"] for r in rows)}
    if args.json or not args.check:
        print(json.dumps(payload, indent=2))
    if args.check:
        sys.exit(0 if payload["all_complete"] else 1)


if __name__ == "__main__":
    main()
