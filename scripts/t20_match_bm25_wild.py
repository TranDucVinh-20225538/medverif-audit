#!/usr/bin/env python3
"""T20 steps 3–4: M1 dose matching vs openFDA + BM25 retrieval + wild review CSV."""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from quantity_norm import canonicalize_dose_span  # noqa: E402
from text_utils import DOSE_RE  # noqa: E402
from t20_surface_diff import categorize_surface_diff, pair_key, pair_key_from_row  # noqa: E402

DRUG_LIST = ROOT / "data/t20/drug_list.jsonl"
LABEL_DIR = ROOT / "data/t20/labels"
BASES_MAIN = ROOT / "data/v3/instances_main.jsonl"
BASES_EXT = ROOT / "data/main_ext/bases_main_ext.jsonl"
OUT_JSON = ROOT / "notes/t20_match_retrieval.json"
OUT_MD = ROOT / "notes/t20_report.md"
QC_DIFF = ROOT / "qc/t20_diff_unit_review.csv"
PI_LABELS = ROOT / "qc/t20_diff_unit_labels.csv"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:80]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def dose_tokens(text: str) -> list[tuple[str, str]]:
    """(canonical, surface) for each dose mention."""
    out: list[tuple[str, str]] = []
    for m in DOSE_RE.finditer(text):
        surf = m.group(0).strip()
        try:
            canon = canonicalize_dose_span(m.group(1), m.group(2))
        except Exception:  # noqa: BLE001
            continue
        out.append((canon, surf))
    return out


def label_dosage_text(doc: dict) -> str:
    parts = []
    for key in ("dosage_and_administration", "dosage_and_administration_table"):
        val = doc.get(key)
        if isinstance(val, list):
            parts.extend(val)
        elif val:
            parts.append(str(val))
    return "\n".join(parts)


def load_bases_by_id() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in (BASES_EXT, BASES_MAIN):
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            bid = row.get("base_id") or row.get("id")
            if bid and row.get("type") == "DOSE":
                out[str(bid)] = row
    return out


def bm25_index(docs: list[list[str]]) -> dict:
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(doc))
    n = len(docs)
    idf = {t: math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) for t in df}
    return {"idf": idf, "docs": docs, "n": n}


def sentence_around(text: str, needle: str, *, max_len: int = 500) -> str:
    if not text or not needle:
        return (text or "")[:max_len]
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return text[:max_len]
    left = max(text.rfind(".", 0, idx), text.rfind("\n", 0, idx))
    right_dot = text.find(".", idx + len(needle))
    right_nl = text.find("\n", idx + len(needle))
    candidates = [p for p in (right_dot, right_nl) if p >= 0]
    right = min(candidates) + 1 if candidates else len(text)
    start = 0 if left < 0 else left + 1
    return text[start:right].strip()[:max_len]


def load_pi_annotations() -> tuple[dict[tuple, dict], int, int, int, int]:
    """First PI row per dedupe key; stats on unique pairs."""
    if not PI_LABELS.is_file():
        return {}, 0, 0, 0, 0
    by_key: dict[tuple, dict] = {}
    pi_rows = 0
    with PI_LABELS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            pi_rows += 1
            k = pair_key_from_row(row)
            if k not in by_key:
                by_key[k] = row
    pi_unique_y = pi_unique_n = scale_confirmed_y = 0
    for row in by_key.values():
        yn = (row.get("same_quantity_same_context") or "").strip().upper()
        if yn == "Y":
            pi_unique_y += 1
            if categorize_surface_diff(row["textbook_span"], row["label_span"]) == "scale_conversion":
                scale_confirmed_y += 1
        elif yn == "N":
            pi_unique_n += 1
    return by_key, pi_rows, pi_unique_y, pi_unique_n, scale_confirmed_y


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


