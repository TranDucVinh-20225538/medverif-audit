#!/usr/bin/env python3
"""(J3-FT) Score the chain-1 C2 fine-tuned checkers (+ their bases through the same inference path) on
  rd   raw              real-dose answers (1451)                         -> part (1) FT-on-RD
  ho   raw/unf/unf_v2   held-out UNF set (S/U/anchor, 450 x 3 variants)  -> part (2) FT x UNF
  rdunf raw/unf/unf_v2  RD pairs changed by UNF v1 or v2 (705 x 3)       -> part (2) on RD
One model per Slurm array task (j3_models.FT order).  Inference = jr_ft_eval.load_scorer (vendored, unchanged):
AlignScore(roberta-large, nli_sp, PASS iff score > 0.5) with best.ckpt (FT) or the pinned AlignScore-large.ckpt (base);
MiniCheck('flan-t5-large', label = PASS) with the FT seq2seq weights swapped in (base = library default weights).
Identical (claim, evidence) texts are scored once per model (text-key cache, also across resumed runs).
Output: results/journal3/ft/scores/<name>__<pack>_<variant>.jsonl ; marker J3_FT_<name>.done.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from j3_common import FT_SCORES, MOCK, ROOT, append_jsonl, is_done, log, mark_done, pack_rows, read_jsonl, text_key  # noqa: E402
from j3_models import AS_FILE, AS_REPO, AS_REV, FT, FT_PACKS, ft_name  # noqa: E402


def ckpt_dir(model: str, tag: str):
    return None if tag == "base" else ROOT / ".cache/checkpoints" / ("jr_%s_r%s" % (model, tag[1:]))


def ckpt_path(model: str, tag: str):
    ck = ckpt_dir(model, tag)
    if ck is None:
        return None
    return ck / ("best.ckpt" if model == "alignscore_large" else "best")


def alignscore_base_ckpt() -> str:
    from huggingface_hub import hf_hub_download

    return hf_hub_download(AS_REPO, AS_FILE, revision=AS_REV, cache_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"))


def load_scorer(model: str, tag: str, batch: int):
    """Vendored from scripts/journal/jr_ft_eval.load_scorer (git 6d0b7d8)."""
    if MOCK:
        import re

        def score(ev, cl):
            s = [0.9 if all(n in e for n in re.findall(r"\d+(?:\.\d+)?", c)) else 0.1 for e, c in zip(ev, cl)]
            return s, ["PASS" if x > 0.5 else "FAIL" for x in s]

        return score, "mock"
    import torch

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    ck = ckpt_path(model, tag)
    if model == "alignscore_large":
        from alignscore.alignscore import AlignScore  # needs pytorch_lightning in this env

        path = str(ck) if ck else alignscore_base_ckpt()
        if not Path(path).is_file():
            raise SystemExit("missing checkpoint %s" % path)
        sc = AlignScore(model="roberta-large", batch_size=batch, device=dev, ckpt_path=path, evaluation_mode="nli_sp", verbose=False)

        def score(ev, cl):
            s = [float(x) for x in sc.score(contexts=ev, claims=cl)]
            return s, ["PASS" if x > 0.5 else "FAIL" for x in s]

        return score, path
    from minicheck.minicheck import MiniCheck

    mc = MiniCheck(model_name="flan-t5-large", batch_size=batch, cache_dir=os.environ.get("HF_HOME"))
    src = "lytang/MiniCheck-Flan-T5-Large (library default)"
    if ck:
        from transformers import AutoModelForSeq2SeqLM

        if not ck.is_dir():
            raise SystemExit("missing checkpoint %s" % ck)
        old = mc.model.model
        mc.model.model = AutoModelForSeq2SeqLM.from_pretrained(str(ck)).to(next(old.parameters()).device).eval()
        del old
        src = str(ck)

    def score(ev, cl):
        labels, probs, _, _ = mc.score(docs=ev, claims=cl)
        return [float(p) for p in probs], ["PASS" if int(l) == 1 else "FAIL" for l in labels]

    return score, src


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--array-index", type=int)
    ap.add_argument("--model", choices=["alignscore_large", "minicheck_ft5"])
    ap.add_argument("--tag", choices=["base", "r0.5", "r1", "r2"])
    ap.add_argument("--packs", default=",".join("%s_%s" % pv for pv in FT_PACKS))
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--chunk", type=int, default=64)
    ap.add_argument("--limit", type=int, default=int(os.environ.get("MEDVERIF_J3_LIMIT", "0") or 0), help="max rows per pack (smoke)")
    ap.add_argument("--out-dir", default=str(FT_SCORES))
    args = ap.parse_args()
    if args.array_index is not None:
        args.model, args.tag = FT[args.array_index]
    name = ft_name(args.model, args.tag)
    stage = "J3_FT_%s" % name
    if is_done(stage) and not args.limit:
        log(stage, skipped="marker present")
        return
    if args.tag == "r2":
        m = ROOT / "results/journal/markers" / ("C2_train_%s_r2.done" % args.model)
        if m.is_file() and "skipped" in m.read_text():
            mark_done(stage, skipped="chain-1 ratio-2 training was skipped")
            return
    out_dir = Path(args.out_dir)
    plan = []  # (pack, variant, out path, rows todo)
    cache = {}
    for pv in [p for p in args.packs.split(",") if p]:
        pack, variant = pv.split("_", 1)
        out = out_dir / ("%s__%s_%s.jsonl" % (name, pack, variant))
        prev = read_jsonl(out)
        for r in prev:
            if r.get("tk") and r.get("score") is not None:
                cache[r["tk"]] = (r["score"], r["verdict"])
        have = {r["instance_id"] for r in prev}
        rows = pack_rows(pack, variant)
        if args.limit:
            rows = rows[:args.limit]
        plan.append((pack, variant, out, [dict(r, tk=text_key(r["claim"], r["evidence"])) for r in rows if r["instance_id"] not in have]))
    uniq = {}
    for _, _, _, rows in plan:
        for r in rows:
            if r["tk"] not in cache:
                uniq.setdefault(r["tk"], r)
    log(stage, todo={"%s_%s" % (p, v): len(rows) for p, v, _, rows in plan}, unique_new_texts=len(uniq), cached=len(cache))
    src = "cache"
    if uniq:
        t0 = time.time()
        score, src = load_scorer(args.model, args.tag, args.batch)
        log(stage, weights=src, load_s=round(time.time() - t0, 1))
        todo = list(uniq.values())
        for off in range(0, len(todo), args.chunk):
            sel = todo[off:off + args.chunk]
            s, v = score([r["evidence"] for r in sel], [r["claim"] for r in sel])
            for r, a, b in zip(sel, s, v):
                cache[r["tk"]] = (a, b)
            if (off // args.chunk) % 10 == 0:
                log(stage, progress=off + len(sel), total=len(todo), secs=round(time.time() - t0))
    counts = {}
    for pack, variant, out, rows in plan:
        append_jsonl(out, [{"instance_id": r["instance_id"], "score": cache[r["tk"]][0], "verdict": cache[r["tk"]][1], "tk": r["tk"],
                            "verifier": name, "weights": src, "pack": pack, "variant": variant} for r in rows])
        counts["%s_%s" % (pack, variant)] = len(read_jsonl(out))
    if not args.limit:
        mark_done(stage, weights=src, rows=counts)
    log(stage, done=True, rows=counts)


if __name__ == "__main__":
    main()
