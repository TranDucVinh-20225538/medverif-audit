#!/usr/bin/env python3
"""Merge cpuverif rescoring chunks (full MiniCheck rescore + 30-row probes) and compare verdicts
with every unrecorded-env score file they cover. Writes notes/minicheck_cpuverif_agreement.json."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from minicheck_cpuverif_build import CHECKER_FILES, GROUP_DIRS, PROBE_CHECKERS  # noqa: E402

CHUNKS = ROOT / "results/raw/minicheck_cpuverif/chunks"
MERGED = ROOT / "results/raw/minicheck_cpuverif"
OUT = ROOT / "notes/minicheck_cpuverif_agreement.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def score_of(row: dict) -> float | None:
    for key in ("score", "released_parser_score"):
        if row.get(key) is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                pass
    return None


def compare(new: dict[str, dict], old_path: Path) -> dict:
    old = {r["instance_id"]: r for r in read_jsonl(old_path)}
    common = sorted(set(new) & set(old))
    disagree = [i for i in common if new[i].get("verdict") != old[i].get("verdict")]
    diffs = [abs(a - b) for i in common if (a := score_of(new[i])) is not None and (b := score_of(old[i])) is not None]
    return {
        "n_compared": len(common),
        "verdict_agree": len(common) - len(disagree),
        "agreement": (len(common) - len(disagree)) / len(common) if common else None,
        "mean_abs_score_diff": sum(diffs) / len(diffs) if diffs else None,
        "max_abs_score_diff": max(diffs) if diffs else None,
        "disagree_ids": disagree,
    }


def main() -> None:
    merged: dict[tuple[str, str, str], dict[str, dict]] = defaultdict(dict)
    for path in sorted(CHUNKS.glob("*.jsonl")):
        parts = path.stem.split("__")
        if parts[0] == "probe":
            key = ("probe30", parts[1], parts[2])
        else:
            key = ("full", parts[0], parts[1])
        for r in read_jsonl(path):
            merged[key][r["instance_id"]] = r
    files: dict[str, dict] = {}
    for (mode, cid, group), rows in sorted(merged.items()):
        if mode == "full":
            with (MERGED / f"{cid}__{group}.jsonl").open("w") as fh:
                for r in rows.values():
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fname = CHECKER_FILES[cid]
        else:
            fname = PROBE_CHECKERS[cid][0]
        for d in GROUP_DIRS[group]:
            old = ROOT / d / fname
            if not old.is_file():
                continue
            rel = str(old.relative_to(ROOT))
            res = compare(rows, old)
            if not res["n_compared"]:
                continue
            files[rel] = {"checker": cid, "group": group, "mode": mode, "n_rescored": len(rows), **res}
            print(f"{mode:8s} {rel:55s} {res['verdict_agree']}/{res['n_compared']} max|d|={res['max_abs_score_diff']}")
    OUT.write_text(json.dumps({"reference_env": "cpuverif (SummaC: cpuverif_legacy)", "files": files}, indent=1) + "\n")


if __name__ == "__main__":
    main()
