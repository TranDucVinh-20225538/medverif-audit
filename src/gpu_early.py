"""GPU scoring for V2a (+ V3 if AlignScore imports). One load per model; resume by instance_id."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import huggingface_hub.file_download as hf_file_download

hf_file_download.is_xet_available = lambda: False

from huggingface_hub import hf_hub_download, snapshot_download
from minicheck.minicheck import MiniCheck
from verifiers.io_utils import append_jsonl, done_ids, read_jsonl

ROOT = Path("/data2/hpcshared/medverif-audit")
EARLY = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
RAW = ROOT / "results" / "raw"
RAW_THR = ROOT / "results" / "raw_threshold"
STATUS = ROOT / "notes" / "gpu_early_status.json"
CACHE = os.environ.get("HF_HOME") or str(ROOT / ".cache" / "huggingface")
BATCH = 16


def split_rows() -> tuple[list[dict], list[dict]]:
    main, thr = [], []
    for row in read_jsonl(EARLY):
        if row.get("magnitude") == "paraphrase" or not row.get("valid", True):
            continue
        if row.get("subset") == "threshold":
            thr.append(row)
        elif row.get("subset") == "main":
            main.append(row)
    return main, thr


def fetch_ckpt() -> Path:
    cache = os.environ.get("HUGGINGFACE_HUB_CACHE")
    snapshot_download(
        "lytang/MiniCheck-Flan-T5-Large",
        revision="96eafd01cee2d16cf81aaa2fb226b14f422a37b3",
        cache_dir=cache,
    )
    snapshot_download(
        "FacebookAI/roberta-large",
        revision="722cf37b1afa9454edce342e7895e588b6ff1d59",
        cache_dir=cache,
        ignore_patterns=["pytorch_model.bin", "*.msgpack", "flax_model*", "tf_model*", "rust_model*"],
    )
    return Path(
        hf_hub_download(
            repo_id="yzha/AlignScore",
            filename="AlignScore-large.ckpt",
            revision="8509e78d25bb914939fc585c626500c9b2944249",
            cache_dir=cache,
        )
    )


def score_v2a(model, rows: list[dict], out_path: Path) -> int:
    done = done_ids(out_path)
    todo = [row for row in rows if row["instance_id"] not in done]
    if not todo:
        return 0
    n = 0
    for offset in range(0, len(todo), BATCH):
        chunk = todo[offset : offset + BATCH]
        docs = [row["evidence"] for row in chunk]
        claims = [row["claim"] for row in chunk]
        started = time.perf_counter()
        labels, probs, _, _ = model.score(docs, claims)
        per = (time.perf_counter() - started) / max(len(chunk), 1)
        scored = []
        for row, label, prob in zip(chunk, labels, probs):
            scored.append({
                "instance_id": row["instance_id"],
                "raw_output": str(prob),
                "score": float(prob),
                "verdict": "PASS" if int(label) == 1 else "FAIL",
                "latency_s": per,
                "verifier": "v2a_minicheck",
            })
        append_jsonl(out_path, scored)
        n += len(scored)
    return n


def score_v3(model, rows: list[dict], out_path: Path) -> int:
    done = done_ids(out_path)
    todo = [row for row in rows if row["instance_id"] not in done]
    if not todo:
        return 0
    n = 0
    for offset in range(0, len(todo), BATCH):
        chunk = todo[offset : offset + BATCH]
        docs = [row["evidence"] for row in chunk]
        claims = [row["claim"] for row in chunk]
        started = time.perf_counter()
        scores = model.score(docs, claims)
        per = (time.perf_counter() - started) / max(len(chunk), 1)
        scored = []
        for row, score in zip(chunk, scores):
            value = float(score)
            scored.append({
                "instance_id": row["instance_id"],
                "raw_output": str(value),
                "score": value,
                "verdict": "PASS" if value > 0.5 else "FAIL",
                "latency_s": per,
                "verifier": "v3_alignscore",
            })
        append_jsonl(out_path, scored)
        n += len(scored)
    return n


def try_load_v3(ckpt: Path):
    from alignscore.alignscore import AlignScore

    started = time.perf_counter()
    model = AlignScore(
        model="roberta-large",
        batch_size=BATCH,
        device="cuda",
        ckpt_path=str(ckpt),
        evaluation_mode="nli_sp",
        verbose=False,
    )
    return model, time.perf_counter() - started


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    RAW_THR.mkdir(parents=True, exist_ok=True)
    main_rows, thr_rows = split_rows()
    print(json.dumps({"main": len(main_rows), "threshold": len(thr_rows)}), flush=True)

    ckpt = fetch_ckpt()
    v2a_started = time.perf_counter()
    v2a = MiniCheck(model_name="flan-t5-large", batch_size=BATCH, cache_dir=CACHE)
    v2a_load_s = time.perf_counter() - v2a_started

    n_main = score_v2a(v2a, main_rows, RAW / "v2a_minicheck.jsonl")
    n_thr = score_v2a(v2a, thr_rows, RAW_THR / "v2a_minicheck.jsonl")
    del v2a

    status = {
        "v2a_load_s": v2a_load_s,
        "v2a_scored_main": n_main,
        "v2a_scored_threshold": n_thr,
        "v3_ran": False,
        "v3_skip_reason": None,
    }

    try:
        v3, v3_load_s = try_load_v3(ckpt)
        status["v3_load_s"] = v3_load_s
        status["v3_scored_main"] = score_v3(v3, main_rows, RAW / "v3_alignscore.jsonl")
        status["v3_scored_threshold"] = score_v3(v3, thr_rows, RAW_THR / "v3_alignscore.jsonl")
        status["v3_ran"] = True
        del v3
    except Exception as exc:
        status["v3_skip_reason"] = f"{type(exc).__name__}: {exc}"

    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps(status), flush=True)


if __name__ == "__main__":
    main()
