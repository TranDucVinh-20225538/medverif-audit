#!/usr/bin/env python3
"""(B5) Report for the real-RAG expansion -> notes/journal_rag_expansion.md (+ JSON).

Cells (per generator and pooled), C0-conditional like the paper / T24b:
  C0 PASS; conversion PASS | C0; value x2 / x10 FAIL | C0; unit-up / unit-down FAIL | C0.
95% CIs: percentile bootstrap clustered by question_id (B resamples, seed 42).
Includes retrieval diagnostics, answer/evidence dose-match rates, spend vs cap, and -- when present --
the second fine-tune models scored on this pack (results/journal/ft/scores/*__rag.jsonl).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import CAP_USD, FT_DIR, JR, NOTES, RAG_DIR, ROOT, read_jsonl, spent_usd  # noqa: E402

INST = ROOT / "data/journal/instances_rag.jsonl"
CELLS = [("C0 PASS", "RAG-C0", "PASS", False), ("conv PASS given C0", "RAG-conv", "PASS", True),
         ("value×2 FAIL given C0", "RAG-value-x2", "FAIL", True), ("value×10 FAIL given C0", "RAG-value-x10", "FAIL", True),
         ("unit-up FAIL given C0", "RAG-unit-up", "FAIL", True), ("unit-down FAIL given C0", "RAG-unit-down", "FAIL", True)]


def load_scores():
    by = defaultdict(dict)
    for p in sorted((RAG_DIR / "scores").glob("*.jsonl")):
        for r in read_jsonl(p):
            v = r.get("verifier") or p.stem
            if r.get("verdict") in ("PASS", "FAIL"):
                by[v][r["instance_id"]] = r["verdict"]
    for p in sorted((FT_DIR / "scores").glob("*__rag.jsonl")):
        for r in read_jsonl(p):
            if r.get("verdict") in ("PASS", "FAIL"):
                by["ft:" + p.stem.replace("__rag", "")][r["instance_id"]] = r["verdict"]
    return by


def cell(inst, verd, cond, want, conditional):
    c0ok = {r["base_id"] for r in inst if r["condition"] == "RAG-C0" and verd.get(r["instance_id"]) == "PASS"}
    groups = defaultdict(lambda: [0, 0])
    for r in inst:
        if r["condition"] != cond or r["instance_id"] not in verd:
            continue
        if conditional and r["base_id"] not in c0ok:
            continue
        g = groups[r["question_id"]]
        g[1] += 1
        g[0] += int(verd[r["instance_id"]] == want)
    return list(groups.values())


def boot(groups, B, seed=42):
    den = sum(d for _, d in groups)
    if not den:
        return None, None, None, 0, 0
    point = sum(n for n, _ in groups) / den
    if len(groups) < 2:
        return point, None, None, den, len(groups)
    rng = random.Random(seed)
    st = []
    for _ in range(B):
        s = [groups[rng.randrange(len(groups))] for _ in groups]
        d = sum(x[1] for x in s)
        if d:
            st.append(sum(x[0] for x in s) / d)
    st.sort()
    return point, st[int(0.025 * (len(st) - 1))], st[int(0.975 * (len(st) - 1))], den, len(groups)


def fmt(t):
    p, lo, hi, n, q = t
    if p is None:
        return "NA"
    return "%.1f%% [%.1f, %.1f] (n=%d, q=%d)" % (100 * p, 100 * (lo or p), 100 * (hi or p), n, q) if lo is not None else "%.1f%% (n=%d)" % (100 * p, n)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out-md", default=str(NOTES / "journal_rag_expansion.md"))
    ap.add_argument("--instances", default=str(INST))
    args = ap.parse_args()
    inst = read_jsonl(Path(args.instances))
    scores = load_scores()
    gens = sorted({r["generator"] for r in inst})
    man = json.loads((RAG_DIR / "build_manifest.json").read_text()) if (RAG_DIR / "build_manifest.json").is_file() else {}
    retr_marker = JR / "markers/B2_retrieve.done"
    retr = json.loads(retr_marker.read_text()) if retr_marker.is_file() else {}
    qn = len([r for r in read_jsonl(RAG_DIR / "questions.jsonl") if r.get("valid")])
    md = ["# Real-RAG expansion (journal revision)", "",
          "Pipeline: textbook dose sentences disjoint from the main bases, earlier packs and T15 training bases -> "
          "LLM-written question -> BM25 + dense (%s) retrieval over MedRAG textbooks, RRF top-k -> 2 generators "
          "(%s; temperature 0, pinned providers) -> same dose-span edits as the main pack -> checkers + judges." % (
              retr.get("dense_model", "?"), ", ".join(gens)), "",
          "- Valid questions: **%d**; answers: %s; instances: %s" % (qn, man.get("answers"), man.get("instances")),
          "- Answer/evidence dose match: %s" % json.dumps(man.get("status_counts", {})),
          "- Gold-passage recall: %s (corpus chunks %s)" % (json.dumps(retr.get("gold_recall", {})), retr.get("corpus_chunks")),
          "- API spend so far (all chain stages): $%.4f of $%.2f cap" % (spent_usd(), CAP_USD),
          "- Human check: `qc/jr_rag_human_check.csv` (%s rows; fill the two Y/N columns)" % man.get("human_check_rows"), "",
          "C0-conditional cells; 95%% CI = percentile bootstrap over question_id (%d resamples)." % args.boot, ""]
    res = {}
    for scope in ["pooled"] + gens:
        sub = inst if scope == "pooled" else [r for r in inst if r["generator"] == scope]
        md += ["## %s" % scope, "", "| verifier | " + " | ".join(c[0] for c in CELLS) + " |", "|---|" + "---|" * len(CELLS)]
        for v in sorted(scores):
            cells = [boot(cell(sub, scores[v], c, w, cond), args.boot) for _, c, w, cond in CELLS]
            res.setdefault(scope, {})[v] = {CELLS[i][0]: cells[i] for i in range(len(CELLS))}
            md.append("| %s | %s |" % (v, " | ".join(fmt(c) for c in cells)))
        md.append("")
    Path(args.out_md).write_text("\n".join(md) + "\n", encoding="utf-8")
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    (RAG_DIR / "report.json").write_text(json.dumps(res, indent=1) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
