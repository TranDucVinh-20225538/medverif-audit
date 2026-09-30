#!/usr/bin/env python3
"""GPU AggreFact test scoring via MiniCheck library (base + T15 ft, same code path as CPU)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verifiers import minicheck_roberta_lib as mcl  # noqa: E402
from verifiers.io_utils import append_jsonl, done_ids, read_jsonl  # noqa: E402

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
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("GPU required for t15_aggrefact_gpu_eval (MiniCheck library on CUDA)")
    fine = leg == "ft"
    verifier = "t15_minicheck_roberta" if fine else "t6a_minicheck_roberta"
    model, meta, _ = mcl.load(fine_tuned=fine, force_cpu=False)
    print(json.dumps({"t15_gpu": "load", "leg": leg, "verifier": verifier, **meta}), flush=True)
    return model, meta, verifier


def compare_ref(ref_path: Path, scored: list[dict]) -> dict:
    ref = {json.loads(line)["instance_id"]: json.loads(line) for line in ref_path.open() if line.strip()}
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


def balanced_acc(rows: list[dict], scored: list[dict]) -> dict:
    labels = {row_id(r): int(r["label"]) for r in rows}
    by_id = {s["instance_id"]: s for s in scored}
    common = [iid for iid in labels if iid in by_id]
    if not common:
        return {"n": 0, "balanced_acc": None}
    ok = sum(
        1
        for iid in common
        if (1 if by_id[iid]["verdict"] == "PASS" else 0) == labels[iid]
    )
    return {"n": len(common), "balanced_acc": ok / len(common)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", choices=("base", "ft"), required=True)
    parser.add_argument("--calibrate-only", action="store_true")
    parser.add_argument(
        "--ref",
        type=Path,
        default=ROOT
        / "results/raw/t15/_archive_cpu_minicheck_partial_20260930/base_aggrefact_test.jsonl",
        help="CPU MiniCheck library scores (t6a_minicheck_roberta) for GPU cal",
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

    model, meta, verifier = load_bundle(leg=args.leg)
    batch = int(meta.get("batch_size") or 16)
    scored_all: list[dict] = []
    t0 = time.perf_counter()
    for off in range(0, len(todo), batch):
        chunk = todo[off : off + batch]
        scored = mcl.score_batch(model, chunk, verifier, meta=meta)
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
                    "elapsed_s": round(time.perf_counter() - t0, 1),
                }
            ),
            flush=True,
        )

    if args.calibrate_only:
        stat = compare_ref(args.ref, scored_all)
        bacc = balanced_acc(rows[:CAL_N], scored_all)
        payload = {
            "leg": args.leg,
            "path": "minicheck_library_gpu",
            "minicheck_commit": mcl.MINICHECK_COMMIT,
            "published_aggrefact_bacc_reference": mcl.PUBLISHED_AGGREFACT_BACC,
            "cal_subset_balanced_acc": bacc.get("balanced_acc"),
            "cal_subset_n": bacc.get("n"),
            **stat,
        }
        cal_path = ROOT / "notes/t15_aggrefact_gpu_calibration.json"
        cal_path.write_text(json.dumps(payload, indent=2) + "\n")
        print(json.dumps(payload, indent=2))
        return 0 if stat.get("pass") else 1

    print(json.dumps({"t15_gpu": "done", "leg": args.leg, "out": str(out), "new_rows": len(scored_all)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
