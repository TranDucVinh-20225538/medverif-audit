#!/usr/bin/env python3
"""T19 scale sweep report: QI/NS/US, AUROC, 8B agreement, figure."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from review_filters import effective_unit_natural_y  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402
import t14_t3_filter_report as filt  # noqa: E402

INST = ROOT / "data/t19/instances_t19.jsonl"
RAW = ROOT / "results/raw/t19"
OUT_MD = ROOT / "notes/t19_scale_sweep.md"
OUT_JSON = ROOT / "notes/t19_scale_sweep.json"
OUT_FIG = ROOT / "results/figures/t19_scale.png"

MODELS = [
    {"slug": "llama32_1b", "label": "1B", "params_b": 1.0, "path": RAW / "llama32_1b_instruct.jsonl"},
    {"slug": "llama32_3b", "label": "3B", "params_b": 3.0, "path": RAW / "llama32_3b_instruct.jsonl"},
    {"slug": "llama31_8b_local", "label": "8B (local)", "params_b": 8.0, "path": RAW / "llama31_8b_instruct.jsonl"},
    {"slug": "llama33_70b_api", "label": "70B (API)", "params_b": 70.0, "path": None},
]

V4_MAIN = ROOT / "results/raw/v4_ragas_nli.llama.jsonl"
V4_T14 = ROOT / "results/raw/t14/v4_ragas_nli.jsonl"
API8B_PATHS = [
    ROOT / "results/raw/t7/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/e2_main/v6_ragas_llama31_8b.jsonl",
]

SEED = 42
N_BOOT = 1000


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def load_scores(path: Path | None, extra_paths: list[Path] | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    paths = []
    if path:
        paths.append(path)
    if extra_paths:
        paths.extend(extra_paths)
    for p in paths:
        for row in read_jsonl(p):
            out[row["instance_id"]] = row
    return out


def is_pass(row: dict) -> bool | None:
    v = (row.get("verdict") or "").strip()
    if v == "PASS":
        return True
    if v == "FAIL":
        return False
    s = row.get("score")
    if s is None:
        return None
    return float(s) >= 0.5


def bootstrap_rate(values: list[int]) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    rng = random.Random(SEED)
    n = len(values)
    pts = []
    for _ in range(N_BOOT):
        samp = [values[rng.randrange(n)] for _ in range(n)]
        pts.append(sum(samp) / n)
    pts.sort()
    lo = pts[int(0.025 * len(pts))]
    hi = pts[int(0.975 * len(pts)) - 1]
    return sum(values) / n, lo, hi


def auroc(labels: list[int], scores: list[float]) -> float | None:
    if len(labels) < 2 or len(set(labels)) < 2:
        return None
    pairs = sorted(zip(scores, labels), key=lambda x: x[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    rank_sum = 0.0
    for i, (_, y) in enumerate(pairs, start=1):
        if y == 1:
            rank_sum += i
    u = rank_sum - n_pos * (n_pos + 1) / 2
    return u / (n_pos * n_neg)


def boot_auroc(labels: list[int], scores: list[float]) -> tuple[float | None, float | None, float | None]:
    if len(labels) < 5:
        a = auroc(labels, scores)
        return a, None, None
    rng = random.Random(SEED)
    n = len(labels)
    pts = []
    for _ in range(N_BOOT):
        idx = [rng.randrange(n) for _ in range(n)]
        y = [labels[i] for i in idx]
        s = [scores[i] for i in idx]
        a = auroc(y, s)
        if a is not None:
            pts.append(a)
    if not pts:
        return None, None, None
    pts.sort()
    return pts[len(pts) // 2], pts[int(0.025 * len(pts))], pts[int(0.975 * len(pts)) - 1]


def inv_natural_ids(instances: list[dict]) -> set[str]:
    out = set()
    for r in instances:
        if r.get("t19_pack") != "main_dose":
            continue
        if r.get("condition") != "INV-claim" or r.get("magnitude") != "unit_conversion":
            continue
        orig = filt.inv_span_before(r)
        if effective_unit_natural_y(r["base_id"], bool(rule_natural_unit_conversion_label(orig))):
            out.add(r["instance_id"])
    return out


def x1000_ids(instances: list[dict]) -> set[str]:
    out = set()
    for r in instances:
        if r.get("t19_pack") == "main_e1_unit" and r.get("magnitude") == "x1000":
            out.add(r["instance_id"])
        if r.get("t19_pack") == "main_dose" and r.get("condition") in ("E1-unit-claim", "E1-unit-evid"):
            out.add(r["instance_id"])
    return out


def c0_bases(instances: list[dict]) -> set[str]:
    return {
        r["base_id"]
        for r in instances
        if r.get("t19_pack", "").startswith("main") and r.get("condition") == "C0" and r.get("valid", True)
    }


def metrics_for_model(instances: list[dict], scores: dict[str, dict]) -> dict:
    inv_ids = inv_natural_ids(instances)
    x1k = x1000_ids(instances)
    c0_pass_bases = {
        r["base_id"]
        for r in instances
        if r.get("condition") == "C0"
        and r["base_id"] in c0_bases(instances)
        and is_pass(scores.get(r["instance_id"], {})) is True
    }
    inv_hits: list[int] = []
    e1_fail: list[int] = []
    c0_hits: list[int] = []
    for r in instances:
        if not r.get("t19_pack", "").startswith("main") and r.get("t19_pack") != "main_e1_unit":
            continue
        iid = r["instance_id"]
        sc = scores.get(iid)
        if not sc:
            continue
        p = is_pass(sc)
        if p is None:
            continue
        bid = r["base_id"]
        if r.get("condition") == "C0":
            c0_hits.append(int(p))
        if iid in inv_ids and bid in c0_pass_bases:
            inv_hits.append(int(p))
        if bid not in c0_pass_bases:
            continue
        if iid in x1k or (
            r.get("condition") in ("E1-claim", "E1-evid") and r.get("magnitude") in ("x2", "x10")
        ):
            e1_fail.append(int(not p))
    qi, qi_lo, qi_hi = bootstrap_rate(inv_hits)
    ns, ns_lo, ns_hi = bootstrap_rate(e1_fail)
    us = qi
    c0, c0_lo, c0_hi = bootstrap_rate(c0_hits)
    return {
        "QI": qi,
        "QI_ci": [qi_lo, qi_hi],
        "NS": ns,
        "NS_ci": [ns_lo, ns_hi],
        "US": us,
        "C0_pass": c0,
        "C0_ci": [c0_lo, c0_hi],
        "n_inv": len(inv_hits),
        "n_e1": len(e1_fail),
        "n_c0": len(c0_hits),
    }


def auroc_cohorts(instances: list[dict], scores: dict[str, dict]) -> dict:
    conv_ids = inv_natural_ids(instances)
    unit_ids = x1000_ids(instances)
    c0_ids = {r["instance_id"] for r in instances if r.get("condition") == "C0" and r.get("t19_pack") == "main_dose"}

    def collect(id_set: set[str], label: int) -> tuple[list[int], list[float]]:
        y, s = [], []
        for iid in id_set:
            row = scores.get(iid)
            if not row or row.get("p_yes") is None:
                continue
            y.append(label)
            s.append(float(row["p_yes"]))
        return y, s

    y0, s0 = collect(c0_ids, 0)
    y1, s1 = collect(conv_ids, 1)
    labels = y0 + y1
    scs = s0 + s1
    a_c0_conv, lo_cc, hi_cc = boot_auroc(labels, scs)

    yc, sc = collect(conv_ids, 1)
    yu, su = collect(unit_ids, 0)
    labels2 = yc + yu
    scs2 = sc + su
    a_conv_unit, lo_cu, hi_cu = boot_auroc(labels2, scs2)
    return {
        "AUROC_C0_vs_Conv": a_c0_conv,
        "AUROC_C0_vs_Conv_ci": [lo_cc, hi_cc],
        "AUROC_Conv_vs_Unit": a_conv_unit,
        "AUROC_Conv_vs_Unit_ci": [lo_cu, hi_cu],
        "n_c0_conv": len(labels),
        "n_conv_unit": len(labels2),
    }


def agreement_8b(local: dict[str, dict], api: dict[str, dict], instances: list[dict]) -> dict:
    agree = tot = 0
    for r in instances:
        iid = r["instance_id"]
        a, b = local.get(iid), api.get(iid)
        if not a or not b:
            continue
        pa, pb = is_pass(a), is_pass(b)
        if pa is None or pb is None:
            continue
        tot += 1
        agree += int(pa == pb)
    return {"n": tot, "agreement": (agree / tot if tot else None)}


def main() -> None:
    instances = read_jsonl(INST)
    if not instances:
        raise SystemExit(f"missing instances: {INST}")

    api70 = load_scores(V4_MAIN, [V4_T14])
    api8b = load_scores(None, API8B_PATHS)

    model_rows = []
    for spec in MODELS:
        if spec["slug"] == "llama33_70b_api":
            scores = api70
        else:
            scores = load_scores(spec["path"])
        m = metrics_for_model(instances, scores)
        au = auroc_cohorts(instances, scores) if spec["slug"] != "llama33_70b_api" else {
            "AUROC_C0_vs_Conv": None,
            "AUROC_Conv_vs_Unit": None,
            "note": "AUROC from p_yes requires local scores",
        }
        row = {
            "slug": spec["slug"],
            "label": spec["label"],
            "params_b": spec["params_b"],
            **m,
            **au,
            "n_scored": sum(1 for r in instances if r["instance_id"] in scores),
        }
        if spec["slug"] == "llama31_8b_local":
            row["api8b_agreement"] = agreement_8b(scores, api8b, instances)
        model_rows.append(row)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {"instances": len(instances), "models": model_rows}
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T19 scale sweep (RAGAS-NLI)",
        "",
        f"Cohort: `{INST.relative_to(ROOT)}` (n={len(instances)} instances; non-dose excluded).",
        "",
        "| Params | Model | QI | NS | US | C0 pass | n(inv) | n(E1) | AUROC C0 vs Conv | AUROC Conv vs Unit |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in model_rows:
        def pct(x, ci=None):
            if x is None:
                return "NA"
            if ci and ci[0] is not None:
                return f"{100*x:.1f}% [{100*ci[0]:.1f},{100*ci[1]:.1f}]"
            return f"{100*x:.1f}%"

        a_cc = r.get("AUROC_C0_vs_Conv")
        a_cu = r.get("AUROC_Conv_vs_Unit")
        s_cc = "NA" if a_cc is None else f"{a_cc:.3f}"
        s_cu = "NA" if a_cu is None else f"{a_cu:.3f}"
        lines.append(
            f"| {r['params_b']:.0f}B | {r['label']} | {pct(r.get('QI'), r.get('QI_ci'))} | "
            f"{pct(r.get('NS'), r.get('NS_ci'))} | {pct(r.get('US'))} | {pct(r.get('C0_pass'), r.get('C0_ci'))} | "
            f"{r.get('n_inv', 0)} | {r.get('n_e1', 0)} | {s_cc} | {s_cu} |"
        )
    loc = next((r for r in model_rows if r["slug"] == "llama31_8b_local"), None)
    if loc and loc.get("api8b_agreement"):
        ag = loc["api8b_agreement"]
        lines.extend(
            [
                "",
                f"**8B local vs API (T6-B Llama-3.1-8B) verdict agreement:** "
                f"{100*(ag.get('agreement') or 0):.1f}% (n={ag.get('n', 0)}).",
            ]
        )
    OUT_MD.write_text("\n".join(lines) + "\n")

    try:
        import matplotlib.pyplot as plt

        OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
        xs = [r["params_b"] for r in model_rows]
        for ax, key, title in zip(
            axes,
            ("QI", "NS", "US"),
            ("QI (INV natural PASS)", "NS (E1 FAIL)", "US"),
        ):
            ys = [r.get(key) for r in model_rows]
            ax.plot(xs, ys, "o-")
            ax.set_xscale("log")
            ax.set_xlabel("Parameters (B)")
            ax.set_ylabel("Rate")
            ax.set_title(title)
            ax.set_ylim(0, 1)
        fig.tight_layout()
        fig.savefig(OUT_FIG, dpi=150)
        plt.close(fig)
    except Exception as exc:
        print(f"figure skipped: {exc}", file=sys.stderr)

    print(OUT_MD.read_text())


if __name__ == "__main__":
    main()
