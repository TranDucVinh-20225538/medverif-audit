#!/usr/bin/env python3
"""(B2) Retrieval for the real-RAG expansion: BM25 + dense (MedCPT; fallback bge) over the MedRAG
textbook chunks, fused with reciprocal-rank fusion (k=60). GPU recommended for the dense encoder
(corpus embeddings are cached under .cache/journal/dense/ and resumable).

Output: results/journal/rag/retrieval.jsonl (one row per question; top-k fused passages with
their BM25/dense ranks; gold-passage ranks as a retrieval diagnostic).
  --dense none  : BM25 only (box dry-run).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import RAG_DIR, ROOT, is_done, log, mark_done, read_jsonl, write_jsonl  # noqa: E402

STAGE = "B2_retrieve"
QUESTIONS = RAG_DIR / "questions.jsonl"
OUT = RAG_DIR / "retrieval.jsonl"
CACHE = ROOT / ".cache/journal/dense"
STOP = set("a an the of and or to in for on with by is are was were be been as at from that this which it its "
           "what how much many should does do dose doses dosage".split())
DENSE_MODELS = {
    "medcpt": ("ncbi/MedCPT-Query-Encoder", "ncbi/MedCPT-Article-Encoder"),
    "bge": ("BAAI/bge-base-en-v1.5", "BAAI/bge-base-en-v1.5"),
}


def tok(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in STOP]


class BM25:
    def __init__(self, docs: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.n = len(docs)
        self.dl = [len(d) for d in docs]
        self.avgdl = (sum(self.dl) / self.n) if self.n else 1.0
        self.post: Dict[str, List] = defaultdict(list)
        for i, d in enumerate(docs):
            for t, f in Counter(d).items():
                self.post[t].append((i, f))
        self.idf = {t: math.log(1 + (self.n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.post.items()}

    def top(self, query: List[str], k: int = 100):
        sc: Dict[int, float] = defaultdict(float)
        for t in set(query):
            if t not in self.post:
                continue
            idf = self.idf[t]
            for i, f in self.post[t]:
                sc[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
        return sorted(sc.items(), key=lambda x: -x[1])[:k]


def load_corpus(dirs: List[Path]):
    from extract_candidates import iter_chunks  # noqa: E402

    ids, titles, texts = [], [], []
    for d in dirs:
        for r in iter_chunks(d):
            ids.append(str(r.get("id") or "%s:%d" % (r["_file"], len(ids))))
            titles.append(str(r.get("title") or ""))
            texts.append(r.get("content") or r.get("contents") or "")
    return ids, titles, texts


def dense_embed(name: str, titles, texts, questions, batch: int, max_len: int):
    import numpy as np
    import torch
    from transformers import AutoModel, AutoTokenizer

    qname, aname = DENSE_MODELS[name]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    CACHE.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(("%s|%d|%s|%s" % (aname, len(texts), texts[0][:200] if texts else "", texts[-1][:200] if texts else "")).encode()).hexdigest()[:12]
    emb_path = CACHE / ("%s_%s.npy" % (name, h))
    prog_path = CACHE / ("%s_%s.progress" % (name, h))
    atok = AutoTokenizer.from_pretrained(aname)
    amod = AutoModel.from_pretrained(aname).to(dev).eval()
    if dev == "cuda":
        amod = amod.half()
    dim = amod.config.hidden_size
    if emb_path.is_file() and not prog_path.is_file():
        E = np.load(emb_path, mmap_mode="r")
    else:
        mode = "r+" if emb_path.is_file() else "w+"
        E = np.lib.format.open_memmap(emb_path, mode=mode, dtype="float16", shape=(len(texts), dim))
        start = int(prog_path.read_text()) if prog_path.is_file() else 0
        with torch.no_grad():
            for off in range(start, len(texts), batch):
                if name == "medcpt":
                    enc = atok([[t, x] for t, x in zip(titles[off:off + batch], texts[off:off + batch])], truncation=True,
                               padding=True, return_tensors="pt", max_length=max_len)
                else:
                    enc = atok(texts[off:off + batch], truncation=True, padding=True, return_tensors="pt", max_length=max_len)
                out = amod(**{k: v.to(dev) for k, v in enc.items()}).last_hidden_state[:, 0, :].float()
                if name == "bge":
                    out = torch.nn.functional.normalize(out, dim=-1)
                E[off:off + len(out)] = out.cpu().numpy().astype("float16")
                if (off // batch) % 200 == 0:
                    E.flush()
                    prog_path.write_text(str(off + len(out)))
                    log(STAGE, dense_progress=off + len(out), total=len(texts))
        E.flush()
        if prog_path.is_file():
            prog_path.unlink()
    qtok = AutoTokenizer.from_pretrained(qname)
    qmod = AutoModel.from_pretrained(qname).to(dev).eval()
    qs = questions if name == "medcpt" else ["Represent this sentence for searching relevant passages: " + q for q in questions]
    with torch.no_grad():
        enc = qtok(qs, truncation=True, padding=True, return_tensors="pt", max_length=64)
        Q = qmod(**{k: v.to(dev) for k, v in enc.items()}).last_hidden_state[:, 0, :].float()
        if name == "bge":
            Q = torch.nn.functional.normalize(Q, dim=-1)
    Q = Q.cpu().numpy().astype("float32")
    tops = []
    for qi in range(len(Q)):
        scores = np.zeros(len(texts), dtype="float32")
        for off in range(0, len(texts), 200000):
            scores[off:off + 200000] = np.asarray(E[off:off + 200000], dtype="float32") @ Q[qi]
        idx = np.argpartition(-scores, min(100, len(scores) - 1))[:100]
        idx = idx[np.argsort(-scores[idx])]
        tops.append([(int(i), float(scores[i])) for i in idx])
    return tops, aname


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-dir", action="append", default=[])
    ap.add_argument("--dense", default="medcpt", choices=["medcpt", "bge", "none"])
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--questions", default=str(QUESTIONS))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if is_done(STAGE) and not args.dry_run:
        log(STAGE, skipped="marker present")
        return
    from jr_rag_questions import default_corpus_dirs  # noqa: E402

    dirs = [Path(d) for d in args.corpus_dir] or default_corpus_dirs()
    qrows = [r for r in read_jsonl(Path(args.questions)) if r.get("valid", True)]
    if not qrows:
        raise SystemExit("no questions in %s" % args.questions)
    ids, titles, texts = load_corpus(dirs)
    log(STAGE, corpus_chunks=len(ids), questions=len(qrows))
    bm = BM25([tok(t + " " + x) for t, x in zip(titles, texts)])
    bm_tops = [bm.top(tok(q["question"]), 100) for q in qrows]
    dense_tops, dense_model = [[] for _ in qrows], None
    if args.dense != "none":
        try:
            dense_tops, dense_model = dense_embed(args.dense, titles, texts, [q["question"] for q in qrows], args.batch, args.max_len)
        except Exception as exc:
            log(STAGE, dense_error=str(exc)[:300], fallback="bge" if args.dense == "medcpt" else "none")
            if args.dense == "medcpt":
                dense_tops, dense_model = dense_embed("bge", titles, texts, [q["question"] for q in qrows], args.batch, args.max_len)
    id_index = {pid: i for i, pid in enumerate(ids)}
    out_rows, hits = [], Counter()
    for q, bt, dt in zip(qrows, bm_tops, dense_tops):
        br = {i: r for r, (i, _) in enumerate(bt, 1)}
        dr = {i: r for r, (i, _) in enumerate(dt, 1)}
        rrf = defaultdict(float)
        for ranks in (br, dr):
            for i, r in ranks.items():
                rrf[i] += 1.0 / (60 + r)
        fused = sorted(rrf.items(), key=lambda x: -x[1])[: args.topk]
        gold = id_index.get(str(q.get("source_passage_id")))
        fused_ids = [i for i, _ in fused]
        g = {"gold_rank_bm25": br.get(gold), "gold_rank_dense": dr.get(gold),
             "gold_in_topk_hybrid": gold in fused_ids if gold is not None else None}
        for k, v in (("bm25@%d" % args.topk, g["gold_rank_bm25"]), ("dense@%d" % args.topk, g["gold_rank_dense"])):
            hits[k] += int(v is not None and v <= args.topk)
        hits["hybrid@%d" % args.topk] += int(bool(g["gold_in_topk_hybrid"]))
        out_rows.append({"qid": q["qid"], "question": q["question"], "dense_model": dense_model,
                         "passages": [{"pid": ids[i], "title": titles[i], "text": texts[i], "bm25_rank": br.get(i),
                                       "dense_rank": dr.get(i), "rrf": round(s, 6)} for i, s in fused], **g})
    out = Path(args.out) if not args.dry_run else Path("/tmp/jr_retrieval_dryrun.jsonl")
    write_jsonl(out, out_rows)
    recall = {k: round(v / len(out_rows), 4) for k, v in hits.items()}
    log(STAGE, wrote=str(out), gold_recall=recall, dense_model=dense_model)
    if not args.dry_run:
        mark_done(STAGE, n=len(out_rows), gold_recall=recall, dense_model=dense_model, corpus_chunks=len(ids))


if __name__ == "__main__":
    main()
