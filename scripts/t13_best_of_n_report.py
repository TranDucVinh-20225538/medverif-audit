#!/usr/bin/env python3
"""T13: pairwise preference harm (primary) + legacy best-of-N appendix."""

from __future__ import annotations

import csv
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import read_jsonl  # noqa: E402
from review_filters import effective_unit_natural_y  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402
from verifier_labels import (  # noqa: E402
    CANONICAL_VERIFIERS,
    FAMILY_COLORS,
    FAMILY_ORDER,
    verifier_display_name,
    verifier_family,
)

MAIN = ROOT / "data/v3/instances_main.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
DOSE3 = ROOT / "qc/dose3_labels.csv"
T7_PI = ROOT / "qc/t7_PI_ok_labels.csv"
T6A = ROOT / "notes/t6a_eco_checkers.json"
OUT_MD = ROOT / "results/tables/t13_pairwise_preference.md"
OUT_JSON = ROOT / "notes/t13_pairwise_preference.json"
OUT_FIG = ROOT / "results/figures/t13_pairwise_x1000_vs_inv.png"
LEGACY_JSON = ROOT / "notes/t13_best_of_n_legacy.json"

SCORE_DIRS = [
    ROOT / "results/raw/e2_main",
    ROOT / "results/raw/t4_eco",
    ROOT / "results/raw/t4c_eco",
    ROOT / "results/raw/t7",
    ROOT / "results/raw/t3",
    ROOT / "results/raw/t3_t2",
    ROOT / "results/raw/t3_t6b",
    ROOT / "results/raw/t6b/full",
    ROOT / "results/raw/t2_full",
    ROOT / "results/raw_m1",
    ROOT / "results/raw_m1/t7",
    ROOT / "results/raw",
]

N_BOOT = 2000
BOOT_SEED = 42

PAIR_TYPES: tuple[tuple[str, str, str], ...] = (
    ("x1000_vs_inv", "E1-unit-claim×1000", "INV-unit natural"),
    ("x1000_vs_inv_all", "E1-unit-claim×1000", "INV-unit (all)"),
    ("x1000_vs_c0", "E1-unit-claim×1000", "C0"),
    ("evid_x1000_vs_c0", "E1-unit-evid×1000", "C0"),
    ("e1x2_vs_inv", "E1-claim×2", "INV-unit natural"),
)

PRIMARY_PAIR_KEYS = ("x1000_vs_inv", "x1000_vs_inv_all", "evid_x1000_vs_c0")


@dataclass
class BaseSlice:
    base_id: str
    c0: str | None = None
    inv_natural: str | None = None
    inv_all: str | None = None
    e1_claim_x2: str | None = None
    e1_unit_x1000: str | None = None
    e1_evid_x1000: str | None = None


def inv_span_before(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    return str(claim.get("span_before") or row.get("claim_span") or "")


def t7_pi_sample_stats() -> dict[str, int]:
    if not T7_PI.is_file():
        return {"labeled": 0, "pi_ok_y": 0}
    with T7_PI.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        "labeled": len(rows),
        "pi_ok_y": sum(1 for r in rows if (r.get("PI_ok") or "").strip().upper() == "Y"),
    }


def main_dose_slices() -> dict[str, BaseSlice]:
    """All valid main DOSE bases; slice instance_ids where defined."""
    slices: dict[str, BaseSlice] = {}
    for r in read_jsonl(MAIN):
        if not r.get("valid", True) or r.get("type") != "DOSE" or r.get("subset") != "main":
            continue
        bid = r["base_id"]
        slices.setdefault(bid, BaseSlice(base_id=bid))
        cond, mag = r.get("condition"), r.get("magnitude")
        if cond == "C0":
            slices[bid].c0 = r["instance_id"]
        elif cond == "E1-claim" and mag == "x2":
            slices[bid].e1_claim_x2 = r["instance_id"]
        elif cond == "INV-claim" and mag == "unit_conversion":
            slices[bid].inv_all = r["instance_id"]
            orig = inv_span_before(r)
            rule_y = bool(rule_natural_unit_conversion_label(orig))
            if effective_unit_natural_y(bid, rule_y):
                slices[bid].inv_natural = r["instance_id"]
    for r in read_jsonl(T7):
        if not r.get("valid", True):
            continue
        bid = r["base_id"]
        if bid not in slices:
            continue
        if r.get("magnitude") != "x1000":
            continue
        if r.get("condition") == "E1-unit-claim":
            slices[bid].e1_unit_x1000 = r["instance_id"]
        elif r.get("condition") == "E1-unit-evid":
            slices[bid].e1_evid_x1000 = r["instance_id"]
    return slices


