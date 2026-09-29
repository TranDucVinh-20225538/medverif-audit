#!/usr/bin/env python3
"""T9 block rates with bootstrap CIs; base + large + stratum splits + manifest changelog."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "notes" / "t9_t10_report.md"
OUT_JSON = ROOT / "notes" / "t9_report.json"
CHANGELOG = ROOT / "notes/t9_manifest_changelog.json"
MANIFEST = ROOT / "data/t9/manifest.json"


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


def load_inst_meta() -> dict[str, dict]:
    meta: dict[str, dict] = {}
    for path in (ROOT / "data" / "t9").glob("instances_*.jsonl"):
        for r in read_jsonl(path):
            meta[r["instance_id"]] = r
    return meta


def analyze_scores(rows: list[dict], inst_meta: dict[str, dict]) -> dict:
    def enrich(r: dict) -> dict:
        m = inst_meta.get(r.get("instance_id") or "", {})
        return {**r, **{k: m.get(k) for k in ("stratum", "eco_category_final", "t9_group")}}

    rows = [enrich(r) for r in rows]
    by_group: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_group[r.get("t9_group") or "?"].append(r)

    def stratum_key(r: dict) -> str:
        if r.get("stratum"):
            return str(r["stratum"])
        if r.get("eco_category_final"):
            return str(r["eco_category_final"])
        return "unsplit"

    stats = {}
    strata_stats: dict[str, dict] = {}
    for g, grp in sorted(by_group.items()):
        blocked = [int(r.get("blocked")) for r in grp if r.get("blocked") is not None]
        m, lo, hi = bootstrap_rate(blocked)
        stats[g] = {"n": len(grp), "n_decided": len(blocked), "block_rate": m, "ci_lo": lo, "ci_hi": hi}
        if g == "b":
            by_s: dict[str, list[dict]] = defaultdict(list)
            for r in grp:
                by_s[stratum_key(r)].append(r)
            for sk, sub in sorted(by_s.items()):
                bl = [int(x.get("blocked")) for x in sub if x.get("blocked") is not None]
                sm, slo, shi = bootstrap_rate(bl)
                strata_stats[f"b:{sk}"] = {
                    "n": len(sub),
                    "n_decided": len(bl),
                    "block_rate": sm,
                    "ci_lo": slo,
                    "ci_hi": shi,
                }
        if g == "a":
            strata_stats["a:eco_verbatim"] = stats["a"]

    endpoint = rows[0].get("endpoint") if rows else None
    return {
        "n_total": len(rows),
        "endpoint": endpoint,
        "groups": stats,
        "strata": strata_stats,
    }


def fmt_row(label: str, s: dict) -> str:
    return f"| {label} | {s['n']} | {s['block_rate']:.3f} | [{s['ci_lo']:.3f}, {s['ci_hi']:.3f}] |"


def load_changelog_md() -> list[str]:
    if not CHANGELOG.is_file():
        return ["_(manifest changelog not generated; run scripts/t9_manifest_delta.py)_", ""]
    ch = json.loads(CHANGELOG.read_text())
    lines = [
        "## Manifest: legacy scores → current inputs",
        "",
        ch.get("policy_summary", ""),
        "",
        "| metric | value |",
        "|---|---:|",
        f"| Legacy scored lines | {ch.get('legacy_score_lines', '?')} |",
        f"| Legacy unique instance_ids | {ch.get('legacy_unique_instance_ids', '?')} |",
        f"| Legacy duplicate extra lines | {ch.get('legacy_duplicate_line_count', 0)} |",
        f"| **Current manifest (scored)** | **{ch.get('current_manifest_n', '?')}** |",
        f"| Unique instance_ids dropped | {ch.get('unique_ids_removed', '?')} |",
        "",
        "**Removal reasons (unique instance_ids):**",
        "",
    ]
    for reason, cnt in sorted((ch.get("removal_reason_counts") or {}).items()):
        lines.append(f"- `{reason}`: **{cnt}**")
    lines.extend(["", "**Group-b stratum (current manifest):**", ""])
    if MANIFEST.is_file():
        m = json.loads(MANIFEST.read_text())
        bs = m.get("b_strata") or {}
        lines.append(f"- `eco_reexpressed`: {bs.get('eco_reexpressed', '?')}")
        lines.append(f"- `inv_unit_natural`: {bs.get('inv_unit_natural', '?')}")
    lines.append("")
    return lines


def eco_source_compare(payload: dict) -> list[str]:
    """Side-by-side group a (eco verbatim) vs group b (eco + inv reexpressed)."""
    lines = [
        "## Eco source comparison (group a vs group b)",
        "",
        "Group **a** = T4 eco exact verbatim only. Group **b** = eco re-expressions + natural INV unit conversions.",
        "",
        "| checkpoint | slice | n | block_rate | 95% CI |",
        "|---|---|---:|---:|---|",
    ]
    for label, key in ("AlignScore-base", "base"), ("AlignScore-large", "large"):
        block = payload.get(key)
        if not block:
            continue
        for g in ("a", "b"):
            s = block["groups"].get(g)
            if s:
                lines.append(
                    f"| {label} | group {g} | {s['n']} | {s['block_rate']:.3f} | "
                    f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}] |"
                )
        for sk, s in sorted((block.get("strata") or {}).items()):
            if sk.startswith("b:"):
                lines.append(
                    f"| {label} | {sk} | {s['n']} | {s['block_rate']:.3f} | "
                    f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}] |"
                )
    lines.append("")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores-base", type=Path, default=ROOT / "results/raw/t9/alignscore_rail.jsonl")
    ap.add_argument("--scores-large", type=Path, default=ROOT / "results/raw/t9/alignscore_rail_large.jsonl")
    args = ap.parse_args()

    inst_meta = load_inst_meta()
    base_rows = read_jsonl(args.scores_base)
    large_rows = read_jsonl(args.scores_large)

    payload = {
        "manifest_n": len(read_jsonl(MANIFEST.parent / "instances_all.jsonl")),
        "base": analyze_scores(base_rows, inst_meta) if base_rows else None,
        "large": analyze_scores(large_rows, inst_meta) if large_rows else None,
    }
    if CHANGELOG.is_file():
        payload["manifest_changelog"] = json.loads(CHANGELOG.read_text())

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T9 / T10 report",
        "",
        "NeMo Guardrails **0.24.1** rail (`FACT_CHECK_THRESHOLD=0.5`, block if score < 0.5).",
        f"Scored manifest: **`data/t9/instances_all.jsonl`** (n={payload.get('manifest_n', '?')}).",
        "",
    ]
    lines.extend(load_changelog_md())

    for model_name, block in ("AlignScore-base", payload.get("base")), ("AlignScore-large", payload.get("large")):
        if not block:
            lines.append(f"## T9 — {model_name}\n\n_(no scores)_\n")
            continue
        lines.extend([
            f"## T9 — {model_name}",
            "",
            f"Endpoint: `{block.get('endpoint', '?')}` · n={block['n_total']}",
            "",
            "### Groups a–d",
            "",
            "| group | n | block_rate | 95% CI |",
            "|---|---:|---:|---|",
        ])
        for g in ("a", "b", "c", "d"):
            s = block["groups"].get(g)
            if s:
                lines.append(fmt_row(g, s))
        if block.get("strata"):
            lines.extend([
                "",
                "### Group b strata",
                "",
                "| slice | n | block_rate | 95% CI |",
                "|---|---:|---:|---|",
            ])
            for sk, s in block["strata"].items():
                if sk.startswith("b:") or sk == "a:eco_verbatim":
                    lines.append(fmt_row(sk, s))
        lines.append("")

    lines.extend(eco_source_compare(payload))

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"wrote": str(OUT_JSON), "wrote_md": str(OUT_MD)}, indent=2))


if __name__ == "__main__":
    main()
