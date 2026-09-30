#!/usr/bin/env python3
"""T24b report: rates conditional on C0 PASS; cluster bootstrap over questions."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import bootstrap_rate, read_jsonl  # noqa: E402
from t13_best_of_n_report import score_from_row  # noqa: E402

INST = ROOT / "data/t24/instances_t24b.jsonl"
RAW = ROOT / "results/raw/t24b"
OUT = ROOT / "notes/t24b_report.md"
MANIFEST = ROOT / "notes/t24b_build_manifest.json"
T6_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"

CONDITIONS = (
    ("T24b-C0", "C0 PASS rate", "pass"),
    ("T24b-unit-up", "Unit-up FAIL | C0 PASS", "fail"),
    ("T24b-unit-down", "Unit-down FAIL | C0 PASS", "fail"),
    ("T24b-value-x10", "Value×10 FAIL | C0 PASS", "fail"),
)

CHECKERS = (
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
    "v2a_minicheck",
    "v3_alignscore",
    "v4_ragas_nli",
    "v1_medscore",
)


def verdict(row: dict) -> str | None:
    score, _ = score_from_row(row)
    if score is None:
        return None
    return "PASS" if score >= 0.5 else "FAIL"


def load_scores(slug: str) -> dict[str, dict]:
    paths = [RAW / f"{slug}.jsonl"]
    if (ROOT / "notes/t6a_eco_checkers.json").is_file():
        id_to = {c["id"]: c["jsonl"] for c in json.loads(T6_MANIFEST.read_text())["checkers"]}
        if slug in id_to:
            paths.insert(0, RAW / id_to[slug])
    out: dict[str, dict] = {}
    for path in paths:
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            out[row["instance_id"]] = row
    return out


def fmt_boot(b: dict) -> str:
    if b["rate"] is None:
        return f"— (n={b['den']})"
    lo = b["lo"]
    hi = b["hi"]
    ci = f" [{100*lo:.1f}%, {100*hi:.1f}%]" if lo is not None and hi is not None else ""
    return f"{100*b['rate']:.1f}%{ci} (n={b['den']}, q={b['n_bases']})"


def main() -> None:
    by_q: dict[str, list[dict]] = defaultdict(list)
    for row in read_jsonl(INST):
        by_q[row["question_id"]].append(row)

    lines = [
        "# T24b — real-RAG dose prevalence & perturbation (P1)",
        "",
        "Author labels: `qc/t24_labels.csv` (**FINAL**). "
        "**55** unique Y questions (56 Y minus **T24_003**; duplicate rows excluded). "
        "**8** unique N → appendix only (span-matcher errors). "
        "**0/56** Y answers re-express a unit → **prevalence**, not in-the-wild conversion.",
        "",
    ]
    if MANIFEST.is_file():
        man = json.loads(MANIFEST.read_text())
        lines.append(f"- Instances built: **{man.get('instances_written')}**")
        lines.append(f"- Build manifest: `{MANIFEST.relative_to(ROOT)}` · skips: **{len(man.get('skips') or [])}**")
        lines.append(f"- Edit log: `{ROOT / 'notes/t24b_edit_log.jsonl'}`")
        lines.append("")

    lines.extend(
        [
            "Conditional cells: perturbation metrics among questions where **C0 PASS**. "
            "Bootstrap: **1000** resamples cluster by `question_id`, seed **42**.",
            "",
            "| Checker | C0 PASS | Unit-up FAIL|C0 | Unit-down FAIL|C0 | Value×10 FAIL|C0 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for slug in CHECKERS:
        scores = load_scores(slug)
        if not scores:
            lines.append(f"| {slug} | — (no scores) | | | |")
            continue
        cells: list[str] = []
        for cond, _label, mode in CONDITIONS:
            groups: list[tuple[int, int]] = []
            for qid, inst_rows in by_q.items():
                c0_id = f"{qid}__T24b-C0"
                c0 = scores.get(c0_id)
                if not c0:
                    continue
                v0 = verdict(c0)
                if v0 is None:
                    continue
                if cond != "T24b-C0" and v0 != "PASS":
                    continue
                target = scores.get(f"{qid}__{cond}")
                if not target:
                    continue
                vt = verdict(target)
                if vt is None:
                    continue
                hit = int(vt == "PASS") if mode == "pass" else int(vt == "FAIL")
                groups.append((hit, 1))
            cells.append(fmt_boot(bootstrap_rate(groups)))
        lines.append(f"| {slug} | {' | '.join(cells)} |")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
