#!/usr/bin/env python3
"""(C2) Second fine-tune with the SAME recipe as scripts/t15_train.py (MiniCheck-RoBERTa ft):
3 epochs, AdamW lr 2e-5, linear decay, no warmup, weight decay 0, batch 8, max_length 512, seed 42,
best epoch by dev loss, threshold 0.5 at inference.  Models:

  alignscore_large : AlignScore-large (yzha/AlignScore@8509e78, RoBERTa-large + heads).  Trained on the
                     3-way head used by the paper's inference mode (nli_sp score = P(class 0)) with a
                     binary log-loss on that probability.  Input = tokenizer(evidence, claim,
                     truncation='only_first') exactly as AlignScore's batch_tokenize.  No Lightning
                     needed; the best weights are written back into a copy of the original .ckpt so the
                     AlignScore library loads it unchanged.
  minicheck_ft5    : MiniCheck-Flan-T5-Large (lytang/MiniCheck-Flan-T5-Large@96eafd0).  Input =
                     'predict: ' + evidence + '</s>' + claim; loss = CE over the first decoder step's
                     logits at token ids [3, 209] (MiniCheck's own inference rule), label 1 = supported.

Resumable at epoch granularity (results in .cache/checkpoints/jr_<model>_r<ratio>/).
Usage: jr_ft_train.py --model alignscore_large --ratio 1      (or --array-index 0..5)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import FT_DIR, ROOT, is_done, log, mark_done, read_jsonl  # noqa: E402

GRID = [("alignscore_large", "0.5"), ("alignscore_large", "1"), ("alignscore_large", "2"),
        ("minicheck_ft5", "0.5"), ("minicheck_ft5", "1"), ("minicheck_ft5", "2")]
AS_REPO, AS_REV, AS_FILE = "yzha/AlignScore", "8509e78d25bb914939fc585c626500c9b2944249", "AlignScore-large.ckpt"
FT5_REPO, FT5_REV = "lytang/MiniCheck-Flan-T5-Large", "96eafd01cee2d16cf81aaa2fb226b14f422a37b3"
SEED = 42


def ckpt_dir(model: str, ratio: str) -> Path:
    return ROOT / ".cache/checkpoints" / ("jr_%s_r%s" % (model, ratio))


def alignscore_ckpt() -> str:
    from huggingface_hub import hf_hub_download

    return hf_hub_download(AS_REPO, AS_FILE, revision=AS_REV, cache_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"))


def build_alignscore(torch, nn):
    from transformers import AutoTokenizer, RobertaModel

    class AlignTri(nn.Module):
        def __init__(self):
            super().__init__()
            self.base_model = RobertaModel.from_pretrained("roberta-large")
            h = self.base_model.config.hidden_size
            self.bin_layer = nn.Linear(h, 2)
            self.tri_layer = nn.Linear(h, 3)
            self.reg_layer = nn.Linear(h, 1)
            self.dropout = nn.Dropout(p=0.1)

        def forward(self, input_ids, attention_mask):
            out = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
            return self.tri_layer(self.dropout(out.pooler_output))

    path = alignscore_ckpt()
    ck = torch.load(path, map_location="cpu", weights_only=False)
    m = AlignTri()
    sd = {k: v for k, v in ck["state_dict"].items() if k.startswith(("base_model.", "tri_layer.", "bin_layer.", "reg_layer."))}
    missing, unexpected = m.load_state_dict(sd, strict=False)
    missing = [k for k in missing if "position_ids" not in k]
    if missing:
        raise SystemExit("AlignScore ckpt missing keys: %s" % missing[:10])
    tok = AutoTokenizer.from_pretrained("roberta-large")

    def encode(ev, cl, max_len):
        return tok(ev, cl, truncation="only_first", max_length=max_len, padding=True, return_tensors="pt")

    def loss_fn(model, batch, y):
        logits = model(batch["input_ids"], batch["attention_mask"]).float()
        lse = torch.logsumexp(logits, dim=-1)
        logp0 = logits[:, 0] - lse
        log1m = torch.logsumexp(logits[:, 1:], dim=-1) - lse
        return -(y * logp0 + (1 - y) * log1m).mean()

    def save(model, out: Path):
        ck2 = {k: v for k, v in ck.items() if k not in ("optimizer_states", "lr_schedulers", "callbacks", "loops")}
        new_sd = dict(ck["state_dict"])
        for k, v in model.state_dict().items():
            if k in new_sd:
                new_sd[k] = v.detach().cpu().to(new_sd[k].dtype)
        ck2["state_dict"] = new_sd
        out.mkdir(parents=True, exist_ok=True)
        torch.save(ck2, out / "best.ckpt")

    return m, encode, loss_fn, save, {"base": "%s@%s/%s" % (AS_REPO, AS_REV[:7], AS_FILE), "half": "fp16"}


def build_ft5(torch, nn):
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    cache = os.environ.get("HUGGINGFACE_HUB_CACHE")
    tok = AutoTokenizer.from_pretrained(FT5_REPO, revision=FT5_REV, cache_dir=cache)
    m = AutoModelForSeq2SeqLM.from_pretrained(FT5_REPO, revision=FT5_REV, cache_dir=cache)
    ids = torch.tensor([3, 209])

    def encode(ev, cl, max_len):
        texts = ["predict: " + tok.eos_token.join([e, c]) for e, c in zip(ev, cl)]
        return tok(texts, truncation=True, max_length=max_len, padding=True, return_tensors="pt")

    def loss_fn(model, batch, y):
        dec = torch.zeros((batch["input_ids"].size(0), 1), dtype=torch.long, device=batch["input_ids"].device)
        logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], decoder_input_ids=dec).logits
        lab_logits = logits[:, 0, ids.to(logits.device)].float()
        return nn.functional.cross_entropy(lab_logits, y.long())

    def save(model, out: Path):
        out.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(out / "best"))
        tok.save_pretrained(str(out / "best"))

    return m, encode, loss_fn, save, {"base": "%s@%s" % (FT5_REPO, FT5_REV[:7]), "half": "bf16"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["alignscore_large", "minicheck_ft5"])
    ap.add_argument("--ratio", choices=["0.5", "1", "2"])
    ap.add_argument("--array-index", type=int)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--limit", type=int, default=0, help="debug: use only N train / N dev rows")
    args = ap.parse_args()
    if args.array_index is not None:
        args.model, args.ratio = GRID[args.array_index]
    if not args.model or not args.ratio:
        raise SystemExit("need --model and --ratio (or --array-index)")
    stage = "C2_train_%s_r%s" % (args.model, args.ratio)
    if is_done(stage):
        log(stage, skipped="marker present")
        return
    man_p = FT_DIR / "data_manifest.json"
    if man_p.is_file():
        info = json.loads(man_p.read_text())["ratios"].get(args.ratio, {})
        if args.ratio == "2" and info.get("effective_ratio", 2) < 1.5:
            mark_done(stage, skipped="ANLI pool capped (effective ratio %s); ratio-2 run would duplicate ratio 1"
                      % info.get("effective_ratio"))
            log(stage, skipped="capped ANLI")
            return
    import numpy as np
    import torch
    import torch.nn as nn
    from transformers import get_linear_schedule_with_warmup

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    dev_ = "cuda" if torch.cuda.is_available() else "cpu"
    data_dir = ROOT / ".cache/journal/ft" / ("ratio_" + args.ratio)
    train = read_jsonl(data_dir / "train.jsonl")
    dev = read_jsonl(data_dir / "dev.jsonl")
    if args.limit:
        train, dev = train[: args.limit], dev[: args.limit]
    if not train:
        raise SystemExit("missing %s (run jr_ft_data.py)" % (data_dir / "train.jsonl"))
    model, encode, loss_fn, save, meta = (build_alignscore if args.model == "alignscore_large" else build_ft5)(torch, nn)
    model.to(dev_)
    use_amp = dev_ == "cuda"
    amp_dtype = torch.bfloat16 if (meta["half"] == "bf16" and use_amp and torch.cuda.is_bf16_supported()) else torch.float16
    if meta["half"] == "bf16" and use_amp and not torch.cuda.is_bf16_supported():
        use_amp = False  # T5 is unstable in fp16; fall back to fp32
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp and amp_dtype == torch.float16)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0)
    steps_per_epoch = math.ceil(len(train) / args.batch_size)
    sched = get_linear_schedule_with_warmup(opt, 0, steps_per_epoch * args.epochs)
    out = ckpt_dir(args.model, args.ratio)
    out.mkdir(parents=True, exist_ok=True)
    state_p = out / "last_state.pt"
    hist_p = out / "history.json"
    start_epoch, best, history = 0, float("inf"), []
    if state_p.is_file():
        st = torch.load(state_p, map_location="cpu", weights_only=False)
        model.load_state_dict(st["model"])
        opt.load_state_dict(st["opt"])
        sched.load_state_dict(st["sched"])
        start_epoch, best, history = st["epoch"], st["best"], st["history"]
        log(stage, resumed_from_epoch=start_epoch)

    def batches(rows, shuffle, seed):
        idx = list(range(len(rows)))
        if shuffle:
            random.Random(seed).shuffle(idx)
        for off in range(0, len(idx), args.batch_size):
            sel = [rows[i] for i in idx[off: off + args.batch_size]]
            enc = encode([r["evidence"] for r in sel], [r["claim"] for r in sel], args.max_length)
            y = torch.tensor([1.0 if r["label"] == "SUPPORTED" else 0.0 for r in sel])
            yield {k: v.to(dev_) for k, v in enc.items()}, y.to(dev_)

    log(stage, model=args.model, ratio=args.ratio, n_train=len(train), n_dev=len(dev), device=dev_, amp=str(amp_dtype) if use_amp else "fp32", **meta)
    for ep in range(start_epoch, args.epochs):
        model.train()
        t0, tot, n = time.time(), 0.0, 0
        for step, (b, y) in enumerate(batches(train, True, SEED + ep)):
            with torch.autocast(device_type="cuda", dtype=amp_dtype, enabled=use_amp):
                loss = loss_fn(model, b, y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
            tot += float(loss) * len(y)
            n += len(y)
            if step % 200 == 0:
                log(stage, epoch=ep + 1, step=step, of=steps_per_epoch, train_loss=round(tot / max(n, 1), 5))
        model.eval()
        dl, dn, correct = 0.0, 0, 0
        with torch.no_grad():
            for b, y in batches(dev, False, 0):
                with torch.autocast(device_type="cuda", dtype=amp_dtype, enabled=use_amp):
                    dl += float(loss_fn(model, b, y)) * len(y)
                dn += len(y)
        dev_loss = dl / max(dn, 1)
        rec = {"epoch": ep + 1, "train_loss": tot / max(n, 1), "dev_loss": dev_loss, "secs": round(time.time() - t0)}
        history.append(rec)
        log(stage, **rec)
        if dev_loss < best:
            best = dev_loss
            save(model, out)
            log(stage, saved_best_epoch=ep + 1)
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(), "epoch": ep + 1,
                    "best": best, "history": history}, state_p)
        hist_p.write_text(json.dumps(history, indent=2) + "\n")
    cfg = {"model": args.model, "ratio": args.ratio, "base_checkpoint": meta["base"], "best_dev_loss": best,
           "best_dir": str(out), "history": history,
           "hyperparameters": {"seed": SEED, "epochs": args.epochs, "lr": args.lr, "batch_size": args.batch_size,
                               "max_length": args.max_length, "optimizer": "AdamW wd=0, linear decay, no warmup",
                               "threshold": 0.5, "amp": str(amp_dtype) if use_amp else "fp32"},
           "n_train": len(train), "n_dev": len(dev)}
    FT_DIR.mkdir(parents=True, exist_ok=True)
    (FT_DIR / ("train_%s_r%s.json" % (args.model, args.ratio))).write_text(json.dumps(cfg, indent=2) + "\n")
    if state_p.is_file() and not args.limit:
        state_p.unlink()  # optimizer state is large; best weights are kept
    if not args.limit:
        mark_done(stage, best_dev_loss=best)


if __name__ == "__main__":
    main()
