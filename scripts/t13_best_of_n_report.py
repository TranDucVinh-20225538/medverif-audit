#!/usr/bin/env python3
"""T13: best-of-N selection harm on human-verified DOSE bases (existing CPU scores)."""

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
from t4_eco_compare import apply_pi_override, load_pi_label_paths  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

CPU = ROOT / "data/v3/instances_cpu_early.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
DOSE3 = ROOT / "qc/dose3_labels.csv"
T7_PI = ROOT / "qc/t7_PI_ok_labels.csv"
T6A = ROOT / "notes/t6a_eco_checkers.json"
CLASSIFIED = ROOT / "data/t4/eco_classified.jsonl"
OUT_MD = ROOT / "results/tables/t13_best_of_n.md"
OUT_JSON = ROOT / "notes/t13_best_of_n.json"
OUT_FIG = ROOT / "results/figures/t13_best_of_n_wrong_select.png"

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

CORRECT_ECO = frozenset({"exact_verbatim", "exact_surface_variant", "frequency_rephrased"})
N_BOOT = 2000
BOOT_SEED = 42

# Tie-break: higher rank = lower preference (conservative on ties).
RANK = {
    "C0": 0,
    "INV_unit": 1,
    "T4_eco": 2,
    "E1x2_claim": 3,
    "E1x2_evid": 4,
    "E1_unit_x1000": 5,
}
WRONG_KINDS = frozenset({"E1x2_claim", "E1x2_evid", "E1_unit_x1000"})


@dataclass(frozen=True)
class Cand:
    base_id: str
    instance_id: str
    kind: str

    @property
    def rank(self) -> int:
        return RANK[self.kind]

    @property
    def wrong(self) -> bool:
        return self.kind in WRONG_KINDS


