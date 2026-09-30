#!/usr/bin/env python3
"""T16: Integrated Gradients + substitution test (MiniCheck-RoBERTa-L base ± T15 ckpt)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import read_jsonl  # noqa: E402
from verifiers.preprocess import verifier_inputs  # noqa: E402

NUM_RE = re.compile(r"\d+(?:\.\d+)?")
UNIT_RE = re.compile(
    r"\b(mg|g|mcg|µg|μg|ml|mL|units?|iu|meq|mmol|mol|kg|lb|oz)\b",
    re.I,
)


def resolve_device() -> torch.device:
    forced = (os.environ.get("MEDVERIF_T16_DEVICE") or "").strip().lower()
    if forced in ("cpu", "cuda", "cuda:0"):
        dev = torch.device(forced)
        if dev.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(f"MEDVERIF_T16_DEVICE={forced} but torch.cuda.is_available() is False")
        return dev
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_minicheck_roberta(ckpt: Path | None):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if ckpt is not None:
        model_id = str(ckpt)
    elif (ROOT / "notes/t15_config.json").is_file():
        model_id = json.loads((ROOT / "notes/t15_config.json").read_text())["base_checkpoint"]
    else:
        model_id = "lytang/MiniCheck-RoBERTa-Large"
    cache = str(ROOT / ".cache/huggingface")
    tok = AutoTokenizer.from_pretrained(model_id, cache_dir=cache)
    device = resolve_device()
    # Full-precision for IG backward (fp16 often unstable here).
    dtype = torch.float32
    model = AutoModelForSequenceClassification.from_pretrained(
        model_id, cache_dir=cache, torch_dtype=dtype
    )
    model.to(device).eval()
    print(
        json.dumps(
            {"t16": "load", "model_id": model_id, "device": str(device), "dtype": str(dtype)}
        ),
        flush=True,
    )
    return model, tok, device


def encode_pair(tok, claim: str, evidence: str, device):
    eos = tok.eos_token or "</s>"
    text = eos.join([evidence, claim])
    enc = tok(text, return_tensors="pt", truncation=True, max_length=512)
    return {k: v.to(device) for k, v in enc.items()}, text


def supported_logit(model, enc) -> torch.Tensor:
    out = model(**enc)
    # label 1 = supported (MiniCheck convention)
    return out.logits[0, 1]


def token_shares(tok, text: str, attributions: np.ndarray) -> dict[str, float]:
    ids = tok(text, return_offsets_mapping=True, truncation=True, max_length=512)
    offsets = ids["offset_mapping"]
    abs_attr = np.abs(attributions[: len(offsets)])
    total = float(abs_attr.sum()) or 1.0
    shares = {"numeral": 0.0, "unit": 0.0, "rest": 0.0}
    for (start, end), a in zip(offsets, abs_attr):
        if start == end == 0:
            continue
        piece = text[start:end]
        if NUM_RE.fullmatch(piece.strip()) or NUM_RE.search(piece):
            shares["numeral"] += float(a)
        elif UNIT_RE.search(piece):
            shares["unit"] += float(a)
        else:
            shares["rest"] += float(a)
    for k in shares:
        shares[k] /= total
    return shares


def ig_claim(model, tok, device, claim: str, evidence: str, steps: int = 16) -> dict[str, float]:
    enc, text = encode_pair(tok, claim, evidence, device)
    attn = enc["attention_mask"]
    emb_layer = model.get_input_embeddings()
    full = emb_layer(enc["input_ids"]).detach()
    baseline = torch.zeros_like(full)
    integrated = torch.zeros_like(full)
    for step in range(1, steps + 1):
        alpha = step / steps
        scaled = (baseline + alpha * (full - baseline)).detach().requires_grad_(True)
        out = model(inputs_embeds=scaled, attention_mask=attn)
        logit = out.logits[:, 1].sum()
        logit.backward()
        integrated += scaled.grad.detach()
        model.zero_grad(set_to_none=True)
    attr_np = (integrated / steps * (full - baseline))[0].cpu().numpy().sum(axis=1)
    return token_shares(tok, text, attr_np)


def subst_tests(model, tok, device, claim: str, evidence: str) -> tuple[float, float]:
    enc0, _ = encode_pair(tok, claim, evidence, device)
    with torch.no_grad():
        base_score = float(torch.sigmoid(supported_logit(model, enc0)).cpu())

    unit_claim = UNIT_RE.sub(lambda m: "g" if m.group(1).lower() == "mg" else "mg", claim, count=1)
    num_claim = NUM_RE.sub(lambda m: str(float(m.group()) * 2), claim, count=1)
    if unit_claim == claim:
        unit_claim = claim + " mg"
    if num_claim == claim:
        num_claim = claim.replace("1", "2", 1)

    def score(c):
        enc, _ = encode_pair(tok, c, evidence, device)
        with torch.no_grad():
            return float(torch.sigmoid(supported_logit(model, enc)).cpu())

    return base_score - score(unit_claim), base_score - score(num_claim)


def run_model(
    tag: str,
    ckpt: Path | None,
    rows: list[dict],
    limit: int,
    *,
    steps: int,
    handle,
) -> dict:
    model, tok, device = load_minicheck_roberta(ckpt)
    todo = rows[:limit] if limit else rows
    by_cond: dict[str, list[dict]] = defaultdict(list)
    for idx, row in enumerate(todo, start=1):
        claim, evidence = verifier_inputs(row)
        shares = ig_claim(model, tok, device, claim, evidence, steps=steps)
        du, dn = subst_tests(model, tok, device, claim, evidence)
        rec = {
            "instance_id": row["instance_id"],
            "condition": row.get("condition"),
            "attribution": shares,
            "subst_unit_delta": du,
            "subst_numeral_delta": dn,
        }
        by_cond[row.get("condition", "?")].append(rec)
        handle.write(json.dumps({"model": tag, **rec}, ensure_ascii=False) + "\n")
        handle.flush()
        if idx == 1 or idx % 5 == 0 or idx == len(todo):
            print(
                json.dumps({"t16": "progress", "model": tag, "done": idx, "total": len(todo)}),
                flush=True,
            )
    return {"model": tag, "by_condition": by_cond}


def plot(summary: dict, out_png: Path) -> None:
    if plt is None:
        return
    conditions = sorted({c for m in summary["models"] for c in m["means"]})
    x = np.arange(len(conditions))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, m in enumerate(summary["models"]):
        vals = [m["means"][c]["numeral"] for c in conditions]
        ax.bar(x + (i - 0.5) * width, vals, width, label=m["tag"])
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylabel("Share |attribution| on numerals")
    ax.legend()
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, default=ROOT / "data/t16/instances_t16.jsonl")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--report", type=Path, default=ROOT / "notes/t16_report.md")
    parser.add_argument("--fig", type=Path, default=ROOT / "results/figures/t16_attribution.png")
    parser.add_argument("--ig-steps", type=int, default=int(os.environ.get("MEDVERIF_T16_IG_STEPS", "16")))
    args = parser.parse_args()
    rows = read_jsonl(args.instances)
    raw_out = ROOT / "results/raw/t16/attribution.jsonl"
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "t16": "start",
                "instances": len(rows),
                "limit": args.limit,
                "ig_steps": args.ig_steps,
                "device_policy": os.environ.get("MEDVERIF_T16_DEVICE", "auto"),
            }
        ),
        flush=True,
    )

    models = [
        ("base", None),
        ("t15_ft", Path(json.loads((ROOT / "notes/t15_config.json").read_text())["best_checkpoint_dir"])),
    ]
    all_runs = []
    summary = {"models": []}
    with raw_out.open("w") as handle:
        for tag, ckpt in models:
            if ckpt and not ckpt.is_dir():
                print(json.dumps({"t16": "skip_model", "tag": tag, "reason": "missing_ckpt"}), flush=True)
                continue
            run = run_model(tag, ckpt, rows, args.limit, steps=args.ig_steps, handle=handle)
            all_runs.append(run)
            means: dict[str, dict[str, float]] = {}
            for cond, recs in run["by_condition"].items():
                if not recs:
                    continue
                means[cond] = {
                    k: float(np.mean([r["attribution"][k] for r in recs]))
                    for k in ("numeral", "unit", "rest")
                }
                means[cond]["subst_unit_delta"] = float(np.mean([r["subst_unit_delta"] for r in recs]))
                means[cond]["subst_numeral_delta"] = float(np.mean([r["subst_numeral_delta"] for r in recs]))
            summary["models"].append({"tag": tag, "means": means})

    plot(summary, args.fig)
    lines = ["# T16 attribution (MiniCheck-RoBERTa-L)", ""]
    for m in summary["models"]:
        lines.append(f"## {m['tag']}")
        for cond, stats in sorted(m["means"].items()):
            lines.append(
                f"- **{cond}:** numeral={stats['numeral']:.3f}, unit={stats['unit']:.3f}, "
                f"rest={stats['rest']:.3f}; Δscore unit-subst={stats['subst_unit_delta']:.3f}, "
                f"numeral×2={stats['subst_numeral_delta']:.3f}"
            )
        lines.append("")
    args.report.write_text("\n".join(lines) + "\n")
    print(json.dumps({"report": str(args.report), "fig": str(args.fig), "n": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
