#!/usr/bin/env python3
"""T24 mini RAG: 80 dose questions, BM25 textbook+FDA, cheap LLM answer, surface-diff review CSV."""

from __future__ import annotations

import csv
import json
import math
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from llm_client import chat  # noqa: E402
from quantity_norm import canonicalize_dose_span  # noqa: E402
from text_utils import DOSE_RE  # noqa: E402
from t24_openrouter_budget import assert_under_cap  # noqa: E402

OUT_CSV = ROOT / "qc/t24_review.csv"
OUT_JSON = ROOT / "notes/t24_manifest.json"
LABEL_DIR = ROOT / "data/t20/labels"
CAP_USD = float(os.environ.get("MEDVERIF_T24_CAP_USD", "2"))
N_QUESTIONS = 80
SEED = 42
DEFAULT_MODEL = os.environ.get("MEDVERIF_T24_MODEL", "mistralai/mistral-small-3.2-24b-instruct")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")[:80]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def bm25_index(docs: list[list[str]]) -> dict:
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(doc))
    n = len(docs)
    idf = {t: math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) for t in df}
    return {"idf": idf, "docs": docs, "n": n}


def bm25_score(query: list[str], doc: list[str], idf: dict, avgdl: float, k1=1.5, b=0.75) -> float:
    tf = Counter(doc)
    dl = len(doc) or 1
    score = 0.0
    for term in query:
        if term not in idf:
            continue
        freq = tf.get(term, 0)
        denom = freq + k1 * (1 - b + b * dl / avgdl)
        score += idf[term] * freq * (k1 + 1) / (denom or 1)
    return score


def first_dose_span(text: str) -> tuple[str, str]:
    m = DOSE_RE.search(text or "")
    if not m:
        return "", ""
    surf = m.group(0).strip()
    try:
        canon = canonicalize_dose_span(m.group(1), m.group(2))
    except Exception:
        canon = surf
    return surf, canon


def fda_dosage_text(drug: str) -> str:
    path = LABEL_DIR / f"{slug(drug)}.json"
    if not path.is_file():
        return ""
    doc = json.loads(path.read_text())
    parts = []
    for key in ("dosage_and_administration", "dosage_and_administration_table"):
        val = doc.get(key)
        if isinstance(val, list):
            parts.extend(str(x) for x in val)
        elif val:
            parts.append(str(val))
    return "\n".join(parts)


def sample_bases() -> list[dict]:
    rows = []
    for rel in ("data/v3/instances_main.jsonl", "data/main_ext/bases_main_ext.jsonl"):
        p = ROOT / rel
        if not p.is_file():
            continue
        for r in read_jsonl(p):
            claim = r.get("claim_c0") or r.get("claim") or ""
            if r.get("valid", True) and DOSE_RE.search(claim):
                rows.append(r)
    rng = random.Random(SEED)
    rng.shuffle(rows)
    return rows[:N_QUESTIONS]


def build_corpus(base: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    evid = base.get("evidence_c0") or base.get("evidence") or ""
    if evid.strip():
        out.append(("textbook", evid.strip()))
    drug = base.get("drug") or ""
    fda = fda_dosage_text(drug)
    if fda.strip():
        out.append(("openfda", fda.strip()))
    if not out and evid:
        out.append(("textbook", evid[:2000]))
    return out


def retrieve(query: str, corpus: list[tuple[str, str]], *, top_k: int = 1) -> tuple[str, str]:
    if not corpus:
        return "", ""
    docs = [tokenize(t) for _, t in corpus]
    idx = bm25_index(docs)
    avgdl = sum(len(d) for d in docs) / max(len(docs), 1)
    q = tokenize(query)
    scored = [
        (bm25_score(q, docs[i], idx["idf"], avgdl), corpus[i][0], corpus[i][1])
        for i in range(len(corpus))
    ]
    scored.sort(key=lambda x: -x[0])
    _, source, text = scored[0]
    passage = text[:1200]
    return source, passage


def generate_answer(question: str, passage: str) -> str:
    assert_under_cap()
    prompt = (
        "Answer the medical dosing question in 1–3 sentences using ONLY the passage. "
        "Include the numeric dose and unit exactly as stated in the passage when present.\n\n"
        f"Passage:\n{passage}\n\nQuestion: {question}\n\nAnswer:"
    )
    resp = chat(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=256,
        seed=SEED,
    )
    assert_under_cap()
    return (resp.text or "").strip()


def main() -> None:
    os.environ.setdefault("MEDVERIF_USE_OPENROUTER", "1")
    bases = sample_bases()
    filled = 0
    rows_out: list[list] = []
    header = [
        "question_id",
        "base_id",
        "drug",
        "question",
        "generated_answer",
        "evidence_passage",
        "evidence_source",
        "answer_dose_span",
        "evidence_dose_span",
        "m1_answer_canon",
        "m1_evidence_canon",
        "surface_diff",
        "minicheck_roberta",
        "minicheck_ft5",
        "alignscore_l",
        "hhem",
        "bespoke",
        "llm_judge_1",
        "llm_judge_2",
        "same_quantity_same_context",
        "note",
    ]

    for i, b in enumerate(bases):
        drug = b.get("drug") or ""
        claim = b.get("claim_c0") or b.get("claim") or ""
        question = f"What dose of {drug} is described in the clinical evidence?" if drug else claim[:200]
        corpus = build_corpus(b)
        source, passage = retrieve(question + " " + claim, corpus)
        answer = ""
        note = ""
        if passage and os.environ.get("MEDVERIF_USE_OPENROUTER") == "1":
            try:
                answer = generate_answer(question, passage)
                filled += 1
            except (RuntimeError, AttributeError) as exc:
                note = str(exc)
                if isinstance(exc, RuntimeError) and "cap" in str(exc).lower():
                    break
        else:
            note = "no corpus or OR disabled"
        ans_span, ans_canon = first_dose_span(answer)
        ev_span, ev_canon = first_dose_span(passage)
        surface_diff = "Y" if ans_span and ev_span and ans_span != ev_span else ("N" if ans_span and ev_span else "")
        rows_out.append(
            [
                f"T24_{i:03d}",
                b.get("base_id") or b.get("id"),
                drug,
                question,
                answer,
                passage,
                source,
                ans_span,
                ev_span,
                ans_canon,
                ev_canon,
                surface_diff,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                note,
            ]
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(header)
        w.writerows(rows_out)

    manifest = {
        "n": len(bases),
        "filled_rows": filled,
        "cap_usd": CAP_USD,
        "model": DEFAULT_MODEL,
        "status": "bm25+or" if filled else "partial",
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT_CSV), "rows": len(bases), "filled": filled, "cap_usd": CAP_USD}, indent=2))


if __name__ == "__main__":
    main()
