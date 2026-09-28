#!/usr/bin/env python3
"""Build T10 HHEM node30 inputs: doc summaries w/ quantities + M1-style re-expressed copies."""

from __future__ import annotations

import csv
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quantity_norm import normalize_quantities  # noqa: E402
from text_utils import DOSE_RE  # noqa: E402

OUT = ROOT / "data" / "t10" / "hhem_pairs.jsonl"
QC = ROOT / "qc" / "t10_sample.csv"
MANIFEST = ROOT / "data" / "t10" / "manifest_hhem.json"
DOCS = ROOT / "data" / "t10" / "leaderboard_docs.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def has_quantity(text: str) -> bool:
    return bool(DOSE_RE.search(text or ""))


def reexpress(text: str) -> str:
    return normalize_quantities(text or "")


def load_doc_summaries() -> list[dict]:
    rows = read_jsonl(DOCS)
    if rows:
        return rows
    # Placeholder rows from fetched README chunks if no OR-generated summaries yet.
    for name in ("leaderboard_readme.md", "hhem_model_readme.md"):
        readme = ROOT / "data" / "t10" / name
        if readme.is_file():
            break
    else:
        return []
    text = readme.read_text(errors="replace")
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for i, p in enumerate(paras):
        if not has_quantity(p):
            continue
        out.append(
            {
                "doc_id": f"leaderboard_readme_p{i}",
                "model_id": "source_doc",
                "summary": p[:2000],
            }
        )
    return out


def main() -> None:
    summaries = load_doc_summaries()
    pairs = []
    for row in summaries:
        orig = row["summary"]
        rex = reexpress(orig)
        if orig.strip() == rex.strip():
            continue
        pairs.append(
            {
                "instance_id": f"{row['doc_id']}__{row.get('model_id', 'na')}",
                "doc_id": row["doc_id"],
                "model_id": row.get("model_id"),
                "claim_original": orig,
                "claim_reexpressed": rex,
                "evidence": row.get("source_doc") or row.get("evidence") or "",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for row in pairs:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    rng = random.Random(20260929)
    sample = list(pairs)
    rng.shuffle(sample)
    QC.parent.mkdir(parents=True, exist_ok=True)
    with QC.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["instance_id", "doc_id", "model_id", "claim_original", "claim_reexpressed", "PI_ok", "note"])
        qc_rows = sample[:30]
        while len(qc_rows) < 30:
            qc_rows.append(
                {
                    "instance_id": f"t10_qc_pad_{len(qc_rows)}",
                    "doc_id": "pending",
                    "model_id": "",
                    "claim_original": "",
                    "claim_reexpressed": "",
                }
            )
        for row in qc_rows:
            w.writerow(
                [
                    row["instance_id"],
                    row["doc_id"],
                    row.get("model_id", ""),
                    (row.get("claim_original") or "")[:500],
                    (row.get("claim_reexpressed") or "")[:500],
                    "",
                    "",
                ]
            )

    manifest = {"n_pairs": len(pairs), "n_qc_sample": min(30, len(pairs)), "paths": {"hhem_pairs": str(OUT.relative_to(ROOT)), "qc": str(QC.relative_to(ROOT))}}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