def inv_span_before(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    return str(claim.get("span_before") or row.get("claim_span") or "")


def load_dose3() -> dict[str, dict]:
    with DOSE3.open(encoding="utf-8-sig") as handle:
        return {r["base_id"]: r for r in csv.DictReader(handle)}


def verified_bases(labels: dict[str, dict]) -> set[str]:
    return {
        bid
        for bid, r in labels.items()
        if (r.get("PI_ok") or "").strip().upper() == "Y"
    }


def t7_pi_ok_ids() -> set[str]:
    if not T7_PI.is_file():
        return set()
    out: set[str] = set()
    with T7_PI.open(encoding="utf-8-sig", newline="") as handle:
        for r in csv.DictReader(handle):
            iid = (r.get("instance_id") or "").strip()
            if iid and (r.get("PI_ok") or "").strip().upper() == "Y":
                out.add(iid)
    return out


def t4_correct_by_base(bases: set[str]) -> dict[str, list[str]]:
    eco_labels = load_pi_label_paths(
        [ROOT / "qc/eco_PI_ok_labels.csv", ROOT / "qc/eco2_PI_ok_labels.csv"]
    )
    out: dict[str, list[str]] = {b: [] for b in bases}
    for line in CLASSIFIED.open():
        if not line.strip():
            continue
        row = json.loads(line)
        bid = row.get("base_id")
        if bid not in bases:
            continue
        key = (row["task_id"], row["answerer_id"])
        if key not in eco_labels:
            continue
        cat = apply_pi_override(
            row["task_id"],
            row["answerer_id"],
            row.get("eco_category_final") or row.get("eco_category") or "",
            eco_labels,
        )
        if cat not in CORRECT_ECO:
            continue
        iid = f"{row['task_id']}__{row['answerer_id']}__eco"
        out[bid].append(iid)
    return out


def build_candidates(
    bases: set[str],
    labels: dict[str, dict],
    t7_pi: set[str],
    t4_by_base: dict[str, list[str]],
) -> dict[str, list[Cand]]:
    cpu = read_jsonl(CPU)
    t7 = read_jsonl(T7)
    by_base: dict[str, list[Cand]] = {b: [] for b in bases}

    for r in cpu:
        bid = r.get("base_id")
        if bid not in bases or not r.get("valid", True) or r.get("type") != "DOSE":
            continue
        lab = labels.get(bid, {})
        cond, mag = r.get("condition"), r.get("magnitude")
        if cond == "C0" and (lab.get("C0_ok") or "").strip().upper() == "Y":
            by_base[bid].append(Cand(bid, r["instance_id"], "C0"))
        elif cond == "E1-claim" and mag == "x2" and (lab.get("E1x2_ok") or "").strip().upper() == "Y":
            by_base[bid].append(Cand(bid, r["instance_id"], "E1x2_claim"))
        elif cond == "E1-evid" and mag == "x2" and (lab.get("E1x2_ok") or "").strip().upper() == "Y":
            by_base[bid].append(Cand(bid, r["instance_id"], "E1x2_evid"))
        elif cond == "INV-claim" and mag == "unit_conversion":
            orig = inv_span_before(r)
            rule_y = bool(rule_natural_unit_conversion_label(orig))
            if effective_unit_natural_y(bid, rule_y):
                by_base[bid].append(Cand(bid, r["instance_id"], "INV_unit"))

    for r in t7:
        bid = r.get("base_id")
        if bid not in bases or not r.get("valid", True):
            continue
        if r.get("condition") == "E1-unit-claim" and r.get("magnitude") == "x1000":
            if r["instance_id"] in t7_pi:
                by_base[bid].append(Cand(bid, r["instance_id"], "E1_unit_x1000"))

    for bid in bases:
        for iid in t4_by_base.get(bid, []):
            by_base[bid].append(Cand(bid, iid, "T4_eco"))

    return {b: cands for b, cands in by_base.items() if cands}


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
    """Return (selection_score, mode) where mode is continuous|binary|logprob."""
    for key in ("score", "released_parser_score", "parser_score"):
        if key in row and row[key] is not None:
            try:
                return float(row[key]), "continuous"
            except (TypeError, ValueError):
                pass
    for key in ("mean_logprob", "logprob", "ll"):
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


def pick_argmax(cands: list[Cand], scores: dict[str, dict]) -> Cand | None:
    scored: list[tuple[Cand, float]] = []
    for c in cands:
        row = scores.get(c.instance_id)
        if not row:
            continue
        val, _ = score_from_row(row)
        if val is None:
            continue
        scored.append((c, val))
    if len(scored) < 2:
        return None
    best = max(scored, key=lambda t: (t[1], t[0].rank))
    return best[0]


def bootstrap_mean(values: list[float], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> tuple[float, float, float]:
    if not values:
        return float("nan"), float("nan"), float("nan")
    n = len(values)
    mean = sum(values) / n
    rng = random.Random(seed)
    boots = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(n_boot))
    lo = boots[int(0.025 * n_boot)]
    hi = boots[int(0.975 * n_boot)]
    return mean, lo, hi


def bootstrap_rate(flags: list[int], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> tuple[float, float, float]:
    return bootstrap_mean([float(x) for x in flags], n_boot=n_boot, seed=seed)


def analyze_verifier(
    slug: str,
    cands_by_base: dict[str, list[Cand]],
) -> dict:
    rows = merged_score_rows(slug)
    modes: set[str] = set()
    wrong_flags: list[int] = []
    x1000_flags: list[int] = []
    x1000_den = 0
    inv_below_flags: list[int] = []
    inv_below_den = 0
    reward_diffs: list[float] = []

    for bid, cands in sorted(cands_by_base.items()):
        picked = pick_argmax(cands, rows)
        if picked is None:
            continue
        for c in cands:
            row = rows.get(c.instance_id)
            if row:
                _, mode = score_from_row(row)
                if mode != "missing":
                    modes.add(mode)

        wrong_flags.append(int(picked.wrong))
        has_x1000 = any(c.kind == "E1_unit_x1000" for c in cands)
        if has_x1000:
            x1000_den += 1
            x1000_flags.append(int(picked.kind == "E1_unit_x1000"))

        inv = next((c for c in cands if c.kind == "INV_unit"), None)
        wrong_scored: list[float] = []
        inv_score = None
        for c in cands:
            row = rows.get(c.instance_id)
            if not row:
                continue
            val, _ = score_from_row(row)
            if val is None:
                continue
            if c.kind == "INV_unit":
                inv_score = val
            elif c.wrong:
                wrong_scored.append(val)
        if inv and inv_score is not None and wrong_scored:
            inv_below_den += 1
            inv_below_flags.append(int(inv_score < max(wrong_scored)))

        inv_c = next((c for c in cands if c.kind == "INV_unit"), None)
        x1k = next((c for c in cands if c.kind == "E1_unit_x1000"), None)
        if inv_c and x1k:
            ri, _ = score_from_row(rows.get(inv_c.instance_id, {}))
            rx, _ = score_from_row(rows.get(x1k.instance_id, {}))
            if ri is not None and rx is not None:
                reward_diffs.append(ri - rx)

    n_sel = len(wrong_flags)
    p_wrong, w_lo, w_hi = bootstrap_rate(wrong_flags) if wrong_flags else (float("nan"), float("nan"), float("nan"))
    p_x1k, x_lo, x_hi = (
        bootstrap_rate(x1000_flags)
        if x1000_flags
        else (float("nan"), float("nan"), float("nan"))
    )
    p_inv, i_lo, i_hi = (
        bootstrap_rate(inv_below_flags)
        if inv_below_flags
        else (float("nan"), float("nan"), float("nan"))
    )
    r_mean, r_lo, r_hi = bootstrap_mean(reward_diffs) if reward_diffs else (float("nan"), float("nan"), float("nan"))

    return {
        "score_mode": "+".join(sorted(modes)) if modes else "none",
        "n_bases_selected": n_sel,
        "p_select_wrong": p_wrong,
        "p_select_wrong_ci": [w_lo, w_hi],
        "p_select_x1000": p_x1k,
        "p_select_x1000_ci": [x_lo, x_hi],
        "n_x1000_present": x1000_den,
        "p_inv_below_wrong": p_inv,
        "p_inv_below_wrong_ci": [i_lo, i_hi],
        "n_inv_vs_wrong": inv_below_den,
        "reward_inv_minus_x1000": r_mean,
        "reward_inv_minus_x1000_ci": [r_lo, r_hi],
        "n_reward_pairs": len(reward_diffs),
    }


def write_figure(table: dict[str, dict]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    items = [
        (v, d["p_select_wrong"])
        for v, d in table.items()
        if d.get("n_bases_selected", 0) >= 5 and d.get("p_select_wrong") == d.get("p_select_wrong")
    ]
    items.sort(key=lambda t: t[1], reverse=True)
    items = items[:20]
    if not items:
        return
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, max(4, 0.35 * len(items))))
    labels = [x[0] for x in items]
    vals = [x[1] for x in items]
    ax.barh(range(len(items)), vals, color="#c44e52")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("P(select WRONG candidate | argmax score, tie → lower rank)")
    ax.set_title("T13 best-of-N selection harm (human-verified DOSE bases)")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=160)
    plt.close(fig)


