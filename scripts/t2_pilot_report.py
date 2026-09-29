#!/usr/bin/env python3
"""Summarize T2 pilot spend and verifier behavior (INV pass, E1 fail)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "t2" / "instances_pilot_100.jsonl"
RAW = ROOT / "results" / "raw" / "t2_pilot"
OUT = ROOT / "notes" / "t2_pilot_report.md"
MANIFEST = ROOT / "data" / "t2" / "manifest_full.json"


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
    out = {}
    for row in read_jsonl(path):
        out[row["instance_id"]] = row
    return out


def main() -> None:
    pilot = read_jsonl(PILOT)
    inst_by_id = {r["instance_id"]: r for r in pilot}
    verifiers = ("v1b_medscore", "v5_ragas_nli")
    lines = ["# T2 pilot report", ""]
    credit = {}
    cp = ROOT / "notes" / "openrouter_credit.json"
    if cp.is_file():
        credit = json.loads(cp.read_text())

    total_spend = 0.0
    n_scored = 0
    for v in verifiers:
        scores = load_scores(v)
        for rec in scores.values():
            total_spend += float(rec.get("api_cost_usd") or 0)
            n_scored += 1

    n_pilot = len(pilot)
    per_inst = total_spend / max(n_scored // len(verifiers), 1) if n_scored else 0.0
    full_n = 0
    mf = ROOT / "data" / "t2" / "manifest_full.json"
    if mf.is_file():
        full_n = json.loads(mf.read_text()).get("n_instances", 0)
    proj = per_inst * full_n * len(verifiers) if per_inst and full_n else None

    lines += [
        f"- Pilot instances: **{n_pilot}** (2 verifiers → **{n_pilot * 2}** API calls when complete)",
        f"- Scored rows in raw: **{n_scored}**",
        f"- Pilot spend (sum api_cost_usd in raw/t2_pilot): **${total_spend:.4f}**",
        f"- Approx $/instance/verifier: **${per_inst:.5f}**",
        f"- OpenRouter limit_remaining: **{credit.get('limit_remaining', '—')}**",
        "",
    ]
    if proj is not None:
        lines.append(f"- Projected full T2 (both verifiers, {full_n} instances): **~${proj:.2f}**")
        lines.append("")
    lines.append("**Full T2 run blocked** until `notes/t2_full_approved` exists.")
    lines.append("")

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
        inv = by_cond.get("INV/unit_conversion", {})
        e1 = sum(v["fail"] + v["pass"] for kk, v in by_cond.items() if kk.startswith("E1-claim"))
        e1_fail = sum(v["fail"] for kk, v in by_cond.items() if kk.startswith("E1-claim"))
        lines.append("")
        lines.append(
            f"- INV-unit PASS rate: **{inv.get('pass', 0)}/{inv.get('n', 0)}**; "
            f"E1-claim FAIL rate: **{e1_fail}/{e1}** (expect high FAIL)."
        )
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
