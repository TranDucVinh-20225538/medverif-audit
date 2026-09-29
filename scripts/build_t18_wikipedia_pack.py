#!/usr/bin/env python3
"""T18: non-medical Wikipedia sentences (HF streaming) with one metric quantity."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import (  # noqa: E402
    DOSE_CONTEXT_RE,
    DRUG_RE,
    join_window,
    normalize_ws,
    split_sentences,
    t18_metric_inv_conversion,
    t18_metric_matches,
)
from verifiers.io_utils import read_jsonl  # noqa: E402

OUT_BASES = ROOT / "data/t18/bases_t18.jsonl"
OUT_INST = ROOT / "data/t18/instances_t18.jsonl"
QC = ROOT / "qc/t18_sample.csv"
MANIFEST = ROOT / "notes/t18_manifest.json"

SCIENCE_RE = re.compile(
    r"\b(?:engineer|engineering|physics|chemistry|biology|geology|geography|"
    r"climate|planet|mountain|river|ocean|continent|architecture|electric|"
    r"mechanical|structural|satellite|orbit|velocity|temperature|pressure)\b",
    re.I,
)


def sentence_ok(sentence: str) -> bool:
    if len(sentence) < 40 or len(sentence) > 320:
        return False
    if DRUG_RE.search(sentence) or DOSE_CONTEXT_RE.search(sentence):
        return False
    if not SCIENCE_RE.search(sentence):
        return False
    matches = t18_metric_matches(sentence)
    if len(matches) != 1:
        return False
    span = matches[0].group(0)
    if not t18_metric_inv_conversion(span, sentence):
        return False
    return True


def parquet_bases(max_bases: int, shard_dir: Path, max_shards: int = 2) -> list[dict]:
    """Load 1–2 local parquet shards (no HF streaming)."""
    import pyarrow.parquet as pq

    shards = sorted(shard_dir.glob("train-*.parquet"))[:max_shards]
    if not shards:
        raise FileNotFoundError(f"No parquet shards under {shard_dir}")
    picked: list[dict] = []
    seq = 0
    for shard in shards:
        table = pq.read_table(shard, columns=["title", "text"])
        for art_i in range(table.num_rows):
            if len(picked) >= max_bases:
                break
            title = table.column("title")[art_i].as_py()
            text = table.column("text")[art_i].as_py() or ""
            sents = split_sentences(text)
            for idx, sentence in enumerate(sents):
                if not sentence_ok(sentence):
                    continue
                m = t18_metric_matches(sentence)[0]
                span = m.group(0)
                pos = sentence.find(span)
                if pos < 0:
                    continue
                evidence, s0, _s1 = join_window(sents, idx)
                epos = evidence.find(span)
                if epos < 0:
                    continue
                seq += 1
                base_id = f"T18{seq:04d}"
                picked.append(
                    {
                        "id": base_id,
                        "type": "DOSE",
                        "t18_metric": True,
                        "subset": "t18_wikipedia",
                        "claim": sentence,
                        "evidence": evidence,
                        "claim_span_start": pos,
                        "claim_span_end": pos + len(span),
                        "evidence_span_start": epos,
                        "evidence_span_end": epos + len(span),
                        "target_span_claim": span,
                        "target_span_evidence": span,
                        "target_sentence": sentence,
                        "book": f"Wikipedia:{str(title)[:80]}",
                        "source_passage_id": f"wiki:{title}:{art_i}",
                        "dose_number": m.group(1),
                        "dose_unit": m.group(2),
                    }
                )
                if len(picked) >= max_bases:
                    break
        if len(picked) >= max_bases:
            break
    return picked


def stream_bases(max_bases: int, max_articles: int) -> list[dict]:
    from datasets import load_dataset

    ds = load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)
    picked: list[dict] = []
    seq = 0
    for art_i, row in enumerate(ds):
        if art_i >= max_articles or len(picked) >= max_bases:
            break
        text = row.get("text") or ""
        title = str(row.get("title") or "wikipedia")
        sents = split_sentences(text)
        for idx, sentence in enumerate(sents):
            if not sentence_ok(sentence):
                continue
            m = t18_metric_matches(sentence)[0]
            span = m.group(0)
            pos = sentence.find(span)
            if pos < 0:
                continue
            evidence, s0, _s1 = join_window(sents, idx)
            epos = evidence.find(span)
            if epos < 0:
                continue
            seq += 1
            base_id = f"T18{seq:04d}"
            picked.append(
                {
                    "id": base_id,
                    "type": "DOSE",
                    "t18_metric": True,
                    "subset": "t18_wikipedia",
                    "claim": sentence,
                    "evidence": evidence,
                    "claim_span_start": pos,
                    "claim_span_end": pos + len(span),
                    "evidence_span_start": epos,
                    "evidence_span_end": epos + len(span),
                    "target_span_claim": span,
                    "target_span_evidence": span,
                    "target_sentence": sentence,
                    "book": f"Wikipedia:{title[:80]}",
                    "source_passage_id": f"wiki:{title}:{art_i}",
                    "dose_number": m.group(1),
                    "dose_unit": m.group(2),
                }
            )
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


def write_qc(instances: list[dict]) -> None:
    inv = [r for r in instances if r.get("condition") == "INV-claim"]
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["instance_id", "base_id", "condition", "PI_ok", "notes"])
        for row in inv:
            w.writerow([row["instance_id"], row["base_id"], row["condition"], "", ""])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--max-bases", type=int, default=100)
    p.add_argument("--smoke-bases", type=int, default=0)
    p.add_argument("--max-articles", type=int, default=8000)
    p.add_argument(
        "--parquet-dir",
        type=Path,
        default=ROOT / ".cache/huggingface/wikipedia_20231101.en_parquet",
        help="local parquet shards (preferred over streaming)",
    )
    p.add_argument("--parquet-shards", type=int, default=2)
    p.add_argument("--use-streaming", action="store_true")
    args = p.parse_args()
    n = args.smoke_bases if args.smoke_bases > 0 else args.max_bases
    if args.use_streaming:
        bases = stream_bases(n, args.max_articles)
    else:
        bases = parquet_bases(n, args.parquet_dir, args.parquet_shards)
    if len(bases) < n:
        raise RuntimeError(f"T18: only found {len(bases)} bases (wanted {n})")
    OUT_BASES.parent.mkdir(parents=True, exist_ok=True)
    with OUT_BASES.open("w") as handle:
        for b in bases:
            handle.write(json.dumps(b, ensure_ascii=False) + "\n")
    fail_path = ROOT / "notes/t18_perturb_failures.json"
    run_perturb(bases, OUT_INST, fail_path)
    instances = read_jsonl(OUT_INST)
    write_qc(instances)
    manifest = {
        "source": "wikimedia/wikipedia 20231101.en (streaming)",
        "domain": "non_medical science/geography/engineering",
        "metric_units": "km/m/cm, kg/g, L/mL, W/kW",
        "bases": len(bases),
        "instances": len(instances),
        "instances_path": str(OUT_INST.relative_to(ROOT)),
        "qc": str(QC.relative_to(ROOT)),
        "legacy_medical_mislabel": "data/t18_medical_expand/ (NOT T18)",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
