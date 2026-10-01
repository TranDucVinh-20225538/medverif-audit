#!/usr/bin/env python3
"""Balanced accuracy on AggreFact test for base vs T15 ft (same instance_ids)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from t15_card_report import aggrefact_bacc  # noqa: E402


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

    raw = ROOT / "results/raw/t15_cpuverif"
    base = read_scores(raw / "base_aggrefact_test.jsonl")
    ft = read_scores(raw / "ft_aggrefact_test.jsonl")
    common = set(labels) & set(base) & set(ft)
    lines = ["## AggreFact test (paired base vs ft; env cpuverif)", ""]
    for tag, scores in (("base", base), ("ft", ft)):
        r = aggrefact_bacc(scores, labels, by_ds, common)
        lines.append(f"- **{tag}** LLM-AggreFact BAcc (macro over datasets)={r['macro_bacc']:.4f} · micro BAcc={r['micro_bacc']:.4f} "
                     f"· accuracy={r['accuracy']:.4f} (n={r['n']} paired)")
        lines += [f"  - {ds}: BAcc {v['bacc']:.4f} (n={v['n']})" for ds, v in r["per_dataset"].items()]
    print("\n".join(lines))
    return lines


if __name__ == "__main__":
    main()
