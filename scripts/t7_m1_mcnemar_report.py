#!/usr/bin/env python3
"""T7 E1-unit FAIL rate |C0 PASS|: raw (before M1) vs raw_m1/t7 (after M1) + McNemar."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _c0_pass_bases  # noqa: E402
from t7_e1_unit_report import (  # noqa: E402
    CONDITIONAL_LLM,
    EXPAND,
    MAIN,
    T7,
    merged_scores,
    read_jsonl,
)

RAW_M1_T7 = ROOT / "results/raw_m1/t7"
OUT_MD = ROOT / "results/tables/t7_m1_mcnemar.md"
OUT_JSON = ROOT / "notes/t7_m1_mcnemar.json"

FOCUS = ("v2a_minicheck", "v3_alignscore", "v1_medscore", "v4_ragas_nli")


def mcnemar(b: int, c: int) -> tuple[float | None, float | None]:
    if b + c == 0:
        return None, None
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    p = math.erfc(math.sqrt(stat / 2))
    return stat, p


def load_m1_scores(slug: str) -> dict[str, str]:
    path = RAW_M1_T7 / f"{slug}.jsonl"
    m: dict[str, str] = {}
    for row in read_jsonl(path):
        iid = row.get("instance_id")
        if iid:
            m[iid] = row.get("verdict") or ""
    return m


def c0_pass_bases_for(t7_bases: set[str], c0_ref: list[dict], sc: dict[str, str], verifier: str) -> set[str]:
    joined = []
    for r in c0_ref:
        if r["base_id"] not in t7_bases:
            continue
        v = sc.get(r["instance_id"])
        if not v:
            continue
        row = dict(r)
        row["verifier"] = verifier
        row["verdict"] = v
        joined.append(row)
    return _c0_pass_bases(joined)


def paired_slice(
    ids: list[str],
    iid_base: dict[str, str],
    c0_pass: set[str],
    raw_sc: dict[str, str],
    m1_sc: dict[str, str],
) -> dict:
    b = c = n = 0
    fail_before = fail_after = 0
    for iid in ids:
        bid = iid_base.get(iid)
        if bid not in c0_pass:
            continue
        v0, v1 = raw_sc.get(iid), m1_sc.get(iid)
        if not v0 or not v1 or v0 == "PARSE_FAIL" or v1 == "PARSE_FAIL":
            continue
        n += 1
        f0, f1 = v0 == "FAIL", v1 == "FAIL"
        fail_before += int(f0)
        fail_after += int(f1)
        if not f0 and f1:
            b += 1
        elif f0 and not f1:
            c += 1
    stat, p = mcnemar(b, c)
    return {
        "n_paired": n,
        "fail_before": fail_before,
        "fail_after": fail_after,
        "fail_rate_before": fail_before / n if n else None,
        "fail_rate_after": fail_after / n if n else None,
        "discordant_pass_fail": b,
        "discordant_fail_pass": c,
        "mcnemar_chi2": stat,
        "mcnemar_p_approx": p,
    }


def fmt_fail(sl: dict, key: str) -> str:
    rate = sl[f"fail_rate_{key}"]
    count = sl[f"fail_{key}"]
    return f"{count} ({rate:.3f})" if rate is not None else "—"


def main() -> None:
    t7_rows = read_jsonl(T7)
    t7_bases = {r["base_id"] for r in t7_rows}
    claim_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-claim"]
    evid_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-evid"]
    iid_base = {r["instance_id"]: r["base_id"] for r in t7_rows}

    ref_rows = read_jsonl(MAIN) + read_jsonl(EXPAND)
    c0_ref = [
        r
        for r in ref_rows
        if r.get("valid", True) and r["base_id"] in t7_bases and r.get("condition") == "C0"
    ]

    report: dict = {"verifiers": {}, "n_claim": len(claim_ids), "n_evid": len(evid_ids)}
    lines = [
        "# T7 M1: E1-unit FAIL |C0 PASS| (before vs after M1)",
        "",
        f"- Cohort: **{len(claim_ids)}** E1-unit-claim + **{len(evid_ids)}** E1-unit-evid ({len(t7_bases)} bases)",
        "- **Before:** merged scores (`results/raw/t7` + main for V1/V4)",
        "- **After:** `results/raw_m1/t7`",
        "",
        "| Verifier | Dir | n | FAIL before | FAIL after | McNemar b/c | p≈ |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for v in FOCUS:
        raw_sc = merged_scores(v)
        m1_sc = load_m1_scores(v)
        # Gate cohort on C0 PASS under raw (pre-M1) scores; paired where M1 scores exist.
        c0_pass = c0_pass_bases_for(t7_bases, c0_ref, raw_sc, v)
        vrep: dict = {"c0_pass_bases": len(c0_pass)}
        for label, ids in (("E1-unit-claim", claim_ids), ("E1-unit-evid", evid_ids)):
            sl = paired_slice(ids, iid_base, c0_pass, raw_sc, m1_sc)
            vrep[label] = sl
            p_s = f"{sl['mcnemar_p_approx']:.4g}" if sl["mcnemar_p_approx"] is not None else "—"
            lines.append(
                f"| {v} | {label} | {sl['n_paired']} | {fmt_fail(sl, 'before')} | {fmt_fail(sl, 'after')} | "
                f"{sl['discordant_pass_fail']}/{sl['discordant_fail_pass']} | {p_s} |"
            )
        report["verifiers"][v] = vrep

    lines.extend(
        [
            "",
            "### LLM judges (V1, V4)",
            "",
            "| Verifier | Dir | n | FAIL before | FAIL after | b/c | p≈ |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for v in CONDITIONAL_LLM:
        if v not in report["verifiers"]:
            continue
        for label in ("E1-unit-claim", "E1-unit-evid"):
            sl = report["verifiers"][v][label]
            p_s = f"{sl['mcnemar_p_approx']:.4g}" if sl["mcnemar_p_approx"] is not None else "—"
            lines.append(
                f"| {v} | {label} | {sl['n_paired']} | {fmt_fail(sl, 'before')} | {fmt_fail(sl, 'after')} | "
                f"{sl['discordant_pass_fail']}/{sl['discordant_fail_pass']} | {p_s} |"
            )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
