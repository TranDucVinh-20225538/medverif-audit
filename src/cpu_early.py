"""CPU early scoring for V2a and V3. Resumes by instance_id. Skips INV-paraphrase."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""

import huggingface_hub.file_download as hf_file_download

hf_file_download.is_xet_available = lambda: False

from huggingface_hub import hf_hub_download
from verifiers.io_utils import append_jsonl, done_ids, read_jsonl

ROOT = Path("/data2/hpcshared/medverif-audit")
EARLY = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
RAW = ROOT / "results" / "raw"
RAW_THR = ROOT / "results" / "raw_threshold"
PROBE_N = 20
ETA_LIMIT_S = 3 * 3600


def ensure_nltk() -> None:
    import nltk

    path = Path(os.environ.get("NLTK_DATA") or (Path.home() / "nltk_data"))
    path.mkdir(parents=True, exist_ok=True)
    os.environ["NLTK_DATA"] = str(path)
    nltk.download("punkt", download_dir=str(path), quiet=True)
    nltk.download("punkt_tab", download_dir=str(path), quiet=True)


def fetch(repo: str, revision: str, filename: str) -> Path:
    return Path(hf_hub_download(
        repo_id=repo,
        filename=filename,
        revision=revision,
        cache_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    ))


def prepare_weights() -> Path:
    from huggingface_hub import snapshot_download

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
    return fetch(
        "yzha/AlignScore",
        "8509e78d25bb914939fc585c626500c9b2944249",
        "AlignScore-large.ckpt",
    )


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


def score_rows(kind: str, model, rows: list[dict], out_path: Path) -> float:
    from verifiers import v2a_minicheck, v3_alignscore

    done = done_ids(out_path)
    todo = [row for row in rows if row["instance_id"] not in done]
    if not todo:
        return 0.0
    started = time.perf_counter()
    step = 4
    for offset in range(0, len(todo), step):
        chunk = todo[offset:offset + step]
        try:
            if kind == "v2a":
                scored = v2a_minicheck.score_batch(model, chunk)
            else:
                scored = v3_alignscore.score_batch(model, chunk)
        except Exception as exc:
            scored = [{
                "instance_id": row["instance_id"],
                "raw_output": repr(exc),
                "score": None,
                "verdict": "PARSE_FAIL",
                "latency_s": None,
                "verifier": "v2a_minicheck" if kind == "v2a" else "v3_alignscore",
            } for row in chunk]
        append_jsonl(out_path, scored)
    return time.perf_counter() - started


def main() -> None:
    ensure_nltk()
    ckpt = prepare_weights()
    main_rows, thr_rows = split_rows()
    print(json.dumps({"main": len(main_rows), "threshold": len(thr_rows)}), flush=True)
    from verifiers import v3_alignscore

    v3, v3_load = v3_alignscore.load(str(ckpt))
    from verifiers import v2a_minicheck

    v2a, v2a_load = v2a_minicheck.load()
    probe = main_rows[:PROBE_N]
    t2 = score_rows("v2a", v2a, probe, RAW / "v2a_minicheck.jsonl")
    del v2a
    t3 = score_rows("v3", v3, probe, RAW / "v3_alignscore.jsonl")
    per = (t2 + t3) / max(len(probe), 1)
    eta_all = per * (len(main_rows) + len(thr_rows))
    eta_main = per * len(main_rows)
    use_threshold = eta_all <= ETA_LIMIT_S
    print(json.dumps({
        "probe_n": len(probe),
        "v2a_probe_s": t2,
        "v3_probe_s": t3,
        "v2a_load_s": v2a_load,
        "v3_load_s": v3_load,
        "sec_per_item_both": per,
        "eta_all_s": eta_all,
        "eta_main_s": eta_main,
        "score_threshold": use_threshold,
    }), flush=True)
    (ROOT / "data" / "v3" / "cpu_probe.json").write_text(json.dumps({
        "probe_n": len(probe),
        "v2a_probe_s": t2,
        "v3_probe_s": t3,
        "eta_all_s": eta_all,
        "eta_main_s": eta_main,
        "score_threshold": use_threshold,
    }, indent=2) + "\n")
    # Probe rows are already in the raw files. Resume skips them.
    rest_main = main_rows
    t2_rest = 0.0
    # v2a was freed. Reload for the remainder.
    v2a, _ = v2a_minicheck.load()
    t2_rest = score_rows("v2a", v2a, rest_main, RAW / "v2a_minicheck.jsonl")
    del v2a
    if use_threshold:
        v2a, _ = v2a_minicheck.load()
        score_rows("v2a", v2a, thr_rows, RAW_THR / "v2a_minicheck.jsonl")
        del v2a
    score_rows("v3", v3, rest_main, RAW / "v3_alignscore.jsonl")
    if use_threshold:
        score_rows("v3", v3, thr_rows, RAW_THR / "v3_alignscore.jsonl")
    print(json.dumps({"v2a_rest_s": t2_rest, "done": True, "threshold": use_threshold}), flush=True)


if __name__ == "__main__":
    main()
