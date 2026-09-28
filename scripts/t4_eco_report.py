#!/usr/bin/env python3
"""T4 eco: PI-labeled cohort stats + verifier false-alarm rates (bootstrap CIs)."""

from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t4_eco_compare import (  # noqa: E402
    apply_pi_override,
    collapse_exact,
    gold_from_pi_row,
    load_pi_label_paths,
    load_pi_sheet_keys,
)

CLASSIFIED = ROOT / "data/t4/eco_classified.jsonl"
DEV_LABELS = ROOT / "qc/eco_PI_ok_labels.csv"
HELD_LABELS = ROOT / "qc/eco2_PI_ok_labels.csv"
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


def final_category(row: dict, labels: dict) -> str:
    cat = row.get("eco_category") or ""
    return apply_pi_override(row["task_id"], row["answerer_id"], cat, labels)


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
    labels = load_pi_label_paths([DEV_LABELS, HELD_LABELS])
    labeled_keys = set(labels.keys())
    dev_labels = load_pi_label_paths([DEV_LABELS])
    held_labels = load_pi_label_paths([HELD_LABELS])

    verifiers = all_verifiers()
    scores = load_scores(verifiers)

    labeled_rows = [r for r in rows if instance_key(r) in labeled_keys]
    dist_labeled = Counter(final_category(r, labels) for r in labeled_rows)

    dev_fit = classifier_vs_gold(rows, dev_labels)
    dev_fit_rate = sum(dev_fit) / len(dev_fit) if dev_fit else float("nan")
    held_acc = classifier_vs_gold(rows, held_labels)
    held_rate = sum(held_acc) / len(held_acc) if held_acc else float("nan")
    held_pi_ok = [
        1
        for lab in held_labels.values()
        if (lab.get("PI_ok") or "").strip().upper() == "Y"
    ]
    held_pi_ok_rate = len(held_pi_ok) / len(held_labels) if held_labels else float("nan")

    n_all = len(rows)
    finals_all = [final_category(r, labels) for r in rows]
    n_omitted = sum(1 for c in finals_all if c == "omitted")
    n_changed_final = sum(1 for c in finals_all if c == "changed_value")
    n_classifier_changed = sum(1 for r in rows if r.get("eco_category") == "changed_value")

    analysis_rows = []
    for r in labeled_rows:
        key = instance_key(r)
        if key in EXCLUDE:
            continue
        cat = final_category(r, labels)
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

    payload = {
        "n_answers_scored": n_all,
        "n_pi_labeled": len(labeled_keys),
        "n_labeled_rows_in_classified": len(labeled_rows),
        "distribution_pi_labeled_final": dict(dist_labeled),
        "classifier_fit_dev_labels": dev_fit_rate,
        "n_dev_labels": len(dev_fit),
        "classifier_accuracy_held_out_eco2_pred_vs_gold": held_rate,
        "n_held_out_eco2_pred_vs_gold": len(held_acc),
        "classifier_acceptance_held_out_eco2_PI_ok": held_pi_ok_rate,
        "n_held_out_eco2_PI_ok_Y": len(held_pi_ok),
        "n_held_out_sheet": len(load_pi_sheet_keys(HELD_LABELS)),
        "real_dose_error_rate": n_changed_final / n_all if n_all else None,
        "n_real_dose_errors_final": n_changed_final,
        "omission_target_mismatch_rate": n_omitted / n_all if n_all else None,
        "n_omitted_final": n_omitted,
        "n_classifier_changed_value_raw": n_classifier_changed,
        "false_alarm_excludes": [list(x) for x in EXCLUDE],
        "n_correct_for_false_alarm_labeled": len(analysis_rows),
        "fail_rates_by_verifier_category": report_fail,
        "pi_real_error_note": "D0162__eco / command_r (only PI-confirmed true dose error in review)",
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
        f"- Ecological answers in scored cohort: **{n_all}**",
        f"- PI-labeled rows (dev 100 + eco2 72): **{len(labeled_keys)}** "
        f"({len(labeled_rows)} present in classified file)",
        f"- Classifier **fit on dev labels** (`eco_PI_ok_labels.csv`, collapsed exact): "
        f"**{dev_fit_rate:.3f}** (n={len(dev_fit)}) — tuning set, not held-out accuracy.",
        f"- **Held-out** classifier acceptance (`eco2_PI_ok_labels.csv`, PI_ok=Y): "
        f"**{held_pi_ok_rate:.3f}** ({len(held_pi_ok)}/{len(held_labels)} = 45/72 when fully labeled).",
        f"- Held-out pred vs gold category (strict): **{held_rate:.3f}** (n={len(held_acc)} scored).",
        f"- False-alarm cohort: PI-labeled rows with final category "
        f"`{', '.join(sorted(CORRECT_CATS))}`, excluding D0122/deepseek and D0077/command_r; "
        f"**n={len(analysis_rows)}**",
        "",
        "## (a) Category distribution (PI-labeled rows only; final = human override)",
        "",
        "| category | n |",
        "|---|---:|",
    ]
    for cat, n in dist_labeled.most_common():
        lines.append(f"| {cat} | {n} |")

    lines.extend(
        [
            "",
            "## (b) FAIL rate on correct answers (PI-labeled cohort; bootstrap 95% CI)",
            "",
            "Among human-labeled **correct** answers (`exact_verbatim`, `exact_surface_variant`, "
            "`frequency_rephrased`), fraction of verifier FAIL.",
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

    real_rate = n_changed_final / n_all if n_all else float("nan")
    omit_rate = n_omitted / n_all if n_all else float("nan")
    lines.extend(
        [
            "## Cohort error rates (full scored ecological set)",
            "",
            f"- **Real dose-error rate** (final `changed_value` after PI override): "
            f"**{n_changed_final}/{n_all} = {real_rate:.4f}** in current cohort "
            f"(**1/444** in the original ecological run; only **D0162__eco / command_r**).",
            f"- **Omission / target-mismatch rate** (final `omitted`): "
            f"**{n_omitted}/{n_all} = {omit_rate:.4f}**.",
            f"- Classifier raw `changed_value` (before PI override on unlabeled rows): **{n_classifier_changed}**.",
            "",
            "Classifier rules: `notes/t4_eco_classifier_rules.md`.",
            "",
        ]
    )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
