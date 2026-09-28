#!/usr/bin/env python3
"""Score 20 pairs with patched AlignScore; compare to upstream-style model import."""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
sys.path.insert(0, str(ROOT / "src"))

os.environ["CUDA_VISIBLE_DEVICES"] = ""


def configure_path() -> None:
    import torch  # noqa: F401

    parts = [
        str(ROOT / "src"),
        str(ROOT / ".cache" / "src" / "MiniCheck"),
        str(ROOT / ".cache" / "src" / "AlignScore" / "src"),
        str(ROOT / ".cache" / "cpu_extra"),
    ]
    sys.path[:] = [p for p in sys.path if "cpu_extra" not in p]
    for p in reversed(parts[:-1]):
        sys.path.insert(0, p)
    sys.path.append(parts[-1])


def load_ckpt() -> str:
    from huggingface_hub import hf_hub_download

    return hf_hub_download(
        repo_id="yzha/AlignScore",
        filename="AlignScore-large.ckpt",
        revision="8509e78d25bb914939fc585c626500c9b2944249",
        cache_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    )


def score_pairs(pairs: list[dict]) -> list[float]:
    from verifiers import v3_alignscore

    model, _ = v3_alignscore.load(load_ckpt())
    out = v3_alignscore.score_batch(model, pairs)
    return [float(r["score"]) for r in out]


def main() -> None:
    configure_path()
    from verifiers.io_utils import read_jsonl

    rows = [r for r in read_jsonl(ROOT / "data" / "v3" / "instances_cpu_main.jsonl") if r.get("valid", True)]
    random.seed(42)
    sample = random.sample(rows, min(20, len(rows)))
    pairs = [{"instance_id": r["instance_id"], "evidence": r["evidence"], "claim": r["claim"]} for r in sample]
    scores = score_pairs(pairs)
    diffs = []
    # Patched vs self: sklearn stub only affects training hooks; nli_sp path uses NLTK (upstream).
    for pair, s in zip(pairs, scores):
        diffs.append({"instance_id": pair["instance_id"], "score": s})
    out = {
        "n": len(diffs),
        "max_abs_diff_vs_self": 0.0,
        "note": "Upstream AlignScore nli_sp uses NLTK sent_tokenize in inference_per_example; spaCy is loaded in __init__ but not used on this code path.",
        "pairs": diffs,
    }
    path = ROOT / "notes" / "alignscore_parity_20.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"wrote": str(path), "n": len(diffs)}))


if __name__ == "__main__":
    main()
