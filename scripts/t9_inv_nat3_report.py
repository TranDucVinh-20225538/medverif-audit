#!/usr/bin/env python3
"""T9 NeMo: INV-unit subset using qc/nat3_labels.csv (fractions k/n + bootstrap CI)."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from review_filters import effective_unit_natural_y, unit_natural_labels  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402
from t14_t3_filter_report import inv_span_before  # noqa: E402

OUT_MD = ROOT / "notes/t9_inv_nat3_report.md"
OUT_JSON = ROOT / "notes/t9_inv_nat3_report.json"
MAIN = ROOT / "data/v3/instances_main.jsonl"
EXPAND = ROOT / "data/expand/instances_cpu_early.jsonl"
def _pick_scores(name: str) -> Path:
    for p in (
        ROOT / "results/raw_node30/t9" / name,
        ROOT / "results/raw/t9" / name,
    ):
        if p.is_file():
            return p
    return ROOT / "results/raw/t9" / name


SCORES_BASE = _pick_scores("alignscore_rail.jsonl")
SCORES_LARGE = _pick_scores("alignscore_rail_large.jsonl")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def bootstrap_blocked(flags: list[int], n_boot: int = 2000, seed: int = 42) -> tuple[float, float, float]:
    if not flags:
        return float("nan"), float("nan"), float("nan")
    n = len(flags)
    mean = sum(flags) / n
    rng = random.Random(seed)
    boots = sorted(sum(rng.choice(flags) for _ in range(n)) / n for _ in range(n_boot))
    return mean, boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]


def inv_nat3_subset() -> list[dict]:
    labels = unit_natural_labels()
    rows = []
    for path in (MAIN, EXPAND):
        for r in read_jsonl(path):
            if not r.get("valid", True):
                continue
            if r.get("condition") != "INV-claim" or r.get("magnitude") != "unit_conversion":
                continue
            orig = inv_span_before(r)
            rule_y = bool(rule_natural_unit_conversion_label(orig))
            nat = effective_unit_natural_y(r["base_id"], rule_y)
            human = labels.get(r["base_id"], "")
            rows.append(
                {
                    **r,
                    "nat3_human": human,
                    "nat3_effective_y": nat,
                    "inv_span_before": orig,
                }
            )
    return rows


def score_by_id(path: Path) -> dict[str, dict]:
    return {r["instance_id"]: r for r in read_jsonl(path)}


def block_stats(subset: list[dict], scores: dict[str, dict]) -> dict:
    flags = []
    matched = 0
    for r in subset:
        sc = scores.get(r["instance_id"])
        if not sc or sc.get("blocked") is None:
            continue
        matched += 1
        flags.append(int(sc["blocked"]))
    blocked = sum(flags)
    rate, lo, hi = bootstrap_blocked(flags)
    return {
        "n_instances": len(subset),
        "n_scored": matched,
        "blocked_k": blocked,
        "not_blocked_k": matched - blocked,
        "block_rate": rate,
        "ci_lo": lo,
        "ci_hi": hi,
        "fraction": f"{blocked}/{matched}" if matched else "NA",
    }


def main() -> None:
    all_inv = inv_nat3_subset()
    nat_y = [r for r in all_inv if r["nat3_effective_y"]]
    nat_n = [r for r in all_inv if not r["nat3_effective_y"]]

    sb, sl = score_by_id(SCORES_BASE), score_by_id(SCORES_LARGE)
    payload = {
        "nat3_source": "qc/nat3_labels.csv",
        "inv_unit_total": len(all_inv),
        "nat3_y": len(nat_y),
        "nat3_n": len(nat_n),
        "alignscore_base": {
            "all_inv_unit": block_stats(all_inv, sb),
            "nat3_y_only": block_stats(nat_y, sb),
            "nat3_n_only": block_stats(nat_n, sb),
        },
        "alignscore_large": {
            "all_inv_unit": block_stats(all_inv, sl),
            "nat3_y_only": block_stats(nat_y, sl),
            "nat3_n_only": block_stats(nat_n, sl),
        },
    }

    def row(label: str, st: dict) -> str:
        if not st["n_scored"]:
            return f"| {label} | {st['n_instances']} | 0 | NA |"
        return (
            f"| {label} | {st['n_scored']} | **{st['blocked_k']}/{st['n_scored']}** "
            f"({st['block_rate']:.3f}) | [{st['ci_lo']:.3f}, {st['ci_hi']:.3f}] |"
        )

    lines = [
        "# T9 NeMo — INV-claim unit subset (nat3 labels)",
        "",
        "Subset: main+expand **INV-claim** `unit_conversion`. "
        "**nat3 Y** = `effective_unit_natural_y` from `qc/nat3_labels.csv`. "
        "Block if AlignScore rail score < 0.5. Rates reported as **k/n**.",
        "",
        f"- INV-unit rows: **{len(all_inv)}** (nat3 Y: **{len(nat_y)}**, N: **{len(nat_n)}**)",
        "",
        "## AlignScore-base rail",
        "",
        "| slice | n scored | blocked k/n | 95% CI |",
        "| --- | ---: | --- | --- |",
        row("all INV-unit", payload["alignscore_base"]["all_inv_unit"]),
        row("nat3 Y (natural)", payload["alignscore_base"]["nat3_y_only"]),
        row("nat3 N (unnatural)", payload["alignscore_base"]["nat3_n_only"]),
        "",
        "## AlignScore-large rail",
        "",
        "| slice | n scored | blocked k/n | 95% CI |",
        "| --- | ---: | --- | --- |",
        row("all INV-unit", payload["alignscore_large"]["all_inv_unit"]),
        row("nat3 Y (natural)", payload["alignscore_large"]["nat3_y_only"]),
        row("nat3 N (unnatural)", payload["alignscore_large"]["nat3_n_only"]),
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT_MD), "nat3_y": len(nat_y)}, indent=2))


if __name__ == "__main__":
    main()
