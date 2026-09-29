#!/usr/bin/env python3
"""T4c: FAIL rates on PI-labeled correct answers (sentence claim), bootstrap CIs."""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t4_eco_compare import apply_pi_override, load_pi_label_paths  # noqa: E402

INST = ROOT / "data/t4/eco_instances_t4c.jsonl"
DEV_LABELS = ROOT / "qc/eco_PI_ok_labels.csv"
HELD_LABELS = ROOT / "qc/eco2_PI_ok_labels.csv"
RAW = ROOT / "results/raw/t4c_eco"
T6A_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
OUT_MD = ROOT / "notes/t4c_eco_report.md"
OUT_JSON = ROOT / "notes/t4c_eco_report.json"

OR_VERIFIERS = [
    "v1c_medscore",
    "v6_ragas_nli",
    "v1b_medscore",
    "v5_ragas_nli",
    "v4_ragas_nli",
    "v1_medscore",
]
ENCODER_VERIFIERS = ["v2a_minicheck", "v3_alignscore"]
CORRECT_CATS = frozenset(
    {"exact_verbatim", "exact_surface_variant", "frequency_rephrased"}
)


def t6a_verifier_ids() -> list[str]:
    if not T6A_MANIFEST.is_file():
        return []
    data = json.loads(T6A_MANIFEST.read_text())
    return [c["id"] for c in data.get("checkers", [])]


def all_verifiers() -> list[str]:
    extra = []
    if (RAW / "t6_bespoke_minicheck.jsonl").is_file() or (RAW / "v2b_bespoke.jsonl").is_file():
        extra.append("v2b_bespoke")
    return OR_VERIFIERS + ENCODER_VERIFIERS + t6a_verifier_ids() + extra


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def load_scores(verifiers: list[str]) -> dict[str, dict[str, str]]:
    manifest = json.loads(T6A_MANIFEST.read_text()) if T6A_MANIFEST.is_file() else {}
    t6a_jsonl = {c["id"]: c["jsonl"] for c in manifest.get("checkers", [])}
    aliases = {
        "v2b_bespoke": ["v2b_bespoke.jsonl", "t6_bespoke_minicheck.jsonl"],
    }
    by_verifier: dict[str, dict[str, str]] = {}
    for v in verifiers:
        names = [t6a_jsonl.get(v, f"{v}.jsonl")]
        if v in aliases:
            names = aliases[v]
        m: dict[str, str] = {}
        for fname in names:
            path = RAW / fname
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


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", type=int, default=2000)
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

    report_fail = {}
    for v in verifiers:
        report_fail[v] = {}
        for cat in sorted(CORRECT_CATS):
            xs = fail_by_v_cat[v].get(cat, [])
            if not xs:
                report_fail[v][cat] = {
                    "n": 0,
                    "fail_rate": None,
                    "ci_lo": None,
                    "ci_hi": None,
                }
                continue
            m, lo, hi = bootstrap_fail_rate(xs, n_boot=args.bootstrap)
            report_fail[v][cat] = {
                "n": len(xs),
                "fail_rate": m,
                "ci_lo": lo,
                "ci_hi": hi,
            }

    payload = {
        "n_instances": len(instances),
        "fail_rates_by_verifier_category": report_fail,
        "instances": str(INST.relative_to(ROOT)),
        "raw_dir": str(RAW.relative_to(ROOT)),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T4c ecological (sentence-level claim; PI-labeled correct answers)",
        "",
        f"- Instances: **{len(instances)}** (`data/t4/eco_instances_t4c.jsonl`)",
        "- Claim = rule-based sentence(s) with target dose (+ next-sentence frequency if needed); evidence unchanged.",
        "",
        "## FAIL rate on correct answers (bootstrap 95% CI)",
        "",
    ]
    for v in verifiers:
        present = any(
            report_fail[v][c]["n"] > 0 for c in CORRECT_CATS if c in report_fail[v]
        )
        if not present:
            lines.append(f"### {v} (no scores yet)")
            lines.append("")
            continue
        lines.append(f"### {v}")
        lines.append("| category | n | FAIL rate | 95% CI |")
        lines.append("|---|---:|---:|---|")
        for cat in sorted(CORRECT_CATS):
            cell = report_fail[v][cat]
            if cell["n"] == 0:
                lines.append(f"| {cat} | 0 | — | — |")
            else:
                lines.append(
                    f"| {cat} | {cell['n']} | {cell['fail_rate']:.3f} | "
                    f"[{cell['ci_lo']:.3f}, {cell['ci_hi']:.3f}] |"
                )
        lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
