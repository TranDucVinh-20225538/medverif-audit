#!/usr/bin/env python3
"""GPU batched AggreFact test scoring (base HF checkpoint + T15 ft)."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers.io_utils import append_jsonl, done_ids, read_jsonl  # noqa: E402
from verifiers.preprocess import verifier_inputs  # noqa: E402

THRESH = 0.97
CAL_N = 200


def row_id(row: dict) -> str:
    if row.get("instance_id"):
        return str(row["instance_id"])
    cid = row.get("contamination_identifier") or row.get("id")
    if cid:
        return str(cid)
    raise KeyError("missing instance id")


def normalize_rows(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        nr = dict(row)
        nr.setdefault("instance_id", row_id(row))
        if not (nr.get("evidence") or "").strip() and (nr.get("doc") or "").strip():
            nr["evidence"] = nr["doc"]
        out.append(nr)
    return out


def load_bundle(*, leg: str):
    cfg = json.loads((ROOT / "notes/t15_config.json").read_text())
    cache = os.environ.get("HF_HOME") or str(ROOT / ".cache/huggingface")
    if leg == "base":
        model_id = cfg["base_checkpoint"]
        verifier = "t15_aggrefact_base_gpu"
    else:
        model_id = str(cfg["best_checkpoint_dir"])
        verifier = "t15_aggrefact_ft_gpu"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("GPU required for t15_aggrefact_gpu_eval")
    use_bf16 = os.environ.get("MEDVERIF_T15_BF16", "1") not in ("0", "false", "False")
    dtype = torch.bfloat16 if use_bf16 and device.type == "cuda" else torch.float32
    tok = AutoTokenizer.from_pretrained(model_id, cache_dir=cache)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_id, cache_dir=cache, torch_dtype=dtype
    )
    model.to(device).eval()
    eos = tok.eos_token or "</s>"
    print(
        json.dumps(
            {
                "t15_gpu": "load",
                "leg": leg,
                "model_id": model_id,
                "device": str(device),
                "dtype": str(dtype),
                "batch": int(os.environ.get("MEDVERIF_T15_BATCH", "64")),
            }
        ),
        flush=True,
    )
    return model, tok, device, eos, verifier, dtype


def score_batch(
    model,
    tok,
    device,
    eos: str,
    verifier: str,
    rows: list[dict],
    *,
    dtype: torch.dtype,
) -> list[dict]:
    texts = []
    for row in rows:
        claim, evidence = verifier_inputs(row)
        texts.append(eos.join([evidence, claim]))
    enc = tok(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
    enc = {k: v.to(device) for k, v in enc.items()}
    t0 = time.perf_counter()
    with torch.no_grad():
        if dtype == torch.bfloat16:
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                logits = model(**enc).logits
        else:
            logits = model(**enc).logits
        probs = torch.softmax(logits.float(), dim=-1)[:, 1].cpu().tolist()
    per = (time.perf_counter() - t0) / max(len(rows), 1)
    out = []
    for row, prob in zip(rows, probs):
        out.append(
            {
                "instance_id": row["instance_id"],
                "raw_output": str(prob),
                "score": float(prob),
                "verdict": "PASS" if prob > 0.5 else "FAIL",
                "latency_s": per,
                "verifier": verifier,
                "precision": "bf16" if dtype == torch.bfloat16 else "fp32",
            }
        )
    return out


def compare_ref(ref_path: Path, scored: list[dict]) -> dict:
    ref = {json.loads(l)["instance_id"]: json.loads(l) for l in ref_path.open() if l.strip()}
    n = agree = 0
    diffs: list[float] = []
    for row in scored:
        iid = row["instance_id"]
        if iid not in ref:
            continue
        rv, nv = ref[iid].get("verdict"), row.get("verdict")
        if rv not in ("PASS", "FAIL") or nv not in ("PASS", "FAIL"):
            continue
        n += 1
        agree += int(rv == nv)
        rs, ns = ref[iid].get("score"), row.get("score")
        if rs is not None and ns is not None:
            diffs.append(abs(float(rs) - float(ns)))
    rate = agree / n if n else None
    return {
        "n": n,
        "verdict_agreement": rate,
        "mean_abs_score_diff": (sum(diffs) / len(diffs)) if diffs else None,
        "pass": rate is not None and rate >= THRESH and n >= 50,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", choices=("base", "ft"), required=True)
    parser.add_argument("--calibrate-only", action="store_true")
    parser.add_argument(
        "--ref",
        type=Path,
        default=ROOT / "results/raw/t15/base_aggrefact_test.jsonl",
        help="reference scores for calibration (base leg only)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="default results/raw/t15/{leg}_aggrefact_test.jsonl",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--instances",
        type=Path,
        default=ROOT / "data/t8/aggrefact/test.jsonl",
    )
    args = parser.parse_args()

    test_path = args.instances
    rows = normalize_rows(read_jsonl(test_path))
    out = args.out or (ROOT / f"results/raw/t15/{args.leg}_aggrefact_test.jsonl")

    if args.calibrate_only:
        if args.leg != "base":
            print(json.dumps({"error": "calibrate-only supported for base leg"}))
            return 2
        todo = rows[:CAL_N]
    else:
        done = done_ids(out)
        todo = [r for r in rows if r["instance_id"] not in done]
        if args.limit:
            todo = todo[: args.limit]

    if not todo:
        print(json.dumps({"t15_gpu": "complete", "leg": args.leg, "out": str(out)}))
        return 0

    model, tok, device, eos, verifier, dtype = load_bundle(leg=args.leg)
    batch = int(os.environ.get("MEDVERIF_T15_BATCH", "64"))
    scored_all: list[dict] = []
    for off in range(0, len(todo), batch):
        chunk = todo[off : off + batch]
        scored = score_batch(model, tok, device, eos, verifier, chunk, dtype=dtype)
        if not args.calibrate_only:
            append_jsonl(out, scored)
        scored_all.extend(scored)
        n_done = len(done_ids(out)) if out.is_file() and not args.calibrate_only else len(scored_all)
        print(
            json.dumps(
                {
                    "t15_gpu": "progress",
                    "leg": args.leg,
                    "done": n_done if not args.calibrate_only else len(scored_all),
                    "total": len(rows) if not args.calibrate_only else CAL_N,
                }
            ),
            flush=True,
        )

    if args.calibrate_only:
        stat = compare_ref(args.ref, scored_all)
        cal_path = ROOT / "notes/t15_aggrefact_gpu_calibration.json"
        cal_path.write_text(json.dumps({"leg": args.leg, **stat}, indent=2) + "\n")
        print(json.dumps(stat, indent=2))
        return 0 if stat.get("pass") else 1

    print(json.dumps({"t15_gpu": "done", "leg": args.leg, "out": str(out), "new_rows": len(scored_all)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
