#!/usr/bin/env python3
"""main_ext: author-whitelist INV bases disjoint from main + T15."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import normalize_ws  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402

POOL = ROOT / "data/expand/candidates_pool.jsonl"
MAIN = ROOT / "data/v3/instances_main.jsonl"
T15_BASES = ROOT / "data/t15/bases.jsonl"
OUT_BASES = ROOT / "data/main_ext/bases_main_ext.jsonl"
OUT_INST = ROOT / "data/main_ext/instances_main_ext.jsonl"
QC = ROOT / "qc/main_ext_review.csv"
MANIFEST = ROOT / "notes/main_ext_manifest.json"


def sentence_hash(text: str) -> str:
    return hashlib.sha1(normalize_ws(text).casefold().encode()).hexdigest()


def forbidden_keys() -> tuple[set[str], set[str], set[str]]:
    base_ids: set[str] = set()
    passage_ids: set[str] = set()
    sent_hashes: set[str] = set()
    for path in (MAIN, T15_BASES):
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            if row.get("base_id"):
                base_ids.add(row["base_id"])
            if row.get("id"):
                base_ids.add(row["id"])
            if row.get("source_passage_id"):
                passage_ids.add(row["source_passage_id"])
            for key in ("target_sentence", "claim", "evidence"):
                if row.get(key):
                    sent_hashes.add(sentence_hash(str(row[key])))
    if T15_BASES.is_file():
        for row in read_jsonl(T15_BASES):
            if row.get("source_passage_id"):
                passage_ids.add(row["source_passage_id"])
            if row.get("target_sentence"):
                sent_hashes.add(sentence_hash(row["target_sentence"]))
    return base_ids, passage_ids, sent_hashes


def cand_to_base(row: dict, base_id: str) -> dict | None:
    if row.get("type") != "DOSE":
        return None
    ts = row.get("target_sentence") or ""
    span = row.get("target_span") or ""
    pos = ts.find(span)
    if pos < 0:
        return None
    evid = row.get("evidence") or ""
    epos = evid.find(span)
    if epos < 0:
        # allow spacing-relaxed match on evidence
        epos = evid.replace(" ", "").find(span.replace(" ", ""))
        if epos < 0:
            return None
        epos = evid.find(span.split()[0]) if span.split() else -1
    if epos < 0:
        return None
    claim = ts
    c0, c1 = pos, pos + len(span)
    e0, e1 = evid.find(span), evid.find(span) + len(span)
    if e0 < 0:
        return None
    return {
        "id": base_id,
        "type": "DOSE",
        "claim": claim,
        "evidence": evid,
        "claim_span_start": c0,
        "claim_span_end": c1,
        "evidence_span_start": e0,
        "evidence_span_end": e1,
        "target_span_claim": span,
        "target_span_evidence": span,
        "subset": "main_ext",
        "book": row.get("book"),
        "source_passage_id": row.get("source_passage_id"),
    }


def select_candidates(max_bases: int) -> list[dict]:
    forbid_b, forbid_p, forbid_h = forbidden_keys()
    picked: list[dict] = []
    seq = 0
    for row in read_jsonl(POOL):
        if row.get("type") != "DOSE":
            continue
        pid = row.get("source_passage_id") or ""
        if pid in forbid_p:
            continue
        ts = row.get("target_sentence") or ""
        if sentence_hash(ts) in forbid_h:
            continue
        seq += 1
        base_id = f"EXT{seq:04d}"
        if base_id in forbid_b:
            continue
        base = cand_to_base(row, base_id)
        if not base:
            continue
        picked.append(base)
        if len(picked) >= max_bases:
            break
    return picked


def run_perturb(bases: list[dict], out_inst: Path, failures: Path) -> int:
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
    return sum(1 for _ in out_inst.open() if _.strip())


def write_qc(instances: list[dict], n_review: int = 40) -> None:
    import random

    rng = random.Random(42)
    sample = instances if len(instances) <= n_review else rng.sample(instances, n_review)
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "instance_id",
                "base_id",
                "condition",
                "magnitude",
                "PI_ok",
                "notes",
            ]
        )
        for row in sample:
            w.writerow([row["instance_id"], row["base_id"], row["condition"], row.get("magnitude"), "", ""])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--max-bases", type=int, default=40)
    p.add_argument("--smoke-bases", type=int, default=0, help="if >0, only build this many (smoke test)")
    args = p.parse_args()
    n = args.smoke_bases if args.smoke_bases > 0 else args.max_bases
    bases = select_candidates(n)
    OUT_BASES.parent.mkdir(parents=True, exist_ok=True)
    with OUT_BASES.open("w") as handle:
        for b in bases:
            handle.write(json.dumps(b, ensure_ascii=False) + "\n")
    fail_path = ROOT / "notes/main_ext_perturb_failures.json"
    n_inst = run_perturb(bases, OUT_INST, fail_path)
    instances = read_jsonl(OUT_INST)
    write_qc(instances)
    manifest = {
        "bases": len(bases),
        "instances": n_inst,
        "bases_path": str(OUT_BASES.relative_to(ROOT)),
        "instances_path": str(OUT_INST.relative_to(ROOT)),
        "qc": str(QC.relative_to(ROOT)),
        "unit_inv_policy": "author_whitelist",
        "smoke": args.smoke_bases > 0,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
