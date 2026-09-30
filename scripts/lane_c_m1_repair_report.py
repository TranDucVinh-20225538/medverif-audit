#!/usr/bin/env python3
"""Lane C: M1 repair-after-norm summary for API verifiers on main pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import bootstrap_rate, load_joined_from_records, read_jsonl  # noqa: E402
from review_filters import analysis_keep_row  # noqa: E402

INST = ROOT / "data/lane_c/m1_h2_main.jsonl"
RAW = ROOT / "results/raw"
RAW_M1 = ROOT / "results/raw_m1/lane_c"
OUT = ROOT / "notes/m1_repair_after_norm.md"

VERIFIERS = (
    ("v1_medscore", "V1"),
    ("v1b_medscore", "V1b"),
    ("v1c_medscore", "V1c"),
    ("v4_ragas_nli", "V4-Llama"),
    ("v5_ragas_nli", "V5"),
    ("v6_ragas_gpt4o_mini", "V6-gpt4o"),
    ("v6_ragas_haiku45", "V6-haiku"),
    ("v6_ragas_llama31_8b", "V6-llama8b"),
    ("v6_ragas_mistral_small32", "V6-mistral"),
)


def load_scores(raw_dir: Path, slug: str) -> list[dict]:
    if slug == "v4_ragas_nli":
        p = raw_dir / "v4_ragas_nli.llama.jsonl"
        if not p.is_file():
            p = raw_dir / "v4_ragas_nli.jsonl"
    else:
        p = raw_dir / f"{slug}.jsonl"
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.open() if l.strip()]


def main() -> None:
    instances = read_jsonl(INST)
    lines = [
        "# M1 repair after quantity normalization (Lane C / H2)",
        "",
        f"Pack: `{INST.relative_to(ROOT)}` (n={len(instances)}).",
        "Compare `results/raw` (before) vs `results/raw_m1/lane_c` (M1=1).",
        "",
        "| Verifier | slice | before | after M1 |",
        "|---|---|---:|---:|",
    ]
    for slug, label in VERIFIERS:
        before = load_scores(RAW, slug)
        after = load_scores(RAW_M1, slug)
        if not before and not after:
            lines.append(f"| {label} | — | NA | NA |")
            continue
        # minimal: INV-unit FAIL rate | C0 pass
        lines.append(f"| {label} | INV-unit PASS | see raw | see raw_m1 |")
    lines.append("")
    lines.append("_Verbatim LLM judge explanations: inspect FAIL rows in lane_c JSONL `raw_output`._")
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT.read_text())


if __name__ == "__main__":
    main()
