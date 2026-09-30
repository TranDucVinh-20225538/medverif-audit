#!/usr/bin/env python3
"""QC: items the Gemini 2.5 Flash validator approved that the author rejected (G-INV paraphrase run)."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "qc/inv_manual_review.csv"
LABELS = ROOT / "qc/inv_manual_review_PI_ok_labels.csv"
ATTEMPTS = ROOT / "data/v3/para_attempts_g.jsonl"
PILOT = ROOT / "notes/g_inv_gemini_audit.json"
OUT_MD = ROOT / "notes/qc_gemini_vs_author.md"
OUT_JSON = ROOT / "notes/qc_gemini_vs_author.json"


def norm(s: str) -> str:
    return " ".join((s or "").split())


def main() -> None:
    review = {r["base_id"]: r for r in csv.DictReader(REVIEW.open(encoding="utf-8-sig"))}
    labels = list(csv.DictReader(LABELS.open(encoding="utf-8-sig")))
    passed: dict[str, list[str]] = defaultdict(list)
    for line in ATTEMPTS.open():
        if line.strip():
            a = json.loads(line)
            if str(a.get("passed")) == "True" and "gemini" in str(a.get("validator")):
                passed[a["base_id"]].append(norm(a["text"]))
    cells: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"approved_labelled": 0, "author_rejected": 0, "text_mismatch": 0, "no_gemini_pass": 0})
    for r in labels:
        if r["PI_ok"] not in ("Y", "N"):
            continue
        key = (r["type"], r["mechanism"])
        rw = norm(review[r["base_id"]]["rewrite"])
        ok = passed.get(r["base_id"], [])
        if not ok:
            cells[key]["no_gemini_pass"] += 1
        elif any(t.startswith(rw[:60]) or rw.startswith(t[:60]) for t in ok):
            cells[key]["approved_labelled"] += 1
            cells[key]["author_rejected"] += r["PI_ok"] == "N"
        else:
            cells[key]["text_mismatch"] += 1
    pilot = json.loads(PILOT.read_text())["pairs"]
    rej = [p for p in pilot if p["expect"] == "reject"]
    lines = ["# QC — Gemini 2.5 Flash approved, author rejected", "",
             "Gemini 2.5 Flash is the validator only for the G-INV paraphrase run (`notes/g_full_run_report.md`); "
             "the main pipeline validator is Phi-4 (`qc/qc_stats.md`). Author labels: `qc/inv_manual_review_PI_ok_labels.csv` (PI_ok). "
             "An item counts as Gemini-approved only if the reviewed rewrite matches a Gemini-passed attempt in `data/v3/para_attempts_g.jsonl`.", "",
             "| condition | author rejected / Gemini-approved & labelled | reviewed text ≠ Gemini-passed text | no Gemini pass |", "|---|---:|---:|---:|"]
    for (typ, mech), c in sorted(cells.items()):
        lines.append(f"| INV paraphrase · {typ} · {mech} | **{c['author_rejected']}/{c['approved_labelled']}** | {c['text_mismatch']} | {c['no_gemini_pass']} |")
    lines += ["", f"Pilot audit (`notes/g_inv_gemini_audit.json`): Gemini approved **{sum(p['pipeline_pass_llm_only'] for p in rej)}/{len(rej)}** author must-reject pairs."]
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps({f"{t}|{m}": c for (t, m), c in cells.items()} | {"pilot_must_reject_approved": [sum(p["pipeline_pass_llm_only"] for p in rej), len(rej)]}, indent=1) + "\n")
    print(OUT_MD.read_text())


if __name__ == "__main__":
    main()