def pair_members(sl: BaseSlice, pair_key: str) -> tuple[str, str] | None:
    if pair_key == "x1000_vs_inv":
        if sl.e1_unit_x1000 and sl.inv_natural:
            return sl.e1_unit_x1000, sl.inv_natural
    elif pair_key == "x1000_vs_inv_all":
        if sl.e1_unit_x1000 and sl.inv_all:
            return sl.e1_unit_x1000, sl.inv_all
    elif pair_key == "x1000_vs_c0":
        if sl.e1_unit_x1000 and sl.c0:
            return sl.e1_unit_x1000, sl.c0
    elif pair_key == "evid_x1000_vs_c0":
        if sl.e1_evid_x1000 and sl.c0:
            return sl.e1_evid_x1000, sl.c0
    elif pair_key == "e1x2_vs_inv":
        if sl.e1_claim_x2 and sl.inv_natural:
            return sl.e1_claim_x2, sl.inv_natural
    return None


def _verifier_slug(path: Path) -> str | None:
    name = path.name
    if "quarantine" in name or ".legacy." in name:
        return None
    if name.endswith(".llama.jsonl"):
        return name[: -len(".llama.jsonl")]
    if name.endswith(".jsonl"):
        return name[: -len(".jsonl")]
    return None


def all_verifier_slugs() -> list[str]:
    slugs: set[str] = set()
    for d in SCORE_DIRS:
        if not d.is_dir():
            continue
        for p in d.glob("*.jsonl"):
            slug = _verifier_slug(p)
            if slug:
                slugs.add(slug)
    if T6A.is_file():
        for c in json.loads(T6A.read_text()).get("checkers", []):
            slugs.add(c["id"])
    if any((d / "t6_bespoke_minicheck.jsonl").is_file() for d in SCORE_DIRS):
        slugs.add("v2b_bespoke")
    return sorted(slugs)


def score_from_row(row: dict) -> tuple[float | None, str]:
    """Higher = verifier prefers / more supported. LLM: score or logprob; else PASS/FAIL."""
    for key in ("score", "released_parser_score", "parser_score"):
        if key in row and row[key] is not None:
            try:
                return float(row[key]), "continuous"
            except (TypeError, ValueError):
                pass
    for key in ("mean_logprob", "logprob", "ll", "log_prob"):
        if key in row and row[key] is not None:
            try:
                return float(row[key]), "logprob"
            except (TypeError, ValueError):
                pass
    raw = row.get("raw_output")
    if raw is not None and raw != "":
        try:
            return float(raw), "continuous"
        except (TypeError, ValueError):
            pass
    verdict = (row.get("verdict") or "").strip()
    if verdict == "PARSE_FAIL":
        return None, "missing"
    if verdict == "PASS":
        return 1.0, "binary"
    if verdict == "FAIL":
        return 0.0, "binary"
    return None, "missing"


def merged_score_rows(slug: str) -> dict[str, dict]:
    paths: list[Path] = []
    if T6A.is_file():
        t6a = {c["id"]: c["jsonl"] for c in json.loads(T6A.read_text()).get("checkers", [])}
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
    out: dict[str, dict] = {}
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        for row in read_jsonl(path):
            iid = row.get("instance_id")
            if iid:
                out[iid] = row
    return out


def preference(wrong_s: float, correct_s: float) -> float:
    """P(wrong ≥ correct) contribution: 1 / 0 / 0.5 on tie."""
    if wrong_s > correct_s:
        return 1.0
    if wrong_s < correct_s:
        return 0.0
    return 0.5


def cluster_bootstrap(outcomes: list[float], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> tuple[float, float, float]:
    if not outcomes:
        return float("nan"), float("nan"), float("nan")
    n = len(outcomes)
    mean = sum(outcomes) / n
    rng = random.Random(seed)
    boots = sorted(sum(rng.choice(outcomes) for _ in range(n)) / n for _ in range(n_boot))
    return mean, boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]


