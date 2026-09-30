#!/usr/bin/env python3
"""Figure 1: QI_all (x) vs US_up claim ×1000 FAIL (y), one point per configuration.

Colour = family, marker area = API cost ($/1k claims, from logged api_cost_usd; local models drawn at a floor size).
Inset: NS (E1-evid FAIL | C0 PASS). Metrics and cohort as in scripts/t15_card_report.py (main DOSE, | C0 PASS,
cluster bootstrap by base)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
for p in ("analysis", "scripts", "src"):
    sys.path.insert(0, str(ROOT / p))

import m1_strong_run as m1s  # noqa: E402
from t13_best_of_n_report import merged_score_rows  # noqa: E402
from t15_card_report import T7, join_extra, join_rows, load_main_dose_instances, metrics_block  # noqa: E402
from verifier_labels import CANONICAL_VERIFIERS, verifier_display_name, verifier_family  # noqa: E402

OUT_PDF = ROOT / "results/figures/fig1_qi_vs_us.pdf"
OUT_JSON = ROOT / "results/figures/fig1_qi_vs_us.json"
COLORS = {
    "small fine-tuned checkers": "#1f77b4",
    "7B fine-tuned checker": "#9467bd",
    "LLM judges": "#d62728",
    "T15 fine-tuned (ours)": "#2ca02c",
}
FLOOR_AREA = 25.0


def verdicts(rows: dict[str, dict]) -> dict[str, str]:
    out = {}
    for iid, r in rows.items():
        v = r.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[iid] = v
        elif r.get("score") is not None:
            out[iid] = "PASS" if float(r["score"]) >= 0.5 else "FAIL"
    return out


def cost_per_1k(rows: dict[str, dict], ids: set[str]) -> float | None:
    costs = [float(r["api_cost_usd"]) for i, r in rows.items() if i in ids and r.get("api_cost_usd") is not None]
    return 1000 * sum(costs) / len(costs) if costs else None


def main() -> None:
    inst = load_main_dose_instances()
    ids = {r["instance_id"] for r in inst}
    points = []
    for slug in CANONICAL_VERIFIERS:
        rows = merged_score_rows(slug)
        v = verdicts(rows)
        for iid, verdict in m1s.merge_verdicts(slug, (ROOT / "results/raw/lane_b/main_e1_evid",)).items():
            v.setdefault(iid, verdict)
        block = join_rows(inst, v) + join_extra(inst, v, T7)
        m = metrics_block(block, set())
        if m["qi_all"].get("rate") is None or m["us_claim_up"].get("rate") is None:
            continue
        points.append({"slug": slug, "label": verifier_display_name(slug), "family": verifier_family(slug),
                       "cost_per_1k": cost_per_1k(rows, ids), "qi_all": m["qi_all"], "us_claim_up": m["us_claim_up"], "ns": m["ns"]})
    ft = json.loads((ROOT / "notes/t15_card.json").read_text())["main_dose"]["ft"]
    points.append({"slug": "t15_ft", "label": "MiniCheck-RoBERTa T15-ft", "family": "T15 fine-tuned (ours)", "cost_per_1k": None,
                   "qi_all": ft["qi_all"], "us_claim_up": ft["us_claim_up"], "ns": ft["ns"]})

    max_cost = max((p["cost_per_1k"] or 0) for p in points) or 1.0
    fig, ax = plt.subplots(figsize=(7.6, 6.6))
    crowded = sorted((p for p in points if p["qi_all"]["rate"] > 0.9 and p["us_claim_up"]["rate"] > 0.9),
                     key=lambda p: -p["us_claim_up"]["rate"])
    offsets = {p["slug"]: (-120, 14 - 9 * i) for i, p in enumerate(crowded)}
    for p in points:
        x, y = 100 * p["qi_all"]["rate"], 100 * p["us_claim_up"]["rate"]
        c = p["cost_per_1k"] or 0.0
        area = FLOOR_AREA + 575.0 * (c / max_cost) ** 0.5
        col = COLORS.get(p["family"], "grey")
        ax.errorbar(x, y, xerr=[[x - 100 * p["qi_all"]["lo"]], [100 * p["qi_all"]["hi"] - x]],
                    yerr=[[y - 100 * p["us_claim_up"]["lo"]], [100 * p["us_claim_up"]["hi"] - y]],
                    fmt="none", ecolor=col, alpha=0.25, lw=0.8, zorder=1)
        ax.scatter(x, y, s=area, c=col, alpha=0.8, edgecolors="black", linewidths=0.5, zorder=2)
        off = offsets.get(p["slug"])
        if off:
            ax.annotate(p["label"], (x, y), fontsize=6, xytext=off, textcoords="offset points",
                        arrowprops={"arrowstyle": "-", "lw": 0.4, "color": "grey"})
        else:
            ax.annotate(p["label"], (x, y), fontsize=6, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("QI_all: PASS on quantity-invariant rewrites | C0 PASS (%)")
    ax.set_ylabel("US_up claim ×1000: FAIL | C0 PASS (%)")
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.grid(alpha=0.3)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=f) for f, c in COLORS.items()]
    for usd in (0.1, 1.0, 5.0):
        if usd <= max_cost * 1.2:
            handles.append(plt.scatter([], [], s=FLOOR_AREA + 575.0 * (usd / max_cost) ** 0.5, c="white", edgecolors="black", label=f"${usd:g}/1k claims"))
    handles.append(plt.scatter([], [], s=FLOOR_AREA, c="white", edgecolors="black", label="local (≈$0 API)"))
    ax.legend(handles=handles, fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, framealpha=0.9)

    ins = ax.inset_axes([0.72, 0.05, 0.26, 0.42])
    order = sorted((p for p in points if p["ns"].get("rate") is not None), key=lambda p: p["ns"]["rate"])
    for i, p in enumerate(order):
        r = 100 * p["ns"]["rate"]
        ins.errorbar(r, i, xerr=[[r - 100 * p["ns"]["lo"]], [100 * p["ns"]["hi"] - r]], fmt="o", ms=2.5,
                     color=COLORS.get(p["family"], "grey"), lw=0.6)
    ins.set_yticks(range(len(order)))
    ins.set_yticklabels([p["label"].split(" (")[0] for p in order], fontsize=4.5)
    ins.set_xlabel("NS: E1-evid FAIL | C0 (%)", fontsize=6)
    ins.tick_params(labelsize=6)
    ins.set_title("NS (value error in evidence)", fontsize=6.5)
    fig.tight_layout()
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_PDF.with_suffix(".png"), dpi=160)
    OUT_JSON.write_text(json.dumps(points, indent=1) + "\n")
    for p in points:
        print(f"{p['label']:34s} {p['family']:26s} QI_all={100*p['qi_all']['rate']:5.1f} (n={p['qi_all']['den']}) "
              f"US_up={100*p['us_claim_up']['rate']:5.1f} (n={p['us_claim_up']['den']}) NS={100*p['ns']['rate'] if p['ns'].get('rate') is not None else float('nan'):5.1f} "
              f"cost={p['cost_per_1k']}")


if __name__ == "__main__":
    main()
