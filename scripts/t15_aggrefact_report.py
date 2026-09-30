#!/usr/bin/env python3
"""Balanced accuracy on AggreFact test for base vs T15 ft (same instance_ids)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_scores(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.is_file():
        return out
    for line in path.open():
        if line.strip():
            row = json.loads(line)
            out[row["instance_id"]] = row
    return out


def main() -> None:
    test = ROOT / "data/t8/aggrefact/test.jsonl"
    labels: dict[str, int] = {}
    by_ds: dict[str, list[str]] = defaultdict(list)
    for line in test.open():
        if not line.strip():
            continue
        row = json.loads(line)
        iid = row.get("contamination_identifier") or row.get("instance_id")
        labels[iid] = int(row["label"])
        by_ds[row.get("dataset", "?")].append(iid)

    base = read_scores(ROOT / "results/raw/t15/base_aggrefact_test.jsonl")
    ft = read_scores(ROOT / "results/raw/t15/ft_aggrefact_test.jsonl")
    common = sorted(set(labels) & set(base) & set(ft))
    lines = ["## AggreFact test (paired base vs ft)", ""]

    def bal_acc(scores: dict[str, dict], ids: list[str]) -> tuple[float, int]:
        if not ids:
            return float("nan"), 0
        ok = 0
        for iid in ids:
            pred = 1 if scores[iid]["verdict"] == "PASS" else 0
            if pred == labels[iid]:
                ok += 1
        return ok / len(ids), len(ids)

    for tag, scores in (("base", base), ("ft", ft)):
        acc, n = bal_acc(scores, common)
        lines.append(f"- **{tag}** overall balanced acc={acc:.4f} (n={n} paired)")
        for ds, ids in sorted(by_ds.items()):
            sub = [i for i in ids if i in common]
            a, nn = bal_acc(scores, sub)
            if nn:
                lines.append(f"  - {ds}: {a:.4f} (n={nn})")
    print("\n".join(lines))
    return lines


if __name__ == "__main__":
    main()
