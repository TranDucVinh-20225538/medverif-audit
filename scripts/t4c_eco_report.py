#!/usr/bin/env python3
"""T4c: FAIL rates on PI-labeled correct answers (sentence claim), bootstrap CIs + permutation tests."""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

INST = ROOT / "data/t4/eco_instances_t4c.jsonl"
RAW = ROOT / "results/raw/t4c_eco"
T6A_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
OUT_MD = ROOT / "notes/t4c_eco_report.md"
OUT_JSON = ROOT / "notes/t4c_eco_report.json"

OR_VERIFIERS = [
    "v1c_medscore",
    "v1b_medscore",
    "v5_ragas_nli",
    "v4_ragas_nli",
    "v1_medscore",
]
ENCODER_VERIFIERS = ["v2a_minicheck", "v3_alignscore"]
CORRECT_CATS = ("exact_verbatim", "exact_surface_variant", "frequency_rephrased")
CAT_LABEL = {
    "exact_verbatim": "verbatim",
    "exact_surface_variant": "surface_variant",
    "frequency_rephrased": "frequency_rephrased",
}
VERB = "exact_verbatim"


def t6a_verifier_ids() -> list[str]:
    if not T6A_MANIFEST.is_file():
        return []
    data = json.loads(T6A_MANIFEST.read_text())
    return [c["id"] for c in data.get("checkers", [])]


def v6_judge_slugs() -> list[str]:
    return sorted(p.stem for p in RAW.glob("v6_ragas_*.jsonl"))


def all_verifiers() -> list[str]:
    extra = []
    if (RAW / "t6_bespoke_minicheck.jsonl").is_file() or (RAW / "v2b_bespoke.jsonl").is_file():
        extra.append("v2b_bespoke")
    v6 = v6_judge_slugs()
    or_v = [v for v in OR_VERIFIERS if v != "v6_ragas_nli"]
    if (RAW / "v6_ragas_nli.jsonl").is_file() and not v6:
        or_v.insert(1, "v6_ragas_nli")
    return or_v + v6 + ENCODER_VERIFIERS + t6a_verifier_ids() + extra


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def score_path(verifier: str) -> list[Path]:
    manifest = json.loads(T6A_MANIFEST.read_text()) if T6A_MANIFEST.is_file() else {}
    t6a_jsonl = {c["id"]: c["jsonl"] for c in manifest.get("checkers", [])}
    if verifier in t6a_jsonl:
        return [RAW / t6a_jsonl[verifier]]
    if verifier == "v2b_bespoke":
        out = []
        for name in ("v2b_bespoke.jsonl", "t6_bespoke_minicheck.jsonl"):
            p = RAW / name
            if p.is_file():
                out.append(p)
        return out
    if verifier == "v4_ragas_nli":
        llama = RAW / "v4_ragas_nli.llama.jsonl"
        if llama.is_file():
            return [llama]
        return [RAW / "v4_ragas_nli.jsonl"]
    return [RAW / f"{verifier}.jsonl"]


def load_scores(verifiers: list[str]) -> dict[str, dict[str, str]]:
    by_verifier: dict[str, dict[str, str]] = {}
    for v in verifiers:
        m: dict[str, str] = {}
        for path in score_path(v):
            for row in read_jsonl(path):
                iid = row.get("instance_id")
                if iid:
                    m[iid] = row.get("verdict") or ""
        by_verifier[v] = m
    return by_verifier


def bootstrap_fail_rate(
    fails: list[int], n_boot: int = 2000, seed: int = 42
) -> tuple[float, float, float]:
    if not fails:
        return float("nan"), float("nan"), float("nan")
    n = len(fails)
    mean = sum(fails) / n
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        s = sum(rng.choice(fails) for _ in range(n)) / n
        boots.append(s)
    boots.sort()
    lo = boots[int(0.025 * n_boot)]
    hi = boots[int(0.975 * n_boot)]
    return mean, lo, hi


def permutation_p_greater(fails_a: list[int], fails_b: list[int], n_perm: int = 5000, seed: int = 42) -> float:
    """One-sided p: P(mean(B) - mean(A) >= observed | label swap)."""
    if not fails_a or not fails_b:
        return float("nan")
    obs = sum(fails_b) / len(fails_b) - sum(fails_a) / len(fails_a)
    pool = fails_a + fails_b
    na, nb = len(fails_a), len(fails_b)
    rng = random.Random(seed)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        a = pool[:na]
        b = pool[na : na + nb]
        diff = sum(b) / nb - sum(a) / na
        if diff >= obs - 1e-12:
            ge += 1
    return (ge + 1) / (n_perm + 1)


