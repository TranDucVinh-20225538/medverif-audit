#!/usr/bin/env python3
"""T9 block rates with bootstrap CIs + example rows per group."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "notes" / "t9_t10_report.md"
OUT_JSON = ROOT / "notes" / "t9_report.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def bootstrap_rate(flags: list[int], n_boot: int = 2000, seed: int = 42) -> tuple[float, float, float]:
    if not flags:
        return float("nan"), float("nan"), float("nan")
    n = len(flags)
    mean = sum(flags) / n
    rng = random.Random(seed)
    boots = sorted(sum(rng.choice(flags) for _ in range(n)) / n for _ in range(n_boot))
    lo = boots[int(0.025 * n_boot)]
    hi = boots[int(0.975 * n_boot)]
    return mean, lo, hi


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", type=Path, default=ROOT / "results/raw/t9/alignscore_rail.jsonl")
    ap.add_argument("--examples", type=int, default=5)
    args = ap.parse_args()

    rows = read_jsonl(args.scores)
    by_group: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_group[r.get("t9_group") or "?"].append(r)

    stats = {}
    examples = {}
    for g, grp in sorted(by_group.items()):
        blocked = [int(r.get("blocked")) for r in grp if r.get("blocked") is not None]
        m, lo, hi = bootstrap_rate(blocked)
        stats[g] = {"n": len(grp), "n_decided": len(blocked), "block_rate": m, "ci_lo": lo, "ci_hi": hi}
        examples[g] = [
            {
                "instance_id": r.get("instance_id"),
                "claim": (r.get("claim") or "")[:400],
                "evidence": (r.get("evidence") or "")[:400],
                "alignscore": r.get("alignscore"),
                "decision": r.get("decision"),
            }
            for r in grp[: args.examples]
        ]

    payload = {"n_total": len(rows), "groups": stats, "examples": examples}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T9 / T10 report (partial — T9 scores)",
        "",
        "## T9 AlignScore rail block rates",
        "",
        "| group | n | block_rate | 95% CI |",
        "|---|---:|---:|---|",
    ]
    for g, s in stats.items():
        lines.append(
            f"| {g} | {s['n']} | {s['block_rate']:.3f} | [{s['ci_lo']:.3f}, {s['ci_hi']:.3f}] |"
        )
    lines.append("")
    for g, ex in examples.items():
        lines.append(f"### Group {g} examples (up to {args.examples})")
        lines.append("")
        for i, e in enumerate(ex, 1):
            lines.append(f"{i}. `{e['instance_id']}` — **{e['decision']}** (score={e['alignscore']})")
            lines.append(f"   - answer: {e['claim'][:200]}…")
            lines.append(f"   - evidence: {e['evidence'][:200]}…")
        lines.append("")

    existing = OUT_MD.read_text() if OUT_MD.is_file() and "T10" in OUT_MD.read_text() else ""
    if "## T10" in existing:
        t10_part = existing.split("## T10", 1)[1]
        lines.append("## T10" + t10_part)
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