def analyze_pairwise(
    slices: dict[str, BaseSlice],
) -> tuple[dict[str, dict], dict[str, int]]:
    """Returns by_verifier stats and eligible pair counts (structural, before scoring)."""
    structural: dict[str, int] = {k: 0 for k, _, _ in PAIR_TYPES}
    for sl in slices.values():
        for pk, _, _ in PAIR_TYPES:
            if pair_members(sl, pk):
                structural[pk] += 1

    by_verifier: dict[str, dict] = {}
    slugs = list(dict.fromkeys(list(CANONICAL_VERIFIERS) + all_verifier_slugs()))
    for slug in slugs:
        rows = merged_score_rows(slug)
        modes: set[str] = set()
        per_pair: dict[str, list[float]] = {pk: [] for pk, _, _ in PAIR_TYPES}
        for sl in slices.values():
            for pk, _, _ in PAIR_TYPES:
                mem = pair_members(sl, pk)
                if not mem:
                    continue
                wrong_iid, correct_iid = mem
                wr, wc = rows.get(wrong_iid), rows.get(correct_iid)
                if not wr or not wc:
                    continue
                ws, wm = score_from_row(wr)
                cs, cm = score_from_row(wc)
                if ws is None or cs is None:
                    continue
                modes.add(wm if wm != "missing" else cm)
                per_pair[pk].append(preference(ws, cs))
        entry: dict = {
            "score_mode": "+".join(sorted(modes)) if modes else "none",
            "family": verifier_family(slug),
            "display_name": verifier_display_name(slug),
            "pairs": {},
        }
        for pk, wrong_l, correct_l in PAIR_TYPES:
            oc = per_pair[pk]
            m, lo, hi = cluster_bootstrap(oc)
            entry["pairs"][pk] = {
                "label": f"{wrong_l} vs {correct_l}",
                "p_wrong_prefers": m,
                "ci95": [lo, hi],
                "n_pairs": len(oc),
            }
        by_verifier[slug] = entry
    return by_verifier, structural


def legacy_best_of_n_footnote() -> dict:
    """Compact legacy 18-base best-of-N (dose3 PI_ok) for appendix only."""
    if LEGACY_JSON.is_file():
        return json.loads(LEGACY_JSON.read_text())
    return {"note": "Run prior commit 97d0b79 for full best-of-N table; underpowered (n=18, ×1000 in 3)."}


def write_figure(by_verifier: dict[str, dict]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    pk = "x1000_vs_inv"
    items = [
        (
            verifier_display_name(v),
            d["pairs"][pk]["p_wrong_prefers"],
            d["pairs"][pk]["n_pairs"],
            d.get("family", "other"),
        )
        for v, d in by_verifier.items()
        if v in CANONICAL_VERIFIERS
        and pk in d.get("pairs", {})
        and d["pairs"][pk]["n_pairs"] >= 1
        and d["pairs"][pk]["p_wrong_prefers"] == d["pairs"][pk]["p_wrong_prefers"]
    ]
    items.sort(key=lambda t: (FAMILY_ORDER.get(t[3], 9), -t[1], t[0]))
    if not items:
        return
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, max(3.5, 0.32 * len(items))))
    vals = [x[1] for x in items]
    labels = [f"{x[0]} (n={x[2]})" for x in items]
    ax.barh(range(len(items)), vals, color=[FAMILY_COLORS.get(x[3], "#888") for x in items])
    ax.axvline(0.5, color="#888", linestyle="--", linewidth=0.8, label="chance")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("P(score(wrong) ≥ score(correct)); ties = 0.5")
    ax.set_title("T13 pair (1): E1-unit-claim ×1000 vs INV-unit natural")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=160)
    plt.close(fig)


def fmt_cell(d: dict) -> str:
    p = d["p_wrong_prefers"]
    if p != p:
        return "—"
    lo, hi = d["ci95"]
    return f"{p:.3f} [{lo:.3f}, {hi:.3f}] (n={d['n_pairs']})"


