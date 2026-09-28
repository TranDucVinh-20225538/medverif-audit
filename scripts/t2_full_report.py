#!/usr/bin/env python3
"""Summarize full T2 spend and stratum pass rates."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data" / "t2" / "instances_full_pending.jsonl"
RAW = ROOT / "results" / "raw" / "t2_full"
OUT = ROOT / "notes" / "t2_full_report.md"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_scores(name: str) -> dict[str, dict]:
    path = RAW / f"{name}.jsonl"
    return {row["instance_id"]: row for row in read_jsonl(path)}


def main() -> None:
    rows = read_jsonl(INST)
    inst_by_id = {r["instance_id"]: r for r in rows}
    verifiers = ("v1b_medscore", "v5_ragas_nli")
    lines = ["# T2 full report", ""]
    credit = {}
    cp = ROOT / "notes" / "openrouter_credit.json"
    if cp.is_file():
        credit = json.loads(cp.read_text())

    total_spend = 0.0
    n_scored = 0
    for v in verifiers:
        for rec in load_scores(v).values():
            total_spend += float(rec.get("api_cost_usd") or 0)
            n_scored += 1

    n_inst = len(rows)
    per_inst = total_spend / max(n_scored // len(verifiers), 1) if n_scored else 0.0
    lines += [
        f"- Instances: **{n_inst}**",
        f"- Scored rows: **{n_scored}** (target {n_inst * 2})",
        f"- Spend: **${total_spend:.4f}**",
        f"- Approx $/instance/verifier: **${per_inst:.5f}**",
        f"- OpenRouter limit_remaining: **{credit.get('limit_remaining', '—')}**",
        "",
        "Models: `notes/t2_models.json`.",
        "",
    ]

    for v in verifiers:
        scores = load_scores(v)
        lines.append(f"## {v}")
        lines.append("")
        by_cond = defaultdict(lambda: {"pass": 0, "fail": 0, "parse": 0, "n": 0})
        for iid, inst in inst_by_id.items():
            rec = scores.get(iid)
            if not rec:
                continue
            key = inst["condition"]
            if inst["condition"] == "E1-claim":
                key = f"E1-claim/{inst.get('magnitude')}"
            if inst["condition"] == "INV-claim":
                key = f"INV/{inst.get('magnitude')}"
            by_cond[key]["n"] += 1
            vd = rec.get("verdict")
            if vd == "PASS":
                by_cond[key]["pass"] += 1
            elif vd == "PARSE_FAIL":
                by_cond[key]["parse"] += 1
            else:
                by_cond[key]["fail"] += 1
        lines.append("| Stratum | PASS | FAIL | PARSE | n |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for k in sorted(by_cond):
            b = by_cond[k]
            lines.append(f"| {k} | {b['pass']} | {b['fail']} | {b['parse']} | {b['n']} |")
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