def ci_non_overlap(hi_a: float, lo_b: float) -> bool:
    return lo_b > hi_a


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", type=int, default=2000)
    p.add_argument("--perm", type=int, default=5000)
    args = p.parse_args()

    instances = read_jsonl(INST)
    by_cat: dict[str, list[str]] = defaultdict(list)
    for row in instances:
        cat = row.get("magnitude") or row.get("eco_category_final") or ""
        if cat in CORRECT_CATS:
            by_cat[cat].append(row["instance_id"])

    verifiers = all_verifiers()
    scores = load_scores(verifiers)

    fail_by_v_cat: dict[str, dict[str, list[int]]] = {
        v: defaultdict(list) for v in verifiers
    }
    for cat, iids in by_cat.items():
        for iid in iids:
            for v in verifiers:
                verdict = scores.get(v, {}).get(iid)
                if verdict is None:
                    continue
                fail_by_v_cat[v][cat].append(int(verdict == "FAIL"))

    report_fail: dict = {}
    significance: dict = {}
    for v in verifiers:
        report_fail[v] = {}
        significance[v] = {}
        for cat in CORRECT_CATS:
            xs = fail_by_v_cat[v].get(cat, [])
            if not xs:
                report_fail[v][cat] = {"n": 0, "fail_rate": None, "ci_lo": None, "ci_hi": None}
                continue
            m, lo, hi = bootstrap_fail_rate(xs, n_boot=args.bootstrap)
            report_fail[v][cat] = {"n": len(xs), "fail_rate": m, "ci_lo": lo, "ci_hi": hi}

        verb = report_fail[v].get(VERB, {})
        if verb.get("n", 0) == 0:
            continue
        for alt in ("exact_surface_variant", "frequency_rephrased"):
            alt_cell = report_fail[v].get(alt, {})
            if alt_cell.get("n", 0) == 0:
                continue
            fa = fail_by_v_cat[v][VERB]
            fb = fail_by_v_cat[v][alt]
            pval = permutation_p_greater(fa, fb, n_perm=args.perm)
            non_ov = ci_non_overlap(verb["ci_hi"], alt_cell["ci_lo"])
            sig = non_ov or pval < 0.05
            significance[v][alt] = {
                "vs_verbatim_perm_p": pval,
                "ci_non_overlap": non_ov,
                "significant": sig,
            }

    payload = {
        "n_instances": len(instances),
        "fail_rates_by_verifier_category": report_fail,
        "significance_vs_verbatim": significance,
        "instances": str(INST.relative_to(ROOT)),
        "raw_dir": str(RAW.relative_to(ROOT)),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T4c ecological (sentence-level claim; PI-labeled correct answers)",
        "",
        f"- Instances: **{len(instances)}** (`data/t4/eco_instances_t4c.jsonl`)",
        "- FAIL rate on human-labeled **correct** answers by eco category.",
        "- **Sig** = surface_variant or frequency_rephrased FAIL rate significantly **higher** than verbatim "
        "(non-overlapping 95% CIs and/or one-sided permutation *p* < 0.05).",
        "",
        "## Summary table (all verifiers)",
        "",
        "| verifier | category | n | FAIL rate | 95% CI | sig vs verbatim |",
        "|---|---:|---:|---:|---|:---:|",
    ]
    for v in verifiers:
        for cat in CORRECT_CATS:
            cell = report_fail[v][cat]
            label = CAT_LABEL[cat]
            if cell["n"] == 0:
                lines.append(f"| {v} | {label} | 0 | — | — | |")
                continue
            sig = ""
            if cat != VERB:
                s = significance.get(v, {}).get(cat, {})
                if s.get("significant"):
                    parts = []
                    if s.get("ci_non_overlap"):
                        parts.append("CI")
                    if s.get("vs_verbatim_perm_p", 1) < 0.05:
                        parts.append(f"p={s['vs_verbatim_perm_p']:.3f}")
                    sig = "**Y** (" + ", ".join(parts) + ")"
            lines.append(
                f"| {v} | {label} | {cell['n']} | {cell['fail_rate']:.3f} | "
                f"[{cell['ci_lo']:.3f}, {cell['ci_hi']:.3f}] | {sig} |"
            )

    lines.append("")
    lines.append("## By verifier (detail)")
    lines.append("")
    for v in verifiers:
        if not any(report_fail[v][c]["n"] > 0 for c in CORRECT_CATS):
            continue
        lines.append(f"### {v}")
        lines.append("| category | n | FAIL rate | 95% CI | sig vs verbatim |")
        lines.append("|---|---:|---:|---|:---:|")
        for cat in CORRECT_CATS:
            cell = report_fail[v][cat]
            label = CAT_LABEL[cat]
            sig = ""
            if cat != VERB:
                s = significance.get(v, {}).get(cat, {})
                if s.get("significant"):
                    sig = "Y"
            if cell["n"] == 0:
                lines.append(f"| {label} | 0 | — | — | |")
            else:
                lines.append(
                    f"| {label} | {cell['n']} | {cell['fail_rate']:.3f} | "
                    f"[{cell['ci_lo']:.3f}, {cell['ci_hi']:.3f}] | {sig} |"
                )
        lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