def main() -> None:
    pi_stats = t7_pi_sample_stats()
    slices = main_dose_slices()
    by_verifier, structural = analyze_pairwise(slices)
    n_x1000 = sum(1 for s in slices.values() if s.e1_unit_x1000)

    payload = {
        "design": "pairwise_preference",
        "cohort": {
            "valid_main_dose_bases": len(slices),
            "e1_unit_claim_x1000_instances": n_x1000,
            "t7_pi_sample": pi_stats,
            "t7_generator_note": "All valid E1-unit×1000 rows used; 30/30 PI sample validates generator.",
            "structural_pairs_eligible": structural,
            "tie_rule": "P(wrong≥correct): 1 if wrong>correct, 0 if wrong<correct, 0.5 if tie",
            "bootstrap": f"cluster over bases, {N_BOOT} resamples, seed {BOOT_SEED}",
        },
        "pair_types": [
            {"key": pk, "wrong": w, "correct": c} for pk, w, c in PAIR_TYPES
        ],
        "by_verifier": by_verifier,
        "appendix_legacy_best_of_n": legacy_best_of_n_footnote(),
    }

    lines = [
        "# T13 — pairwise preference (selection harm)",
        "",
        "- **Cohort:** all **valid main DOSE** bases (`instances_main.jsonl`).",
        "- **E1-unit ×1000:** **all** valid `E1-unit-claim` / `E1-unit-evid` rows in `data/t7/instances_e1_unit.jsonl` "
        f"(**{n_x1000}** claim on main DOSE); generator validated by **{pi_stats.get('pi_ok_y', 0)}/{pi_stats.get('labeled', 0)}** PI sample (`qc/t7_PI_ok_labels.csv`).",
        "- **INV-unit natural:** `rule_natural_unit_conversion_label` + `effective_unit_natural_y` (same gate as T9).",
        "- **Metric:** per base pair, contribute **P(wrong ≥ correct)** — 1 if score(wrong)>score(correct), "
        "**0.5 on ties**, 0 if lower. **Cluster bootstrap** over bases (95% CI).",
        "- **Scores:** continuous where logged; else LLM **verdict** (PASS=1, FAIL=0) and **logprob** when present.",
        "",
        f"- Main DOSE bases: **{len(slices)}**. Structural pair counts (both slices exist): "
        + ", ".join(f"({w} vs {c}) **{structural[pk]}**" for pk, w, c in PAIR_TYPES)
        + ".",
        "",
        "## Pairwise table (19 verifiers; pairs 1, 1′, 2′)",
        "",
        "Cells: **P(wrong ≥ correct)** [95% cluster-bootstrap CI] **(n=…)**; **ties counted as 0.5**.",
        "",
        "| model | family | mode | (1) ×1000 vs INV nat | (1′) ×1000 vs INV all | (2′) evid×1000 vs C0 |",
        "|---|---|---|---|---|---|",
    ]
    for v, d in sorted(
        by_verifier.items(),
        key=lambda t: (
            FAMILY_ORDER.get(t[1].get("family", "other"), 9),
            -(t[1]["pairs"].get("x1000_vs_inv", {}).get("p_wrong_prefers") or -1),
        ),
    ):
        if v not in CANONICAL_VERIFIERS:
            continue
        p1 = d["pairs"].get("x1000_vs_inv", {})
        p1p = d["pairs"].get("x1000_vs_inv_all", {})
        p2e = d["pairs"].get("evid_x1000_vs_c0", {})
        name = d.get("display_name") or verifier_display_name(v)
        lines.append(
            f"| {name} | {d.get('family', 'other')} | {d['score_mode']} | "
            f"{fmt_cell(p1) if p1.get('n_pairs') else '—'} | "
            f"{fmt_cell(p1p) if p1p.get('n_pairs') else '—'} | "
            f"{fmt_cell(p2e) if p2e.get('n_pairs') else '—'} |"
        )
    lines.extend(
        [
            "",
            "## Other pairs (supplementary)",
            "",
            "| model | (2) ×1000 vs C0 | (3) E1×2 vs INV |",
            "|---|---|---|",
        ]
    )
    for v, d in sorted(
        by_verifier.items(),
        key=lambda t: (
            FAMILY_ORDER.get(t[1].get("family", "other"), 9),
            t[0],
        ),
    ):
        if v not in CANONICAL_VERIFIERS:
            continue
        p2 = d["pairs"].get("x1000_vs_c0", {})
        p3 = d["pairs"].get("e1x2_vs_inv", {})
        name = d.get("display_name") or verifier_display_name(v)
        lines.append(
            f"| {name} | {fmt_cell(p2) if p2.get('n_pairs') else '—'} | "
            f"{fmt_cell(p3) if p3.get('n_pairs') else '—'} |"
        )

    write_figure(by_verifier)
    if OUT_FIG.is_file():
        lines.extend(["", f"**Figure (pair 1):** `{OUT_FIG.relative_to(ROOT)}`", ""])

    leg = legacy_best_of_n_footnote()
    lines.extend(
        [
            "## Appendix — superseded best-of-N (footnote only)",
            "",
            "The prior **18-base** `PI_ok=Y` best-of-N argmax design was underpowered (×1000 in only 3 bases) "
            "and its **tie → lower rank** rule biased **binary** LLM judges. "
            "See commit `97d0b79` / `notes/t13_best_of_n.json` for that exploratory table; "
            "**do not use for inference.** Primary T13 estimand is pairwise above.",
            "",
        ]
    )
    if isinstance(leg, dict) and leg.get("by_verifier"):
        v1 = leg["by_verifier"].get("v1_medscore", {})
        lines.append(
            f"- Legacy example: v1_medscore P(select wrong) ≈ "
            f"{v1.get('p_select_wrong', '—')} on n={v1.get('n_bases_selected', '?')} bases."
        )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT_MD} ({len(by_verifier)} verifiers)")


if __name__ == "__main__":
    main()
