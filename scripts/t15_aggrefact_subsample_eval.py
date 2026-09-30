#!/usr/bin/env python3
"""Stratified 3k AggreFact subsample (base+ft GPU/CPU) + bootstrap CI report."""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402

SEED = 42
N_SAMPLE = 3000


def row_id(row: dict) -> str:
    if row.get("instance_id"):
        return str(row["instance_id"])
    return str(row.get("contamination_identifier") or row["id"])


def stratified_sample(rows: list[dict], n: int, seed: int) -> list[dict]:
    by_ds: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_ds[r.get("dataset", "?")].append(r)
    total = len(rows)
    rng = random.Random(seed)
    picked: list[dict] = []
    for ds, items in sorted(by_ds.items()):
        k = max(1, round(n * len(items) / total))
        picked.extend(rng.sample(items, min(k, len(items))))
    if len(picked) > n:
        rng.shuffle(picked)
        picked = picked[:n]
    elif len(picked) < n:
        rest = [r for r in rows if r not in picked]
        rng.shuffle(rest)
        picked.extend(rest[: n - len(picked)])
    return picked


def write_sample_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            nr = dict(r)
            nr.setdefault("instance_id", row_id(r))
            if not (nr.get("evidence") or "").strip() and (nr.get("doc") or "").strip():
                nr["evidence"] = nr["doc"]
            f.write(json.dumps(nr, ensure_ascii=False) + "\n")


def bootstrap_paired(base_acc: list[bool], ft_acc: list[bool], *, n_boot: int = 2000) -> tuple[float, float]:
    rng = random.Random(SEED)
    n = len(base_acc)
    diffs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        b = sum(base_acc[i] for i in idx) / n
        f = sum(ft_acc[i] for i in idx) / n
        diffs.append(f - b)
    diffs.sort()
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot)]
    return lo, hi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=N_SAMPLE)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    test = read_jsonl(ROOT / "data/t8/aggrefact/test.jsonl")
    sample = stratified_sample(test, args.n, args.seed)
    sample_path = ROOT / "data/t15/aggrefact_subsample_3000.jsonl"
    write_sample_jsonl(sample, sample_path)
    meta = {
        "n": len(sample),
        "seed": args.seed,
        "by_dataset": {},
    }
    for r in sample:
        ds = r.get("dataset", "?")
        meta["by_dataset"][ds] = meta["by_dataset"].get(ds, 0) + 1
    (ROOT / "notes/t15_aggrefact_subsample.json").write_text(json.dumps(meta, indent=2) + "\n")

    for leg in ("base", "ft"):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/t15_aggrefact_gpu_eval.py"),
                "--leg",
                leg,
                "--instances",
                str(sample_path),
                "--out",
                str(ROOT / f"results/raw/t15/{leg}_aggrefact_subsample_{args.n}.jsonl"),
            ],
            check=True,
            cwd=str(ROOT),
        )

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/t15_aggrefact_subsample_report.py"), "--n", str(args.n)],
        check=True,
        cwd=str(ROOT),
    )
    print(json.dumps({"sample": str(sample_path), "n": len(sample)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