def main() -> None:
    drugs = [json.loads(line) for line in DRUG_LIST.open() if line.strip()]
    bases = load_bases_by_id()
    match_rows: list[dict] = []
    seen_pairs: set[tuple] = set()
    drugs_with_label = 0

    for rec in drugs:
        drug = rec["drug"]
        path = LABEL_DIR / f"{slug(drug)}.json"
        if not path.is_file():
            continue
        doc = json.loads(path.read_text())
        drugs_with_label += 1
        label_text = label_dosage_text(doc)
        label_doses = dose_tokens(label_text)
        for bid in rec.get("bases") or []:
            base = bases.get(bid)
            if not base:
                continue
            claim = base.get("claim_c0") or base.get("claim") or ""
            for t_canon, t_surf in dose_tokens(claim):
                for l_canon, l_surf in label_doses:
                    if t_canon != l_canon:
                        continue
                    tb_sent = sentence_around(claim, t_surf)
                    lb_sent = sentence_around(label_text, l_surf)
                    key = pair_key(drug, tb_sent, lb_sent, t_surf, l_surf)
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)
                    surf_diff = t_surf.replace(" ", "").lower() != l_surf.replace(" ", "").lower()
                    cat = categorize_surface_diff(t_surf, l_surf) if surf_diff else "same_surface"
                    match_rows.append(
                        {
                            "drug": drug,
                            "base_id": bid,
                            "textbook_dose": t_surf,
                            "label_dose": l_surf,
                            "canonical": t_canon,
                            "unit_surface_differs": surf_diff,
                            "surface_diff_category": cat,
                            "textbook_sentence": tb_sent,
                            "label_sentence": lb_sent,
                            "claim_snip": claim[:200],
                        }
                    )

    matched_pairs = len(match_rows)
    diff_rows = [r for r in match_rows if r["unit_surface_differs"]]
    diff_cats = Counter(r["surface_diff_category"] for r in diff_rows)
    pi_by_key, pi_rows, pi_unique_y, pi_unique_n, scale_confirmed_y = load_pi_annotations()
    QC_DIFF.parent.mkdir(parents=True, exist_ok=True)
    with QC_DIFF.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "drug",
                "base_id",
                "textbook_sentence",
                "label_sentence",
                "textbook_span",
                "label_span",
                "surface_diff_category",
                "same_quantity_same_context",
                "note",
            ]
        )
        for r in diff_rows:
            pk = pair_key(
                r["drug"],
                r["textbook_sentence"],
                r["label_sentence"],
                r["textbook_dose"],
                r["label_dose"],
            )
            pi = pi_by_key.get(pk, {})
            w.writerow(
                [
                    r["drug"],
                    r["base_id"],
                    r["textbook_sentence"],
                    r["label_sentence"],
                    r["textbook_dose"],
                    r["label_dose"],
                    r["surface_diff_category"],
                    (pi.get("same_quantity_same_context") or "").strip(),
                    (pi.get("note") or "").strip()
                    or "M1 canonical match; PI in t20_diff_unit_labels.csv",
                ]
            )

    # BM25 retrieval simulation on dose bases
    corpus_chunks: list[str] = []
    chunk_meta: list[str] = []
    for doc_path in LABEL_DIR.glob("*.json"):
        doc = json.loads(doc_path.read_text())
        txt = label_dosage_text(doc)
        if txt.strip():
            corpus_chunks.append(txt[:4000])
            chunk_meta.append(doc_path.stem)
    for base in bases.values():
        corpus_chunks.append((base.get("evidence") or base.get("claim") or "")[:2000])
        chunk_meta.append(base.get("id") or base.get("base_id") or "base")

    tok_docs = [tokenize(c) for c in corpus_chunks]
    avgdl = sum(len(d) for d in tok_docs) / max(1, len(tok_docs))
    idx = bm25_index(tok_docs)
    queries_hit = 0
    queries_n = 0
    for rec in drugs:
        for bid in rec.get("bases") or []:
            base = bases.get(bid)
            if not base:
                continue
            claim = base.get("claim_c0") or base.get("claim") or ""
            if not DOSE_RE.search(claim):
                continue
            queries_n += 1
            q = tokenize(f"What is the dose of {rec['drug']} for treatment? {claim[:120]}")
            scores = [
                bm25_score(q, doc, idx["idf"], avgdl)
                for doc in tok_docs
            ]
            top5 = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
            tb_doses = {c for _, c in dose_tokens(claim)}
            hit = False
            for i in top5:
                for _, surf in dose_tokens(corpus_chunks[i]):
                    if surf.replace(" ", "").lower() not in {t.replace(" ", "").lower() for t in tb_doses}:
                        # same quantity different unit in retrieved chunk vs textbook
                        for t_canon, t_surf in dose_tokens(claim):
                            for l_canon, l_surf in dose_tokens(corpus_chunks[i]):
                                if t_canon == l_canon and t_surf.lower() != l_surf.lower():
                                    hit = True
                                    break
            if hit:
                queries_hit += 1

    summary = {
        "drugs_in_list": len(drugs),
        "drugs_with_cached_label": drugs_with_label,
        "unique_matched_pairs": matched_pairs,
        "unique_diff_pairs": len(diff_rows),
        "unique_diff_categories": dict(diff_cats),
        "matcher_rows_before_dedupe_note": "363 inflated (cross-product duplicates)",
        "bm25_queries": queries_n,
        "bm25_queries_unit_mismatch_in_top5_raw": queries_hit,
        "bm25_pct_withdrawn": True,
        "diff_unit_review_csv": str(QC_DIFF.relative_to(ROOT)),
        "pi_label_rows": pi_rows,
        "pi_unique_reviewed": pi_unique_y + pi_unique_n,
        "pi_same_context_y": pi_unique_y,
        "scale_conversion_confirmed_pi_y": scale_confirmed_y,
    }
    OUT_JSON.write_text(
        json.dumps({"summary": summary, "unique_diff_pairs": diff_rows, "sample_matches": match_rows[:20]}, indent=2)
        + "\n"
    )
    print(json.dumps(summary, indent=2))
    import subprocess

    subprocess.run([sys.executable, str(ROOT / "scripts/t20_write_report.py")], check=True)


if __name__ == "__main__":
    main()
