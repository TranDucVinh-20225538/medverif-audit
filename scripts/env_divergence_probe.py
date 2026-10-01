#!/usr/bin/env python3
"""Stage-by-stage MiniCheck-RoBERTa probe (sentences, chunks, token ids, dtype, per-chunk prob) for env comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PACK = ROOT / "data/t18/instances_t18_t15ood.jsonl"
DISAGREE = (
    "T180012__E1-unit__unit_swap",
    "T180015__E1-unit__unit_swap",
    "T180016__E1-unit__unit_swap",
    "T180019__E1-unit__unit_swap",
    "T180050__E1-unit__unit_swap",
    "T180051__E1-unit__unit_swap",
    "T180070__C0__none",
    "T180080__E1-unit__unit_swap",
)
AGREE = ("T180001__E1-unit__unit_swap", "T180004__E1-unit__unit_swap", "T180001__C0__none", "T180004__C0__none")


def non_ascii(text: str) -> list[str]:
    return sorted({f"U+{ord(c):04X} {unicodedata.name(c, '?')}" for c in text if ord(c) > 127})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    import minicheck
    import nltk
    import tokenizers
    import torch
    import transformers
    from minicheck.inference import sent_tokenize_with_newlines
    from verifiers import t6a_minicheck as mc

    rows = {json.loads(line)["instance_id"]: json.loads(line) for line in PACK.open() if line.strip()}
    model, _ = mc.load("t6a_minicheck_roberta")
    inf = model.model
    inf.chunk_size = 400
    tok = inf.tokenizer
    out = {
        "env": args.env,
        "versions": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "tokenizers": tokenizers.__version__,
            "nltk": nltk.__version__,
            "minicheck_path": minicheck.__file__,
        },
        "model_dtype": str(next(inf.model.parameters()).dtype),
        "model_device": str(next(inf.model.parameters()).device),
        "torch_threads": torch.get_num_threads(),
        "tokenizer_class": type(tok).__name__,
        "tokenizer_model_max_length": tok.model_max_length,
        "max_model_len": inf.max_model_len,
        "eos_token": tok.eos_token,
        "rows": {},
    }
    for iid in DISAGREE + AGREE:
        r = rows.get(iid)
        if not r:
            continue
        doc, claim = r["evidence"], r["claim"]
        sents = sent_tokenize_with_newlines(doc)
        res = inf.inference_per_example(doc, claim)
        text = tok.eos_token.join([doc, claim])
        ids = tok([text], max_length=inf.max_model_len, truncation=True, padding=True)["input_ids"][0]
        with torch.no_grad():
            enc = tok([text], max_length=inf.max_model_len, truncation=True, padding=True, return_tensors="pt")
            logits = inf.model(**enc).logits[0].tolist()
        out["rows"][iid] = {
            "group": "disagree" if iid in DISAGREE else "agree",
            "non_ascii_claim": non_ascii(claim),
            "non_ascii_evidence": non_ascii(doc),
            "n_sentences": len(sents),
            "sentences_sha1": hashlib.sha1(json.dumps(sents).encode()).hexdigest(),
            "chunks": list(res["used_chunks"]),
            "support_prob_per_chunk": [float(x) for x in res["support_prob_per_chunk"]],
            "max_support_prob": float(res["max_support_prob"]),
            "n_input_ids": len(ids),
            "input_ids": ids,
            "logits_single": logits,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"wrote": str(args.out), "rows": len(out["rows"]), "dtype": out["model_dtype"]}))


if __name__ == "__main__":
    main()