def main() -> None:
    labels = load_dose3()
    bases = verified_bases(labels)
    t7_pi = t7_pi_ok_ids()
    t4_by_base = t4_correct_by_base(bases)
    cands_by_base = build_candidates(bases, labels, t7_pi, t4_by_base)

    payload: dict = {
        "cohort": {
            "dose3_PI_ok_bases": len(bases),
            "bases_with_candidates": len(cands_by_base),
            "candidate_kinds": list(RANK.keys()),
            "tie_break": "max score; ties → higher rank index (conservative)",
        },
        "by_verifier": {},
    }

    table: dict[str, dict] = {}
    for slug in all_verifier_slugs():
        stats = analyze_verifier(slug, cands_by_base)
        if stats["n_bases_selected"] == 0:
            continue
        table[slug] = stats

    payload["by_verifier"] = table

    def fmt_p(x: float | None, ci: list[float] | None, n: int) -> str:
        if x != x:
            return "—"
        ci_s = ""
        if ci and ci[0] == ci[0]:
            ci_s = f" [{ci[0]:.3f}, {ci[1]:.3f}]"
        return f"{x:.3f}{ci_s} (n={n})"

    lines = [
        "# T13 — best-of-N selection harm",
        "",
        "- **Cohort:** DOSE bases with `PI_ok=Y` in `qc/dose3_labels.csv`.",
        "- **Pool per base:** human-gated C0, INV-unit (natural), E1×2 claim+evid, "
        "E1-unit-claim×1000 (T7 PI_ok), T4 eco human-correct answers when labeled.",
        "- **Selection:** argmax verifier score; **ties → lower-ranked candidate** (higher rank index).",
        "- **Scores:** continuous `score` / parser fields when present; else PASS=1 / FAIL=0.",
        "",
        f"- Bases in cohort: **{len(bases)}**; with ≥1 candidate: **{len(cands_by_base)}**.",
        "",
        "## Selection harm",
        "",
        "| verifier | score mode | (a) P(wrong) | (b) P(×1000) | (c) P(inv below wrong) |",
        "|---|---|---:|---:|---:|",
    ]
    for v, d in sorted(table.items(), key=lambda t: -(t[1].get("p_select_wrong") or 0)):
        lines.append(
            f"| {v} | {d['score_mode']} | "
            f"{fmt_p(d['p_select_wrong'], d['p_select_wrong_ci'], d['n_bases_selected'])} | "
            f"{fmt_p(d['p_select_x1000'], d['p_select_x1000_ci'], d['n_x1000_present'])} | "
            f"{fmt_p(d['p_inv_below_wrong'], d['p_inv_below_wrong_ci'], d['n_inv_vs_wrong'])} |"
        )

    lines.extend(
        [
            "",
            "## Reward view (INV-unit − ×1000 wrong), paired by base",
            "",
            "| verifier | mean Δscore [95% CI] | n pairs |",
            "|---|---:|---:|",
        ]
    )
    for v, d in sorted(table.items(), key=lambda t: t[0]):
        m = d["reward_inv_minus_x1000"]
        ci = d["reward_inv_minus_x1000_ci"]
        if m != m:
            cell = "—"
        else:
            cell = f"{m:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]"
        lines.append(f"| {v} | {cell} | {d['n_reward_pairs']} |")

    if OUT_FIG.exists() or True:
        write_figure(table)
        if OUT_FIG.is_file():
            lines.extend(["", f"Figure: `{OUT_FIG.relative_to(ROOT)}`", ""])

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT_MD} ({len(table)} verifiers)")


if __name__ == "__main__":
    main()
