#!/usr/bin/env python3
"""DOSE robustness across all headline verifiers + weak-contrast breakdown."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _c0_pass_bases, read_jsonl  # noqa: E402
from review_filters import analysis_keep_row  # noqa: E402

INST = ROOT / "data/v3/instances_cpu_early.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
T6A_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
OUT = ROOT / "results/tables/dose3_robustness_diff.md"
META = ROOT / "notes/dose3_robustness_diff.json"
WEAK_OUT = ROOT / "notes/dose3_weak_contrast_breakdown.json"

SCORE_DIRS = [
    ROOT / "results/raw/e2_main",
    ROOT / "results/raw",
    ROOT / "results/raw/t6b/full",
    ROOT / "results/raw/t2_full",
    ROOT / "results/raw/t7",
    ROOT / "results/raw/t3",
    ROOT / "results/raw_m1",
    ROOT / "results/raw_m1/t7",
]

VERIFIERS: list[tuple[str, str]] = [
    ("v1_medscore", "V1"),
    ("v4_ragas_nli", "V4"),
    ("v1b_medscore", "V1b"),
    ("v5_ragas_nli", "V5"),
    ("v2a_minicheck", "V2a"),
    ("v3_alignscore", "V3"),
    ("v2b_bespoke", "Bespoke"),
    ("v6_ragas_gpt4o_mini", "T6B gpt4o-mini"),
    ("v6_ragas_haiku45", "T6B haiku4.5"),
    ("v6_ragas_llama31_8b", "T6B llama3.1-8b"),
    ("v6_ragas_mistral_small32", "T6B mistral3.2-24b"),
]


def load_t6a_verifiers() -> list[tuple[str, str]]:
    if not T6A_MANIFEST.is_file():
        return []
    data = json.loads(T6A_MANIFEST.read_text())
    return [(c["id"], f"T6A {c['label']}") for c in data.get("checkers", [])]


def merged_verdicts(slug: str) -> dict[str, str]:
    paths: list[Path] = []
    if T6A_MANIFEST.is_file():
        t6a = {c["id"]: c["jsonl"] for c in json.loads(T6A_MANIFEST.read_text()).get("checkers", [])}
        if slug in t6a:
            for d in SCORE_DIRS:
                cand = d / t6a[slug]
                if cand.is_file():
                    paths.append(cand)
    if slug == "v2b_bespoke":
        for name in ("t6_bespoke_minicheck.jsonl", "v2b_bespoke.jsonl"):
            for d in SCORE_DIRS:
                cand = d / name
                if cand.is_file():
                    paths.append(cand)
    for d in SCORE_DIRS:
        llama = d / f"{slug}.llama.jsonl"
        plain = d / f"{slug}.jsonl"
        if llama.is_file():
            paths.append(llama)
        elif plain.is_file():
            paths.append(plain)
    out: dict[str, str] = {}
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        for row in read_jsonl(path):
            iid = row.get("instance_id")
            if iid:
                out[iid] = row.get("verdict") or ""
    return out


def filter_main(rows: list[dict], mode: str) -> tuple[list[dict], set[str]]:
    """Return filtered DOSE main rows and allowed base_ids."""
    bases: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if not r.get("valid", True) or r.get("type") != "DOSE":
            continue
        if not analysis_keep_row(r):
            continue
        bid = r["base_id"]
        if mode == "no_underspec" and r.get("c0_underspecified"):
            continue
        if mode == "no_weak" and r.get("weak_e1_contrast"):
            continue
        out.append(r)
        bases.add(bid)
    return out, bases


def c0_pass_bases_for(instances: list[dict], scores: dict[str, str], slug: str) -> set[str]:
    joined = []
    for r in instances:
        if r.get("condition") != "C0":
            continue
        v = scores.get(r["instance_id"])
        if v and v != "PARSE_FAIL":
            row = dict(r)
            row["verifier"] = slug
            row["verdict"] = v
            joined.append(row)
    return _c0_pass_bases(joined)


def rate_fail(
    ids: list[str], scores: dict[str, str], c0_bases: set[str], iid_base: dict[str, str]
) -> tuple[float | None, int, int]:
    hits = []
    for iid in ids:
        bid = iid_base.get(iid)
        if bid not in c0_bases:
            continue
        v = scores.get(iid)
        if v and v != "PARSE_FAIL":
            hits.append(int(v == "FAIL"))
    if not hits:
        return None, 0, 0
    return sum(hits) / len(hits), sum(hits), len(hits)


def rate_pass(
    ids: list[str], scores: dict[str, str], c0_bases: set[str], iid_base: dict[str, str]
) -> tuple[float | None, int, int]:
    hits = []
    for iid in ids:
        bid = iid_base.get(iid)
        if bid not in c0_bases:
            continue
        v = scores.get(iid)
        if v and v != "PARSE_FAIL":
            hits.append(int(v == "PASS"))
    if not hits:
        return None, 0, 0
    return sum(hits) / len(hits), sum(hits), len(hits)


def weak_contrast_breakdown(all_rows: list[dict]) -> dict:
    reason_counts: Counter = Counter()
    combo_counts: Counter = Counter()
    sole_counts: Counter = Counter()
    instance_rows = 0
    bases: set[str] = set()
    for r in all_rows:
        if not r.get("weak_e1_contrast"):
            continue
        if r.get("type") != "DOSE" or not r.get("valid", True):
            continue
        instance_rows += 1
        bases.add(r["base_id"])
        reasons = tuple(sorted(r.get("weak_e1_contrast_reasons") or []))
        if reasons:
            combo_counts["+".join(reasons)] += 1
            if len(reasons) == 1:
                sole_counts[reasons[0]] += 1
        for reason in reasons:
            reason_counts[reason] += 1
    return {
        "weak_e1_contrast_instances": instance_rows,
        "weak_e1_contrast_bases": len(bases),
        "reason_tag_counts": dict(reason_counts),
        "sole_reason_instance_counts": dict(sole_counts),
        "reason_combo_counts": dict(combo_counts),
        "note": "Tags are not mutually exclusive (one row can have multiple reasons).",
    }


def collect_mode(main_rows: list[dict], bases: set[str], t7_rows: list[dict], slug: str) -> dict:
    scores = merged_verdicts(slug)
    if not scores:
        return {"scored": False}
    iid_base = {r["instance_id"]: r["base_id"] for r in main_rows + t7_rows}
    c0_bases = c0_pass_bases_for(main_rows, scores, slug)

    inv_ids = [
        r["instance_id"]
        for r in main_rows
        if r["base_id"] in bases
        and r["condition"] == "INV-claim"
        and r.get("magnitude") == "unit_conversion"
    ]
    e1_x2 = [
        r["instance_id"]
        for r in main_rows
        if r["base_id"] in bases
        and r["condition"] == "E1-claim"
        and r.get("magnitude") == "x2"
    ]
    e1_x10 = [
        r["instance_id"]
        for r in main_rows
        if r["base_id"] in bases
        and r["condition"] == "E1-claim"
        and r.get("magnitude") == "x10"
    ]
    t7_claim = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-claim" and r["base_id"] in bases]
    t7_evid = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-evid" and r["base_id"] in bases]

    inv = rate_pass(inv_ids, scores, c0_bases, iid_base)
    x2 = rate_fail(e1_x2, scores, c0_bases, iid_base)
    x10 = rate_fail(e1_x10, scores, c0_bases, iid_base)
    u_c = rate_fail(t7_claim, scores, c0_bases, iid_base)
    u_e = rate_fail(t7_evid, scores, c0_bases, iid_base)
    return {
        "scored": True,
        "inv_unit_pass": inv[0],
        "inv_n": inv[2],
        "e1_x2_fail": x2[0],
        "e1_x2_n": x2[2],
        "e1_x10_fail": x10[0],
        "e1_x10_n": x10[2],
        "t7_unit_claim_fail": u_c[0],
        "t7_unit_claim_n": u_c[2],
        "t7_unit_evid_fail": u_e[0],
        "t7_unit_evid_n": u_e[2],
    }


def pct(x: float | None, n: int) -> str:
    if n <= 0:
        return "—"
    return "NA" if x is None else f"{100 * x:.1f}%"


def main() -> None:
    all_main = read_jsonl(INST)
    weak = weak_contrast_breakdown(all_main)
    WEAK_OUT.write_text(json.dumps(weak, indent=2) + "\n")

    t7_all = read_jsonl(T7)
    verifiers = VERIFIERS + load_t6a_verifiers()

    modes = {
        "all_valid": "all",
        "excl_weak_e1": "no_weak",
        "excl_c0_underspec": "no_underspec",
    }
    results: dict = {}
    for mode_name, mode_key in modes.items():
        main_filt, bases = filter_main(all_main, mode_key)
        t7_filt = [r for r in t7_all if r.get("valid", True) and r["base_id"] in bases]
        results[mode_name] = {}
        for slug, label in verifiers:
            results[mode_name][slug] = {"label": label, **collect_mode(main_filt, bases, t7_filt, slug)}

    shifts = []
    base = results["all_valid"]
    metrics = (
        "inv_unit_pass",
        "e1_x2_fail",
        "e1_x10_fail",
        "t7_unit_claim_fail",
        "t7_unit_evid_fail",
    )
    for mode in ("excl_weak_e1", "excl_c0_underspec"):
        cur = results[mode]
        for slug, _label in verifiers:
            if not base.get(slug, {}).get("scored"):
                continue
            for key in metrics:
                a, b = base[slug].get(key), cur[slug].get(key)
                if a is None or b is None:
                    continue
                d = 100 * (b - a)
                if abs(d) > 3.0:
                    shifts.append(
                        {
                            "verifier": slug,
                            "metric": key,
                            "subset": mode,
                            "all_pct": round(100 * a, 2),
                            "subset_pct": round(100 * b, 2),
                            "delta_pp": round(d, 2),
                        }
                    )

    lines = [
        "# DOSE robustness (dose3 audit) — all headline verifiers",
        "",
        "Subsets: **(a)** all valid DOSE main; **(b)** drop `weak_e1_contrast` E1 rows; "
        "**(c)** drop `c0_underspecified` bases. Conditional rates use **C0 PASS** per verifier.",
        "",
        f"Scores merged from `results/raw/**` (+ t2_full, t6b/full, t7, raw_m1). "
        f"V4 audit: see `notes/openrouter_model_audit.md`.",
        "",
        "## Weak-contrast flags (main DOSE, rule-based)",
        "",
        f"- Instances flagged: **{weak['weak_e1_contrast_instances']}** ({weak['weak_e1_contrast_bases']} bases).",
        f"- By reason tag (non-exclusive): **threshold_context** {weak['reason_tag_counts'].get('threshold_context', 0)}, "
        f"**pk_descriptive** {weak['reason_tag_counts'].get('pk_descriptive', 0)}, "
        f"**within_evidence_range** {weak['reason_tag_counts'].get('within_evidence_range', 0)}.",
        f"- Sole reason only: threshold {weak['sole_reason_instance_counts'].get('threshold_context', 0)}, "
        f"PK-descriptive {weak['sole_reason_instance_counts'].get('pk_descriptive', 0)}, "
        f"within-range {weak['sole_reason_instance_counts'].get('within_evidence_range', 0)}.",
        f"- Top combos: "
        + ", ".join(f"`{k}` {v}" for k, v in sorted(weak["reason_combo_counts"].items(), key=lambda x: -x[1])[:5])
        + f" (full list `{WEAK_OUT.relative_to(ROOT)}`).",
        "",
    ]

    for mode_name, title in (
        ("all_valid", "(a) all valid"),
        ("excl_weak_e1", "(b) excl weak E1"),
        ("excl_c0_underspec", "(c) excl C0 underspec"),
    ):
        lines += [
            f"## {title}",
            "",
            "| Verifier | INV-unit PASS | E1-claim x2 FAIL | E1-claim x10 FAIL | T7 unit-claim FAIL | T7 unit-evid FAIL | n(inv) |",
            "| --- | --- | --- | --- | --- | --- | ---: |",
        ]
        for slug, label in verifiers:
            m = results[mode_name].get(slug, {})
            if not m.get("scored"):
                lines.append(f"| {label} | — | — | — | — | — | 0 |")
                continue
            inv_n = m.get("inv_n", 0)
            lines.append(
                f"| {label} | {pct(m.get('inv_unit_pass'), inv_n)} | "
                f"{pct(m.get('e1_x2_fail'), m.get('e1_x2_n', 0))} | "
                f"{pct(m.get('e1_x10_fail'), m.get('e1_x10_n', 0))} | "
                f"{pct(m.get('t7_unit_claim_fail'), m.get('t7_unit_claim_n', 0))} | "
                f"{pct(m.get('t7_unit_evid_fail'), m.get('t7_unit_evid_n', 0))} | {inv_n} |"
            )
        lines.append("")

    lines += [
        "**T6-A (7 encoders):** main-pack INV / E1 cells use `results/raw/t4_eco/t6_*.jsonl` (0 overlap with main); "
        "T7 unit columns merge `results/raw/t7/t6_*.jsonl` when present.",
        "",
        "## Shifts > 3 pp vs (a)",
        "",
    ]
    if not shifts:
        lines.append("**None** on listed metrics.")
    else:
        lines.append("| Verifier | Metric | Subset | (a) | subset | Δ pp |")
        lines.append("| --- | --- | --- | ---: | ---: | ---: |")
        for s in sorted(shifts, key=lambda x: (-abs(x["delta_pp"]), x["verifier"])):
            lines.append(
                f"| {s['verifier']} | {s['metric']} | {s['subset']} | {s['all_pct']}% | "
                f"{s['subset_pct']}% | {s['delta_pp']:+.2f} |"
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    META.write_text(json.dumps({"weak": weak, "results": results, "shifts_gt_3pp": shifts}, indent=2) + "\n")
    print(OUT)
    print(json.dumps({"weak_instances": weak["weak_e1_contrast_instances"], "shifts": len(shifts)}, indent=2))


if __name__ == "__main__":
    main()
