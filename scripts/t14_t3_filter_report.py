#!/usr/bin/env python3
"""T3-style filter view: ×1000 keep vs INV drop + T13 pairwise (no new scoring)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from review_filters import effective_unit_natural_y  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

import t13_best_of_n_report as t13  # noqa: E402

from t13_best_of_n_report import (  # noqa: E402
    CANONICAL_VERIFIERS,
    MAIN,
    T7,
    VERIFIER_FAMILY,
    inv_span_before,
    merged_score_rows,
    score_from_row,
)

OUT_MD = ROOT / "results/tables/t14_t3_filter_view.md"
OUT_JSON = ROOT / "notes/t14_t3_filter_view.json"
OUT_FIG = ROOT / "results/figures/t14_t3_filter_reward.png"
T13_JSON = ROOT / "notes/t13_pairwise_preference.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def is_pass(slug: str, row: dict) -> bool | None:
    score, mode = score_from_row(row)
    if score is None:
        return None
    if slug == "v1_medscore" or slug == "v1b_medscore" or slug == "v1c_medscore":
        return score >= 1.0 - 1e-9
    if slug in ("v2a_minicheck", "v2b_bespoke", "v3_alignscore") or slug.startswith("t6"):
        return score > 0.5
    if slug.startswith("v4") or slug.startswith("v5") or slug.startswith("v6"):
        verdict = (row.get("verdict") or "").strip()
        if verdict == "PASS":
            return True
        if verdict == "FAIL":
            return False
        return score >= 0.5
    return score > 0.5


def x1000_claim_ids() -> list[str]:
    main_bases = {
        r["base_id"]
        for r in read_jsonl(MAIN)
        if r.get("valid", True) and r.get("type") == "DOSE" and r.get("subset") == "main"
    }
    out = []
    for r in read_jsonl(T7):
        if not r.get("valid", True):
            continue
        if r.get("condition") != "E1-unit-claim" or r.get("magnitude") != "x1000":
            continue
        if r["base_id"] in main_bases:
            out.append(r["instance_id"])
    return out


def inv_natural_ids() -> list[str]:
    out = []
    for r in read_jsonl(MAIN):
        if not r.get("valid", True) or r.get("type") != "DOSE" or r.get("subset") != "main":
            continue
        if r.get("condition") != "INV-claim" or r.get("magnitude") != "unit_conversion":
            continue
        orig = inv_span_before(r)
        if effective_unit_natural_y(r["base_id"], bool(rule_natural_unit_conversion_label(orig))):
            out.append(r["instance_id"])
    return out


def load_t13_pair1() -> dict[str, float]:
    if not T13_JSON.is_file():
        subprocess.run([sys.executable, str(ROOT / "scripts/t13_best_of_n_report.py")], check=False)
    if not T13_JSON.is_file():
        return {}
    data = json.loads(T13_JSON.read_text())
    out = {}
    for v, cell in data.get("by_verifier", {}).items():
        p = (cell.get("pairs") or {}).get("x1000_vs_inv") or {}
        if p.get("n_pairs"):
            out[v] = p.get("p_wrong_prefers")
    return out


def main() -> None:
    x1k = x1000_claim_ids()
    inv = inv_natural_ids()
    t13_p = load_t13_pair1()
    rows_out: dict[str, dict] = {}

    for slug in CANONICAL_VERIFIERS:
        scores = merged_score_rows(slug)
        keep_x1k: list[int] = []
        drop_inv: list[int] = []
        for iid in x1k:
            row = scores.get(iid)
            if not row:
                continue
            p = is_pass(slug, row)
            if p is None:
                continue
            keep_x1k.append(int(p))
        for iid in inv:
            row = scores.get(iid)
            if not row:
                continue
            p = is_pass(slug, row)
            if p is None:
                continue
            drop_inv.append(int(not p))
        if not keep_x1k and not drop_inv:
            rows_out[slug] = {
                "family": VERIFIER_FAMILY.get(slug, "other"),
                "keep_rate_x1000": None,
                "drop_rate_inv_natural": None,
                "n_x1000": 0,
                "n_inv_natural": 0,
                "t13_p_wrong_vs_inv": t13_p.get(slug),
            }
            continue
        rows_out[slug] = {
            "family": VERIFIER_FAMILY.get(slug, "other"),
            "keep_rate_x1000": sum(keep_x1k) / len(keep_x1k) if keep_x1k else None,
            "drop_rate_inv_natural": sum(drop_inv) / len(drop_inv) if drop_inv else None,
            "n_x1000": len(keep_x1k),
            "n_inv_natural": len(drop_inv),
            "t13_p_wrong_vs_inv": t13_p.get(slug),
            "note": "keep_x1000 = P(PASS|×1000 error); drop_inv = P(FAIL|correct INV natural); 1−US / 1−QI",
        }

    payload = {
        "x1000_claim_ids": len(x1k),
        "inv_natural_ids": len(inv),
        "by_verifier": rows_out,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T14 / T3 filter view (#3 — existing scores only)",
        "",
        "At each verifier’s **default threshold** (see `configs/verifiers.yaml`):",
        "- **keep rate ×1000** = P(PASS | E1-unit-claim ×1000 wrong) — bad if high (= **1−US**).",
        "- **drop rate INV natural** = P(FAIL | INV-unit natural correct) — bad if high (= **1−QI**).",
        "- **T13 pair (1)** = P(score(×1000) ≥ score(INV natural)) with tie=0.5.",
        "",
        f"- ×1000 claim instances (main DOSE): **{len(x1k)}**; INV natural: **{len(inv)}**.",
        "",
        "| verifier | family | keep ×1000 | drop INV | T13 pair(1) | n ×1000 | n INV |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    fam_order = {"encoders": 0, "llm_checker": 1, "llm_judges": 2, "other": 3}

    def fmt(x):
        return f"{x:.3f}" if x is not None and x == x else "—"

    for v, d in sorted(rows_out.items(), key=lambda t: (fam_order.get(t[1]["family"], 9), t[0])):
        lines.append(
            f"| {v} | {d['family']} | {fmt(d['keep_rate_x1000'])} | {fmt(d['drop_rate_inv_natural'])} | "
            f"{fmt(d.get('t13_p_wrong_vs_inv'))} | {d['n_x1000']} | {d['n_inv_natural']} |"
        )

    write_figure(rows_out)
    if OUT_FIG.is_file():
        lines.extend(["", f"Figure: `{OUT_FIG.relative_to(ROOT)}`", ""])

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


def write_figure(rows: dict[str, dict]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fam_order = {"encoders": 0, "llm_checker": 1, "llm_judges": 2, "other": 3}
    items = [
        (v, d)
        for v, d in rows.items()
        if d.get("n_x1000", 0) >= 10 and d.get("keep_rate_x1000") is not None
    ]
    items.sort(key=lambda t: (fam_order.get(t[1]["family"], 9), t[0]))
    if not items:
        return
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, max(4, 0.28 * len(items))))
    y = range(len(items))
    keep = [d["keep_rate_x1000"] for _, d in items]
    drop = [d.get("drop_rate_inv_natural") or 0 for _, d in items]
    t13 = [d.get("t13_p_wrong_vs_inv") or 0 for _, d in items]
    h = 0.25
    ax.barh([i - h for i in y], keep, height=h, label="keep ×1000 (bad↑)", color="#c44e52")
    ax.barh(y, drop, height=h, label="drop INV nat (bad↑)", color="#dd8452")
    ax.barh([i + h for i in y], t13, height=h, label="T13 P(wrong≥INV)", color="#4c72b0")
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{v} ({d['family']})" for v, d in items], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Rate (filter / reward harm proxy)")
    ax.set_title("If this verifier were your data filter or reward")
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
