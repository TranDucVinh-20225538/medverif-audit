#!/usr/bin/env python3
"""Report balanced acc + bootstrap CI on T15 AggreFact subsample."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 42


def read_scores(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.is_file():
        return out
    for line in path.open():
        if line.strip():
            row = json.loads(line)
            out[row["instance_id"]] = row
    return out


def bal_acc(scores: dict[str, dict], labels: dict[str, int], ids: list[str]) -> float:
    if not ids:
        return float("nan")
    pairs = [(1 if scores[iid]["verdict"] == "PASS" else 0, labels[iid]) for iid in ids]
    pos = [p for p, y in pairs if y == 1]
    neg = [p for p, y in pairs if y == 0]
    tpr = sum(pos) / len(pos) if pos else float("nan")
    tnr = sum(1 - p for p in neg) / len(neg) if neg else float("nan")
    return (tpr + tnr) / 2


def bootstrap_ci(base_ok: list[bool], ft_ok: list[bool], n_boot: int = 2000) -> tuple[float, float]:
    rng = random.Random(SEED)
    n = len(base_ok)
    deltas = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        b = sum(base_ok[i] for i in idx) / n
        f = sum(ft_ok[i] for i in idx) / n
        deltas.append(f - b)
    deltas.sort()
    return deltas[int(0.025 * n_boot)], deltas[int(0.975 * n_boot)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=3000)
    args = parser.parse_args()
    sample_path = ROOT / "data/t15/aggrefact_subsample_3000.jsonl"
    labels: dict[str, int] = {}
    by_ds: dict[str, list[str]] = defaultdict(list)
    for line in sample_path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        iid = row.get("instance_id") or row.get("contamination_identifier")
        labels[iid] = int(row["label"])
        by_ds[row.get("dataset", "?")].append(iid)

    base = read_scores(ROOT / f"results/raw/t15/base_aggrefact_subsample_{args.n}.jsonl")
    ft = read_scores(ROOT / f"results/raw/t15/ft_aggrefact_subsample_{args.n}.jsonl")
    common = sorted(set(labels) & set(base) & set(ft))

    base_ok = [(1 if base[i]["verdict"] == "PASS" else 0) == labels[i] for i in common]
    ft_ok = [(1 if ft[i]["verdict"] == "PASS" else 0) == labels[i] for i in common]
    lo, hi = bootstrap_ci(base_ok, ft_ok)

    lines = [
        "# T15 evaluation (AggreFact **subsample**)",
        "",
        f"**Note:** Not the full 29k test — **stratified n={len(common)}** "
        f"(target {args.n}, seed={SEED}), proportional by `dataset`.",
        "",
        f"- Sample: `{sample_path.relative_to(ROOT)}`",
        "",
        "## Balanced accuracy (paired ids)",
        "",
        f"- **base** overall: {bal_acc(base, labels, common):.4f} (n={len(common)})",
        f"- **ft** overall: {bal_acc(ft, labels, common):.4f}",
        f"- **Δ(ft−base)** paired bootstrap 95% CI: [{lo:.4f}, {hi:.4f}]",
        "",
    ]
    for ds, ids in sorted(by_ds.items()):
        sub = [i for i in ids if i in common]
        if not sub:
            continue
        lines.append(
            f"- **{ds}:** base={bal_acc(base, labels, sub):.4f}, "
            f"ft={bal_acc(ft, labels, sub):.4f} (n={len(sub)})"
        )
    (ROOT / "notes/t15_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
