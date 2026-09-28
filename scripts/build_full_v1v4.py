#!/usr/bin/env python3
"""Full four-verifier report (V1–V4) with human review filters. Requires V1+V4 complete."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import (  # noqa: E402
    _c0_pass_bases,
    _parsed,
    kappa_matrix,
    load_joined_from_records,
    read_jsonl,
    run as analyze_run,
)
from review_filters import (  # noqa: E402
    analysis_keep_row,
    flip_pi_ok_bases,
    flip_pi_ok_counts,
    unit_natural_y_bases,
)

MAIN = ROOT / "data" / "v3" / "instances_main.jsonl"
THR = ROOT / "data" / "v3" / "instances_threshold.jsonl"
VERDICTS = ROOT / "results" / "raw"
OUT = ROOT / "results" / "tables" / "full_v1v4.md"
FULL_VERIFIERS = ("v1_medscore", "v2a_minicheck", "v3_alignscore", "v4_ragas_nli")


def valid_instance_rows() -> list[dict]:
    rows = []
    for path in (MAIN, THR):
        rows.extend(r for r in read_jsonl(path) if r.get("valid", True))
    return rows


def scored_ids(name: str) -> set[str]:
    path = VERDICTS / f"{name}.jsonl"
    if not path.exists():
        return set()
    return {json.loads(line)["instance_id"] for line in path.open() if line.strip()}


def target_n() -> int:
    return len(valid_instance_rows())


def parse_fail_rate(joined: list[dict], verifier: str) -> tuple[int, int]:
    block = [r for r in joined if r["verifier"] == verifier]
    n = len(block)
    pf = sum(r["verdict"] == "PARSE_FAIL" for r in block)
    return pf, n


def headline_pass_table(joined: list[dict]) -> list[str]:
    """DOSE main headline; POLARITY human flip_ok Y (26) secondary."""
    flip_y = flip_pi_ok_bases()
    lines = [
        "## Headline pass @ 0.5 (conditional on C0 PASS)",
        "",
        "**DOSE (main analysis set)** — all valid main/threshold DOSE instances.",
        "",
        "| Verifier | C0 | E1-claim | INV-unit (all valid) | INV-unit (natural=Y) |",
        "| --- | --- | --- | --- | --- |",
    ]
    nat_y = unit_natural_y_bases()
    for verifier in FULL_VERIFIERS:
        block = [r for r in joined if r["verifier"] == verifier and r["type"] == "DOSE"]
        cond = _c0_pass_bases(block)

        def rate(pred) -> str:
            parsed = [r for r in block if pred(r) and r["base_id"] in cond and _parsed(r)]
            if not parsed:
                return "—"
            return f"{sum(r['verdict']=='PASS' for r in parsed)}/{len(parsed)}"

        lines.append(
            f"| {verifier} | {rate(lambda r: r['condition']=='C0')} | "
            f"{rate(lambda r: r['condition']=='E1-claim')} | "
            f"{rate(lambda r: r['condition']=='INV-claim' and r.get('magnitude')=='unit_conversion')} | "
            f"{rate(lambda r: r['condition']=='INV-claim' and r.get('magnitude')=='unit_conversion' and r['base_id'] in nat_y)} |"
        )
    lines += [
        "",
        f"**POLARITY (human-verified flips, n={len(flip_y)})** — E1/E2 rows only for "
        "`qc/e1_pol_review.csv` PI_ok=Y; C0/INV on other POL bases may still appear in C0-only slices.",
        "",
        "| Verifier | C0 (all valid POL main) | E1-claim (flip_ok Y only) | INV (PI_ok=Y) |",
        "| --- | --- | --- | --- |",
    ]
    for verifier in FULL_VERIFIERS:
        pol = [r for r in joined if r["verifier"] == verifier and r["type"] == "POLARITY"]
        cond = _c0_pass_bases(pol)

        def rate_pol(pred) -> str:
            parsed = [r for r in pol if pred(r) and _parsed(r)]
            if not parsed:
                return "—"
            return f"{sum(r['verdict']=='PASS' for r in parsed)}/{len(parsed)}"

        lines.append(
            f"| {verifier} | {rate_pol(lambda r: r['condition']=='C0' and r['base_id'] in cond)} | "
            f"{rate_pol(lambda r: r['condition']=='E1-claim' and r['base_id'] in flip_y)} | "
            f"{rate_pol(lambda r: r['condition']=='INV-claim')} |"
        )
    return lines


def write_report(joined: list[dict], *, complete: bool) -> None:
    flip = flip_pi_ok_counts()
    v1_agree = ROOT / "notes" / "v1_agreement_50x2.json"
    agree_line = ""
    if v1_agree.exists():
        agree = json.loads(v1_agree.read_text())
        agree_line = f"V1 agreement (50×2): **{agree.get('agreement_rate')}** ({agree.get('verifier')}).\n\n"
    pf_lines = ["| Verifier | PARSE_FAIL | n |", "| --- | --- | --- |"]
    for v in FULL_VERIFIERS:
        pf, n = parse_fail_rate(joined, v)
        pf_lines.append(f"| {v} | {pf}/{n} | {n} |")
    kappa = kappa_matrix(joined)
    k_lines = ["|  | " + " | ".join(FULL_VERIFIERS) + " |", "| --- | " + " | ".join(["---"] * len(FULL_VERIFIERS)) + " |"]
    for left in FULL_VERIFIERS:
        cells = []
        for right in FULL_VERIFIERS:
            match = next((r for r in kappa if r["left"] == left and r["right"] == right), None)
            val = match["kappa"] if match and match.get("kappa") is not None else None
            cells.append(f"{val:.3f}" if isinstance(val, float) else "—")
        k_lines.append(f"| {left} | " + " | ".join(cells) + " |")

    lines = [
        "# Full V1–V4 analysis",
        "",
        f"Status: {'**complete**' if complete else '**partial** (V1/V4 still scoring)'}",
        "",
        "Filters: `valid=true`; conditional rates use C0 PASS; **POL E1/E2** use "
        f"flip PI_ok=Y (**{flip['Y']}** bases); **INV** uses `qc/inv_manual_review.csv` PI_ok=Y "
        "(DOSE unit always eligible); INV-unit **natural=Y** subset from `qc/unit_naturalness.csv`.",
        "",
        agree_line + "## Parse-fail rate",
        "",
        *pf_lines,
        "",
        "## Cohen's κ (verifier × verifier, parsed PASS/FAIL/PARSE_FAIL)",
        "",
        *k_lines,
        "",
        *headline_pass_table(joined),
        "",
    ]
    if not complete:
        lines += [
            "## Pending",
            "",
            "Re-run after `v1_medscore` and `v4_ragas_nli` each cover all valid main+threshold instances.",
            "",
        ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    target = target_n()
    v1n = len(scored_ids("v1_medscore"))
    v4n = len(scored_ids("v4_ragas_nli"))
    complete = v1n >= target and v4n >= target
    instances = valid_instance_rows()
    joined = load_joined_from_records(instances, VERDICTS)
    joined = [r for r in joined if r["verifier"] in FULL_VERIFIERS and analysis_keep_row(r)]
    write_report(joined, complete=complete)
    if complete:
        union = ROOT / "data" / "v3" / "instances_main_threshold_valid.jsonl"
        with union.open("w", encoding="utf-8") as handle:
            for row in instances:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        analyze_run(union, VERDICTS, ROOT / "results", stamp="full_v1v4")
    print(
        json.dumps(
            {
                "target_instances": target,
                "v1_scored": v1n,
                "v4_scored": v4n,
                "complete": complete,
                "joined_after_filters": len(joined),
                "report": str(OUT),
                "flip_pi_ok_Y": len(flip_pi_ok_bases()),
            },
            indent=2,
        )
    )
    if not complete:
        sys.exit(0)


if __name__ == "__main__":
    main()
