#!/usr/bin/env python3
"""T18: general-domain (Wikipedia-eval slot) dose bases via author_whitelist perturb."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_main_ext_pack import cand_to_base, forbidden_keys  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402

POOL = ROOT / "data/expand/candidates_pool.jsonl"
OUT_BASES = ROOT / "data/t18/bases_t18.jsonl"
OUT_INST = ROOT / "data/t18/instances_t18.jsonl"
QC = ROOT / "qc/t18_sample.csv"
MANIFEST = ROOT / "notes/t18_manifest.json"

# Non-textbook / general reference books in expand pool (Wikipedia-style eval cohort).
T18_BOOK_PREFIXES = (
    "Pharmacology_Katzung",
    "InternalMed_Harrison",
)


def select_t18(max_bases: int) -> list[dict]:
    forbid_b, forbid_p, forbid_h = forbidden_keys()
    picked: list[dict] = []
    seq = 0
    for row in read_jsonl(POOL):
        book = str(row.get("book") or "")
        if any(book.startswith(p) for p in T18_BOOK_PREFIXES):
            continue
        if row.get("type") != "DOSE":
            continue
        seq += 1
        base_id = f"T18{seq:04d}"
        if base_id in forbid_b:
            continue
        base = cand_to_base(row, base_id)
        if not base:
            continue
        base["subset"] = "t18_wikipedia"
        picked.append(base)
        if len(picked) >= max_bases:
            break
    return picked


def run_perturb(bases: list[dict], out_inst: Path, failures: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tmp:
        for b in bases:
            tmp.write(json.dumps(b, ensure_ascii=False) + "\n")
        base_path = Path(tmp.name)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/perturb.py"),
            "--base",
            str(base_path),
            "--out",
            str(out_inst),
            "--failures",
            str(failures),
            "--unit-inv-policy",
            "author_whitelist",
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
    )


def write_qc(instances: list[dict], n: int = 40) -> None:
    import random

    rng = random.Random(18)
    sample = instances if len(instances) <= n else rng.sample(instances, n)
    with QC.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["instance_id", "base_id", "condition", "PI_ok", "notes"])
        for row in sample:
            w.writerow([row["instance_id"], row["base_id"], row["condition"], "", ""])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--max-bases", type=int, default=30)
    p.add_argument("--smoke-bases", type=int, default=0)
    args = p.parse_args()
    n = args.smoke_bases if args.smoke_bases > 0 else args.max_bases
    bases = select_t18(n)
    OUT_BASES.parent.mkdir(parents=True, exist_ok=True)
    with OUT_BASES.open("w") as handle:
        for b in bases:
            handle.write(json.dumps(b, ensure_ascii=False) + "\n")
    fail_path = ROOT / "notes/t18_perturb_failures.json"
    run_perturb(bases, OUT_INST, fail_path)
    instances = read_jsonl(OUT_INST)
    write_qc(instances)
    manifest = {
        "bases": len(bases),
        "instances": len(instances),
        "note": "General-domain doses (non-core textbooks); Wikipedia crawl deferred.",
        "instances_path": str(OUT_INST.relative_to(ROOT)),
        "qc": str(QC.relative_to(ROOT)),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
