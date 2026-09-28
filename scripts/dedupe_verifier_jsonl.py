#!/usr/bin/env python3
"""Dedupe verifier JSONL by instance_id; drop rows whose content sha1 is stale vs instances."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from raw_jsonl_backup import backup_raw  # noqa: E402


def content_sha1(claim: str, evidence: str) -> str:
    return hashlib.sha1(f"{claim}\n{evidence}".encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def instance_sha_map(instances_path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in read_jsonl(instances_path):
        iid = row["instance_id"]
        claim = row.get("claim") or ""
        evidence = row.get("evidence") or ""
        out[iid] = row.get("content_sha1") or content_sha1(claim, evidence)
    return out


def dedupe(path: Path, valid_ids: set[str], sha_by_id: dict[str, str]) -> tuple[list[dict], dict]:
    rows = read_jsonl(path)
    stats: dict = {
        "input_lines": len(rows),
        "duplicate_instance_id": 0,
        "unknown_instance_id": 0,
        "stale_content_sha1": 0,
        "kept": 0,
    }
    by_id: dict[str, dict] = {}
    dup_ids: Counter[str] = Counter()
    unknown_ids: list[str] = []
    stale_ids: list[str] = []
    for row in rows:
        iid = row["instance_id"]
        if iid in by_id:
            stats["duplicate_instance_id"] += 1
            dup_ids[iid] += 1
        if iid not in valid_ids:
            stats["unknown_instance_id"] += 1
            unknown_ids.append(iid)
            continue
        claim = row.get("claim") or ""
        evidence = row.get("evidence") or ""
        if claim or evidence:
            expected = sha_by_id[iid]
            got = row.get("content_sha1") or content_sha1(claim, evidence)
            if got != expected:
                stats["stale_content_sha1"] += 1
                stale_ids.append(iid)
                continue
        by_id[iid] = row
    kept = list(by_id.values())
    stats["kept"] = len(kept)
    stats["sample_duplicate_ids"] = [k for k, _ in dup_ids.most_common(10)]
    stats["sample_stale_ids"] = stale_ids[:10]
    stats["sample_unknown_ids"] = unknown_ids[:10]
    return kept, stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", type=Path, required=True)
    ap.add_argument("--scores", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None, help="default: overwrite --scores")
    ap.add_argument("--dry-run", action="store_true", help="report only; do not write scores")
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    args.instances = args.instances.resolve()
    args.scores = args.scores.resolve()
    if args.out:
        args.out = args.out.resolve()
    sha_map = instance_sha_map(args.instances)
    valid_ids = set(sha_map)
    kept, stats = dedupe(args.scores, valid_ids, sha_map)
    out = args.out or args.scores
    if not args.dry_run:
        backup_raw(args.scores)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w") as handle:
            for row in kept:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "instances": str(args.instances.relative_to(ROOT)),
        "n_instances": len(sha_map),
        "scores": str(args.scores.relative_to(ROOT)),
        "out": str(out.relative_to(ROOT)),
        **stats,
    }
    report_path = args.report or ROOT / "notes" / f"dedupe_{args.scores.stem}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
