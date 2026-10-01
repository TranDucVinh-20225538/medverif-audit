#!/usr/bin/env python3
"""Shared in-process loaders for the five small checkers used by journal chain 2 (UNF + RD).

Uses the repo wrappers (src/verifiers/*), i.e. the paper's chunking, thresholds and CPU patches:
  t6a_minicheck_roberta, t6a_minicheck_deberta, t6a_alignscore_base, v2a_minicheck (Flan-T5-Large),
  v3_alignscore (AlignScore-large ckpt, pinned HF revision).

`alignscore_compat()` is applied right before an AlignScore wrapper is imported.  It is a no-op on the
paper's cpuverif env; on newer stacks it restores two things AlignScore's source relies on and that do
not change inference: `transformers.AdamW` (imported but unused at inference) and lightning's old
behaviour of `instance.load_from_checkpoint()` acting as the classmethod.

CLI (resumable by instance_id; file names follow the paper's raw-score conventions):
  python scripts/journal2/small_checkers.py --instances X.jsonl --outdir DIR --checker <id>|all [--limit N]
  -> DIR/t6_minicheck_roberta.jsonl, t6_minicheck_deberta.jsonl, t6_alignscore_base.jsonl,
     v2a_minicheck.jsonl, v3_alignscore.jsonl
"""

from __future__ import annotations

import argparse
import functools
import gc
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ["MEDVERIF_M1"] = "0"  # never stack the pre-registered M1 normalizer on top of these runs

CHECKERS = ("t6a_minicheck_roberta", "t6a_minicheck_deberta", "t6a_alignscore_base", "v2a_minicheck", "v3_alignscore")
OUT_NAME = {"t6a_minicheck_roberta": "t6_minicheck_roberta.jsonl", "t6a_minicheck_deberta": "t6_minicheck_deberta.jsonl",
            "t6a_alignscore_base": "t6_alignscore_base.jsonl", "v2a_minicheck": "v2a_minicheck.jsonl",
            "v3_alignscore": "v3_alignscore.jsonl"}
AS_LARGE_REV = "8509e78d25bb914939fc585c626500c9b2944249"


def alignscore_compat() -> list:
    applied = []
    try:
        import torch
        import transformers

        if not hasattr(transformers, "AdamW"):
            transformers.AdamW = torch.optim.AdamW
            applied.append("transformers.AdamW")
    except Exception:  # noqa: BLE001
        pass
    try:
        from pytorch_lightning.utilities import model_helpers as mh

        impl = getattr(mh, "_restricted_classmethod_impl", None)
        if impl is not None and not getattr(impl, "_jr2_compat", False):
            def _get(self, instance, cls=None):
                cls_type = cls if cls is not None else type(instance)

                @functools.wraps(self.method)
                def wrapper(*a, **k):
                    return self.method(cls_type, *a, **k)
                wrapper.__func__ = self.method
                return wrapper
            impl.__get__ = _get
            impl._jr2_compat = True
            applied.append("lightning.load_from_checkpoint")
    except Exception:  # noqa: BLE001
        pass
    return applied


def env_tag(env: str = None) -> dict:
    import torch
    import transformers

    return {"env": env or os.environ.get("MEDVERIF_SCORE_ENV_TAG", "box_cpu"), "torch": torch.__version__,
            "transformers": transformers.__version__, "python": platform.python_version()}


def load(checker: str):
    if checker in ("t6a_minicheck_roberta", "t6a_minicheck_deberta"):
        from verifiers import t6a_minicheck as mc

        model, _ = mc.load(checker)
        return lambda rows: mc.score_batch(model, rows, checker)
    if checker == "v2a_minicheck":
        from verifiers import v2a_minicheck as v2a

        model, _ = v2a.load()
        return lambda rows: v2a.score_batch(model, rows)
    if checker == "t6a_alignscore_base":
        alignscore_compat()
        from verifiers import t6a_alignscore_base as asb

        model, _ = asb.load()
        return lambda rows: asb.score_batch(model, rows)
    if checker == "v3_alignscore":
        alignscore_compat()
        from huggingface_hub import hf_hub_download
        from verifiers import v3_alignscore as v3

        ckpt = hf_hub_download("yzha/AlignScore", "AlignScore-large.ckpt", revision=AS_LARGE_REV,
                               cache_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"))
        model, _ = v3.load(ckpt)
        return lambda rows: v3.score_batch(model, rows)
    raise SystemExit("unknown checker " + checker)


def read_jsonl(p: Path) -> list:
    if not Path(p).is_file():
        return []
    return [json.loads(l) for l in Path(p).open(encoding="utf-8") if l.strip()]


def score_rows(rows: list, checker: str, out: Path, batch: int = 4, limit: int = 0, extra: dict = None,
               label: str = "") -> int:
    """Append {instance_id, score, verdict, verifier, **extra} rows to `out`; skips ids already there."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {r["instance_id"] for r in read_jsonl(out)}
    todo = [r for r in rows if r["instance_id"] not in done]
    if limit:
        todo = todo[:limit]
    print(json.dumps({"score": checker, "label": label, "todo": len(todo), "done": len(done)}), flush=True)
    if not todo:
        return 0
    fn = load(checker)
    t0 = time.time()
    for off in range(0, len(todo), batch):
        chunk = todo[off: off + batch]
        res = fn(chunk)
        with out.open("a", encoding="utf-8") as fh:
            for r in res:
                fh.write(json.dumps({"instance_id": r["instance_id"], "score": r["score"], "verdict": r["verdict"],
                                     "verifier": checker, **(extra or {})}) + "\n")
        n = off + len(chunk)
        if n % 100 < batch or n == len(todo):
            el = time.time() - t0
            print(json.dumps({"score": checker, "label": label, "n": n, "of": len(todo), "s_per_row": round(el / n, 3),
                              "eta_min": round(el / n * (len(todo) - n) / 60, 1)}), flush=True)
    del fn
    gc.collect()
    return len(todo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--checker", required=True, help="one id or 'all'")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=4)
    args = ap.parse_args()
    rows = [r for r in read_jsonl(Path(args.instances)) if r.get("valid", True)]
    try:
        import cpu_early as ce

        ce.ensure_nltk()
    except Exception as exc:  # noqa: BLE001
        print("nltk check:", exc)
    tag = env_tag()
    for ck in (CHECKERS if args.checker == "all" else [args.checker]):
        score_rows(rows, ck, Path(args.outdir) / OUT_NAME[ck], batch=args.batch, limit=args.limit, extra=tag)


if __name__ == "__main__":
    main()
