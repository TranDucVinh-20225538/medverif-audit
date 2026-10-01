#!/usr/bin/env python3
"""(C3) Score base + fine-tuned AlignScore-large / MiniCheck-Flan-T5 with the LIBRARY inference paths
(same as the paper's v3_alignscore / v2a_minicheck): AlignScore(nli_sp, PASS iff score > 0.5) and
MiniCheck('flan-t5-large', PASS iff prob > 0.5) with the fine-tuned weights swapped in.

Packs: main_dose (data/v3/instances_main.jsonl) + t7 (unit-swap card rows), aggrefact (LLM-AggreFact
test, stratified n=3000 seed 42 = scripts/t15_aggrefact_subsample_eval.py sample), t24b (existing
out-of-template real RAG), rag (new journal RAG pack, if built).
Output: results/journal/ft/scores/<model>_<tag>__<pack>.jsonl  (resumable by instance_id)
Usage: jr_ft_eval.py --model minicheck_ft5 --tag r1   (tags: base, r0.5, r1, r2)  or --array-index 0..7
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import FT_DIR, ROOT, append_jsonl, done_ids, is_done, log, mark_done, read_jsonl  # noqa: E402

GRID = [(m, t) for m in ("alignscore_large", "minicheck_ft5") for t in ("base", "r0.5", "r1", "r2")]
PACKS = {
    "main_dose": ROOT / "data/v3/instances_main.jsonl",
    "t7": ROOT / "data/t7/instances_e1_unit.jsonl",
    "aggrefact": ROOT / "data/t8/aggrefact/test.jsonl",
    "t24b": ROOT / "data/t24/instances_t24b.jsonl",
    "rag": ROOT / "data/journal/instances_rag.jsonl",
}


def rid(r: dict) -> str:
    return str(r.get("instance_id") or r.get("contamination_identifier") or r.get("id"))


def pack_rows(name: str):
    rows = read_jsonl(PACKS[name])
    if name == "aggrefact" and rows:
        from t15_aggrefact_subsample_eval import N_SAMPLE, SEED, stratified_sample  # noqa: E402

        rows = stratified_sample(rows, int(os.environ.get("MEDVERIF_JR_AGG_N", N_SAMPLE)), SEED)
    out = []
    for r in rows:
        if not r.get("valid", True):
            continue
        ev = (r.get("evidence") or r.get("doc") or "").strip()
        cl = (r.get("claim") or "").strip()
        if ev and cl:
            out.append({"instance_id": rid(r), "evidence": ev, "claim": cl})
    return out


def load_scorer(model: str, tag: str, batch: int):
    import torch

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    ratio = tag[1:] if tag != "base" else None
    ck = ROOT / ".cache/checkpoints" / ("jr_%s_r%s" % (model, ratio)) if ratio else None
    if model == "alignscore_large":
        from alignscore.alignscore import AlignScore  # needs pytorch_lightning in this env

        from jr_ft_train import alignscore_ckpt  # noqa: E402

        path = str(ck / "best.ckpt") if ck else alignscore_ckpt()
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

        best = ck / "best"
        if not best.is_dir():
            raise SystemExit("missing checkpoint %s" % best)
        old = mc.model.model
        mc.model.model = AutoModelForSeq2SeqLM.from_pretrained(str(best)).to(next(old.parameters()).device).eval()
        del old
        src = str(best)

    def score(ev, cl):
        labels, probs, _, _ = mc.score(docs=ev, claims=cl)
        return [float(p) for p in probs], ["PASS" if int(l) == 1 else "FAIL" for l in labels]

    return score, src


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["alignscore_large", "minicheck_ft5"])
    ap.add_argument("--tag", choices=["base", "r0.5", "r1", "r2"])
    ap.add_argument("--array-index", type=int)
    ap.add_argument("--packs", default="main_dose,t7,t24b,rag,aggrefact")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--chunk", type=int, default=64)
    args = ap.parse_args()
    if args.array_index is not None:
        args.model, args.tag = GRID[args.array_index]
    stage = "C3_eval_%s_%s" % (args.model, args.tag)
    if is_done(stage):
        log(stage, skipped="marker present")
        return
    if args.tag == "r2":
        m = FT_DIR.parent / "markers" / ("C2_train_%s_r2.done" % args.model)
        if m.is_file() and "skipped" in m.read_text():
            mark_done(stage, skipped="ratio-2 training skipped (capped ANLI)")
            return
    score, src = load_scorer(args.model, args.tag, args.batch)
    name = "%s_%s" % (args.model, args.tag)
    counts, missing = {}, []
    for pack in [p.strip() for p in args.packs.split(",") if p.strip()]:
        if not PACKS[pack].is_file():
            log(stage, pack=pack, skipped="missing %s" % PACKS[pack])
            missing.append(pack)
            continue
        rows = pack_rows(pack)
        out = FT_DIR / "scores" / ("%s__%s.jsonl" % (name, pack))
        todo = [r for r in rows if r["instance_id"] not in done_ids(out)]
        t0 = time.time()
        for off in range(0, len(todo), args.chunk):
            sel = todo[off: off + args.chunk]
            s, v = score([r["evidence"] for r in sel], [r["claim"] for r in sel])
            append_jsonl(out, [{"instance_id": r["instance_id"], "score": a, "verdict": b, "verifier": name, "weights": src}
                               for r, a, b in zip(sel, s, v)])
            if (off // args.chunk) % 10 == 0:
                log(stage, pack=pack, progress=off + len(sel), total=len(todo), secs=round(time.time() - t0))
        counts[pack] = len(done_ids(out))
    if missing:
        log(stage, not_marking_done="packs missing: %s (rerun later; scoring resumes by id)" % missing, rows=counts)
    else:
        mark_done(stage, weights=src, rows=counts)


if __name__ == "__main__":
    main()
