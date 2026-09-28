#!/usr/bin/env python3
"""T4 eco: category distribution + verifier false-alarm rates (bootstrap CIs)."""

from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t4_eco_compare import (  # noqa: E402
    collapse_exact,
    gold_from_pi_row,
    load_pi_label_paths,
    load_pi_sheet_keys,
)

CLASSIFIED = ROOT / "data/t4/eco_classified.jsonl"
DEV_LABELS = ROOT / "qc/eco_PI_ok_labels.csv"
REVIEW2 = ROOT / "qc/eco_review2.csv"
RAW = ROOT / "results/raw/t4_eco"
T6A_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"
OUT_MD = ROOT / "notes/t4_eco_report.md"
OUT_JSON = ROOT / "notes/t4_eco_report.json"

EXCLUDE = {
    ("D0122__eco", "deepseek_chat"),
    ("D0077__eco", "command_r"),
}

CORRECT_CATS = frozenset(
    {"exact_verbatim", "exact_surface_variant", "frequency_rephrased"}
)

OR_VERIFIERS = [
    "v1c_medscore",
    "v6_ragas_nli",
    "v1b_medscore",
    "v5_ragas_nli",
    "v4_ragas_nli",
    "v1_medscore",
]
ENCODER_VERIFIERS = ["v2a_minicheck", "v3_alignscore"]


def t6a_verifier_ids() -> list[str]:
    if not T6A_MANIFEST.is_file():
        return []
    data = json.loads(T6A_MANIFEST.read_text())
    return [c["id"] for c in data.get("checkers", [])]


def all_verifiers() -> list[str]:
    return OR_VERIFIERS + ENCODER_VERIFIERS + t6a_verifier_ids()


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def instance_key(row: dict) -> tuple[str, str]:
    return (row["task_id"], row["answerer_id"])


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


def load_scores(verifiers: list[str]) -> dict[str, dict[str, str]]:
    by_verifier: dict[str, dict[str, str]] = {}
    t6a_ids = set(t6a_verifier_ids())
    manifest = json.loads(T6A_MANIFEST.read_text()) if T6A_MANIFEST.is_file() else {}
    t6a_jsonl = {c["id"]: c["jsonl"] for c in manifest.get("checkers", [])}
    for v in verifiers:
        fname = t6a_jsonl.get(v, f"{v}.jsonl")
        path = RAW / fname
        m: dict[str, str] = {}
        for row in read_jsonl(path):
            iid = row.get("instance_id")
            if iid:
                m[iid] = row.get("verdict") or ""
        by_verifier[v] = m
    return by_verifier


def classifier_vs_gold(rows: list[dict], labels: dict) -> list[int]:
    hits = []
    for key, lab in labels.items():
        row = next((r for r in rows if instance_key(r) == key), None)
        if not row:
            continue
        pred = collapse_exact(row.get("eco_category") or "")
        gold = gold_from_pi_row(lab)
        hits.append(int(pred == gold))
    return hits


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--classified", type=Path, default=CLASSIFIED)
    p.add_argument("--bootstrap", type=int, default=2000)
    args = p.parse_args()

    rows = read_jsonl(args.classified)
    dev_keys = load_pi_sheet_keys(DEV_LABELS)
    review2_keys = load_pi_sheet_keys(REVIEW2)
    dev_labels = load_pi_label_paths([DEV_LABELS])
    review2_labels = load_pi_label_paths([REVIEW2])
    held_out_labels = {
        k: v for k, v in review2_labels.items() if k in review2_keys and k not in dev_keys
    }

    verifiers = all_verifiers()
    scores = load_scores(verifiers)

    dist_all = Counter(r.get("eco_category_final") or r.get("eco_category") for r in rows)
    by_answerer: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_answerer[r["answerer_id"]][
            r.get("eco_category_final") or r.get("eco_category")
        ] += 1

    dev_fit = classifier_vs_gold(rows, dev_labels)
    dev_fit_rate = sum(dev_fit) / len(dev_fit) if dev_fit else float("nan")
    held_acc = classifier_vs_gold(rows, held_out_labels)
    held_rate = sum(held_acc) / len(held_acc) if held_acc else float("nan")

    analysis_rows = []
    for r in rows:
        key = instance_key(r)
        if key in EXCLUDE:
            continue
        cat = r.get("eco_category_final") or r.get("eco_category")
        if cat not in CORRECT_CATS:
            continue
        iid = f"{r['task_id']}__{r['answerer_id']}__eco"
        analysis_rows.append((cat, iid))

    fail_by_v_cat: dict[str, dict[str, list[int]]] = {
        v: defaultdict(list) for v in verifiers
    }
    for cat, iid in analysis_rows:
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

    changed_rows = []
    for r in rows:
        key = instance_key(r)
        if key in EXCLUDE:
            continue
        cat = r.get("eco_category_final") or r.get("eco_category")
        if cat != "changed_value":
            continue
        iid = f"{r['task_id']}__{r['answerer_id']}__eco"
        changed_rows.append(iid)

    sens_by_v: dict[str, dict] = {}
    for v in verifiers:
        xs = []
        for iid in changed_rows:
            verdict = scores.get(v, {}).get(iid)
            if verdict is None:
                continue
            xs.append(int(verdict == "FAIL"))
        if not xs:
            sens_by_v[v] = {"n": 0, "fail_rate": None, "ci_lo": None, "ci_hi": None}
        else:
            m, lo, hi = bootstrap_fail_rate(xs, n_boot=args.bootstrap)
            sens_by_v[v] = {"n": len(xs), "fail_rate": m, "ci_lo": lo, "ci_hi": hi}

    payload = {
        "n_answers": len(rows),
        "distribution_all": dict(dist_all),
        "distribution_by_answerer": {k: dict(v) for k, v in sorted(by_answerer.items())},
        "classifier_fit_dev_labels": dev_fit_rate,
        "n_dev_labels": len(dev_fit),
        "classifier_accuracy_held_out_review2": held_rate,
        "n_held_out_review2_labeled": len(held_acc),
        "n_review2_sheet": len(review2_keys),
        "false_alarm_excludes": [list(x) for x in EXCLUDE],
        "n_correct_for_false_alarm": len(analysis_rows),
        "fail_rates_by_verifier_category": report_fail,
        "changed_value_detection_fail_rate": sens_by_v,
        "n_changed_value_cohort": len(changed_rows),
    }
    t6a_map = {}
    if T6A_MANIFEST.is_file():
        t6a_map = {
            c["id"]: c["jsonl"]
            for c in json.loads(T6A_MANIFEST.read_text()).get("checkers", [])
        }
    payload["verifier_files_present"] = {
        v: (RAW / t6a_map.get(v, f"{v}.jsonl")).is_file() for v in verifiers
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T4 ecological (PI-reviewed classifier + verifier metrics)",
        "",
        f"- Answers classified: **{len(rows)}**",
        f"- Classifier **fit on dev labels** (`eco_PI_ok_labels.csv`, collapsed exact): "
        f"**{dev_fit_rate:.3f}** (n={len(dev_fit)}) — tuning set, not held-out accuracy.",
        f"- **Held-out** classifier accuracy (`eco_review2.csv` rows you labeled, excluding dev 100): "
        f"**{held_rate:.3f}** (n={len(held_acc)} labeled / {len(review2_keys)} on sheet).",
        f"- False-alarm cohort: correct `{', '.join(sorted(CORRECT_CATS))}`, excluding D0122/deepseek (empty) and D0077/command_r (wrong context); **n={len(analysis_rows)}**",
        "",
        "## (a) Category distribution (final = PI override on labeled rows)",
        "",
        "| category | n |",
        "|---|---:|",
    ]
    for cat, n in dist_all.most_common():
        lines.append(f"| {cat} | {n} |")

    lines.extend(["", "### Per answerer", ""])
    for ans in sorted(by_answerer):
        lines.append(
            f"**{ans}**: "
            + ", ".join(f"{c}={n}" for c, n in by_answerer[ans].most_common())
        )

    lines.extend(
        [
            "",
            "## (b) FAIL rate on correct answers (bootstrap 95% CI)",
            "",
            "Hypothesis: specialized checkers false-alarm more on `exact_surface_variant` than `exact_verbatim`; LLM judges less so.",
            "",
        ]
    )

    for v in verifiers:
        present = payload["verifier_files_present"][v]
        tag = " (partial/missing scores)" if not present else ""
        lines.append(f"### {v}{tag}")
        lines.append("| category | n | FAIL rate | 95% CI |")
        lines.append("|---|---:|---:|---|")
        for cat in sorted(CORRECT_CATS):
            cell = report_fail[v][cat]
            if not cell["n"]:
                lines.append(f"| {cat} | 0 | — | — |")
            else:
                lines.append(
                    f"| {cat} | {cell['n']} | {cell['fail_rate']:.3f} | "
                    f"[{cell['ci_lo']:.3f}, {cell['ci_hi']:.3f}] |"
                )
        lines.append("")

    lines.extend(
        [
            "## (c) Detection on human-verified `changed_value` answers",
            "",
            f"Cohort: `eco_category_final=changed_value`, same exclusions as (b); **n={len(changed_rows)}**. "
            "FAIL rate = real-world sensitivity (verifier flags wrong dose).",
            "",
            "| verifier | n scored | FAIL rate | 95% CI |",
            "|---|---:|---:|---|",
        ]
    )
    for v in verifiers:
        cell = sens_by_v[v]
        if not cell["n"]:
            lines.append(f"| {v} | 0 | — | — |")
        else:
            lines.append(
                f"| {v} | {cell['n']} | {cell['fail_rate']:.3f} | "
                f"[{cell['ci_lo']:.3f}, {cell['ci_hi']:.3f}] |"
            )
    lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
