#!/usr/bin/env python3
"""T19 scale sweep report: card-aligned QI/NS/US/C0 + optional E2/Rephrase."""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import N_BOOT, SEED, _c0_pass_bases, _groups, _parsed, bootstrap_rate  # noqa: E402
from review_filters import effective_unit_natural_y  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402
import t14_t3_filter_report as filt  # noqa: E402

INST = ROOT / "data/t19/instances_t19.jsonl"
RAW = ROOT / "results/raw/t19"
OUT_MD = ROOT / "notes/t19_scale_sweep.md"
OUT_JSON = ROOT / "notes/t19_scale_sweep.json"
OUT_FIG = ROOT / "results/figures/t19_scale.png"

MODELS = [
    {"slug": "llama32_1b", "label": "1B (local)", "params_b": 1.0, "path": RAW / "llama32_1b_instruct.jsonl"},
    {"slug": "llama32_3b", "label": "3B (local)", "params_b": 3.0, "path": RAW / "llama32_3b_instruct.jsonl"},
    {"slug": "llama31_8b_local", "label": "8B (local)", "params_b": 8.0, "path": RAW / "llama31_8b_instruct.jsonl"},
    {"slug": "llama31_8b_api", "label": "8B (API)", "params_b": 8.0, "path": None, "extra_paths": True},
    {"slug": "llama33_70b_api", "label": "70B (API Llama-3.3)", "params_b": 70.0, "path": None, "api70": True},
]

MAIN = ROOT / "data/v3/instances_main.jsonl"
V4_MAIN = ROOT / "results/raw/v4_ragas_nli.llama.jsonl"
V4_T14 = ROOT / "results/raw/t14/v4_ragas_nli.jsonl"
T17_V4_LLAMA = ROOT / "results/raw/t17/v4_ragas_nli.llama.jsonl"
T17_V6_8B = ROOT / "results/raw/t17/v6_ragas_llama31_8b.jsonl"
T14_V6_8B = ROOT / "results/raw/t14/v6_ragas_llama31_8b.jsonl"
API8B_PATHS = [
    ROOT / "results/raw/t7/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/e2_main/v6_ragas_llama31_8b.jsonl",
    T17_V6_8B,
    T14_V6_8B,
]
API70_PATHS = [V4_T14, T17_V4_LLAMA]
LOCAL_SLUGS = ("llama32_1b", "llama32_3b", "llama31_8b_local")
T14_FAMILIES = ("spacing", "unit_spell", "symbol_micro")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def load_scores(path: Path | None, extra_paths: list[Path] | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    paths: list[Path] = []
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


def pol_main_instances() -> list[dict]:
    """POLARITY main-pack rows for Rephrase (not in instances_t19.jsonl)."""
    out: list[dict] = []
    for r in read_jsonl(MAIN):
        if not r.get("valid", True) or r.get("type") != "POLARITY" or r.get("subset") != "main":
            continue
        cond, mag = r.get("condition"), r.get("magnitude")
        if cond == "C0" and mag == "none":
            out.append({**r, "t19_pack": "main_pol"})
        elif cond == "INV-claim" and mag == "rephrase":
            out.append({**r, "t19_pack": "main_pol"})
    return out


def join_pol_scores(pol_instances: list[dict], scores: dict[str, dict]) -> list[dict]:
    return join_instances(pol_instances, scores)


def _pol_c0_pass_bases(pol_joined: list[dict]) -> set[str]:
    return {
        r["base_id"]
        for r in pol_joined
        if r.get("condition") == "C0" and r.get("verdict") == "PASS"
    }


def join_instances(instances: list[dict], scores: dict[str, dict]) -> list[dict]:
    joined: list[dict] = []
    for inst in instances:
        sc = scores.get(inst["instance_id"])
        if not sc:
            continue
        v = sc.get("verdict")
        if v not in ("PASS", "FAIL"):
            continue
        row = dict(inst)
        row["verdict"] = v
        row["score"] = sc.get("score")
        joined.append(row)
    return joined


def _fail_groups(rows: list[dict], keep) -> list[tuple[int, int]]:
    by: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if not keep(row) or not _parsed(row):
            continue
        by[row["base_id"]].append(row)
    out: list[tuple[int, int]] = []
    for g in by.values():
        out.append((sum(1 for r in g if r["verdict"] == "FAIL"), len(g)))
    return out


def _natural_inv(r: dict) -> bool:
    if r.get("condition") != "INV-claim" or r.get("magnitude") != "unit_conversion":
        return False
    if r.get("t19_pack") != "main_dose":
        return False
    orig = filt.inv_span_before(r)
    return effective_unit_natural_y(r["base_id"], bool(rule_natural_unit_conversion_label(orig)))


def _pack_stat(groups: list[tuple[int, int]]) -> dict:
    s = bootstrap_rate(groups)
    return {
        "rate": s["rate"],
        "ci_lo": s["lo"],
        "ci_hi": s["hi"],
        "n": s["den"],
        "n_pass_or_fail": s["num"],
        "n_bases": s["n_bases"],
    }


def metrics_card(
    joined: list[dict],
    *,
    cond_bases: set[str] | None = None,
    pol_joined: list[dict] | None = None,
) -> dict:
    main = [r for r in joined if r.get("t19_pack") == "main_dose"]
    cond = cond_bases if cond_bases is not None else _c0_pass_bases(main)
    if cond_bases is not None:
        c0_stat = _pack_stat(_groups(main, lambda r: r["condition"] == "C0" and r["base_id"] in cond_bases))
    else:
        c0_stat = _pack_stat(_groups(main, lambda r: r["condition"] == "C0"))

    qi_all = _pack_stat(
        _groups(
            main,
            lambda r: r["base_id"] in cond
            and r["condition"] == "INV-claim"
            and r.get("magnitude") == "unit_conversion",
        )
    )
    qi_nat = _pack_stat(
        _groups(
            main,
            lambda r: r["base_id"] in cond and _natural_inv(r),
        )
    )

    def ns_claim_main(r: dict) -> bool:
        return (
            r["base_id"] in cond
            and r.get("t19_pack") == "main_dose"
            and r.get("condition") == "E1-claim"
            and r.get("magnitude") in ("x2", "x10")
        )

    def ns_evid_main(r: dict) -> bool:
        return (
            r["base_id"] in cond
            and r.get("t19_pack") == "main_dose"
            and r.get("condition") == "E1-evid"
            and r.get("magnitude") in ("x2", "x10")
        )

    t17 = [r for r in joined if r.get("t19_pack") == "t17"]
    ns_claim_down2 = _pack_stat(_fail_groups(t17, lambda r: r["base_id"] in cond and r["condition"] == "E1-down2"))
    ns_claim_down10 = _pack_stat(_fail_groups(t17, lambda r: r["base_id"] in cond and r["condition"] == "E1-down10"))
    ns_claim = _pack_stat(_fail_groups(joined, ns_claim_main))
    ns_evid = _pack_stat(_fail_groups(joined, ns_evid_main))

    unit = [r for r in joined if r.get("t19_pack") in ("main_e1_unit", "main_dose", "t17")]

    def us_claim_x1000(r: dict) -> bool:
        return (
            r["base_id"] in cond
            and r.get("t19_pack") == "main_e1_unit"
            and r.get("condition") == "E1-unit-claim"
            and r.get("magnitude") == "x1000"
        )

    def us_evid_x1000(r: dict) -> bool:
        return (
            r["base_id"] in cond
            and r.get("t19_pack") == "main_e1_unit"
            and r.get("condition") == "E1-unit-evid"
            and r.get("magnitude") == "x1000"
        )

    def us_unit_down(r: dict) -> bool:
        return r["base_id"] in cond and r.get("t19_pack") == "t17" and r.get("condition") == "E1-unit-down"

    us_claim_x1k = _pack_stat(_fail_groups(unit, us_claim_x1000))
    us_evid_x1k = _pack_stat(_fail_groups(unit, us_evid_x1000))
    us_unit_down_stat = _pack_stat(_fail_groups(unit, us_unit_down))

    e2_rows = [r for r in joined if r.get("condition") == "E2"]
    e2_stat = _pack_stat(_groups(joined, lambda r: r.get("condition") == "E2")) if e2_rows else None

    pol = pol_joined or []
    pol_cond = _pol_c0_pass_bases(pol)
    pol_repr_rows = [
        r
        for r in pol
        if r.get("condition") == "INV-claim"
        and r.get("magnitude") == "rephrase"
        and r["base_id"] in pol_cond
    ]
    rephrase_stat = (
        _pack_stat(
            _groups(
                pol,
                lambda r: r["base_id"] in pol_cond
                and r.get("condition") == "INV-claim"
                and r.get("magnitude") == "rephrase",
            )
        )
        if pol_repr_rows
        else None
    )

    t14_rows = [r for r in joined if r.get("t19_pack") == "t14" and r.get("condition") == "T14-repr-claim"]
    t14_repr_stat = (
        _pack_stat(
            _groups(
                joined,
                lambda r: r.get("t19_pack") == "t14" and r.get("condition") == "T14-repr-claim",
            )
        )
        if t14_rows
        else None
    )
    t14_by_family: dict[str, dict] = {}
    for fam in T14_FAMILIES:
        fam_rows = [r for r in t14_rows if (r.get("t14_family") or r.get("magnitude")) == fam]
        if not fam_rows:
            continue
        st = _pack_stat(
            _groups(
                joined,
                lambda r, family=fam: r.get("t19_pack") == "t14"
                and r.get("condition") == "T14-repr-claim"
                and (r.get("t14_family") or r.get("magnitude")) == family,
            )
        )
        if st.get("n", 0) > 0:
            t14_by_family[fam] = st

    inv_bases_all = {
        r["base_id"]
        for r in main
        if r["base_id"] in cond
        and r["condition"] == "INV-claim"
        and r.get("magnitude") == "unit_conversion"
    }
    inv_bases_nat = {r["base_id"] for r in main if r["base_id"] in cond and _natural_inv(r)}

    return {
        "n_c0_pass_bases": len(cond),
        "n_bases_qi_all": len(inv_bases_all),
        "n_bases_qi_nat": len(inv_bases_nat),
        "C0": c0_stat,
        "QI_all": qi_all,
        "QI_nat": qi_nat,
        "NS_claim": ns_claim,
        "NS_evid": ns_evid,
        "NS_claim_T17_down2": ns_claim_down2,
        "NS_claim_T17_down10": ns_claim_down10,
        "US_claim_x1000": us_claim_x1k,
        "US_evid_x1000": us_evid_x1k,
        "US_T17_unit_down": us_unit_down_stat,
        "n_pol_c0_pass_bases": len(pol_cond),
        "E2_PASS": e2_stat,
        "Rephrase_PASS": rephrase_stat,
        "T14_repr_PASS": t14_repr_stat,
        "T14_repr_by_family": t14_by_family,
    }


def fmt_pct(stat: dict | None) -> str:
    if not stat or stat.get("rate") is None:
        return "NA"
    lo, hi = stat.get("ci_lo"), stat.get("ci_hi")
    body = f"{100 * stat['rate']:.1f}%"
    if lo is not None and hi is not None:
        body += f" [{100 * lo:.1f}, {100 * hi:.1f}]"
    n = stat.get("n", 0)
    nb = stat.get("n_bases", 0)
    return f"{body} (n={n}, bases={nb})"


def agreement_8b(local: dict[str, dict], api: dict[str, dict], instances: list[dict]) -> dict:
    rng = random.Random(SEED)
    pairs: list[tuple[int, int]] = []
    for r in instances:
        iid = r["instance_id"]
        a, b = local.get(iid), api.get(iid)
        if not a or not b:
            continue
        pa, pb = is_pass(a), is_pass(b)
        if pa is None or pb is None:
            continue
        pairs.append((int(pa == pb), 1))
    if not pairs:
        return {"n": 0, "agreement": None, "ci_lo": None, "ci_hi": None}
    point = sum(p for p, _ in pairs) / len(pairs)
    if len(pairs) < 2:
        return {"n": len(pairs), "agreement": point, "ci_lo": None, "ci_hi": None}
    m = len(pairs)
    pts = []
    for _ in range(N_BOOT):
        agree = sum(pairs[rng.randrange(m)][0] for _ in range(m))
        pts.append(agree / m)
    pts.sort()
    return {
        "n": m,
        "agreement": point,
        "ci_lo": pts[int(0.025 * len(pts))],
        "ci_hi": pts[int(0.975 * len(pts)) - 1],
    }


def local_c0_pass_bases(joined: list[dict]) -> set[str]:
    main = [r for r in joined if r.get("t19_pack") == "main_dose"]
    return _c0_pass_bases(main)


def main() -> None:
    instances = read_jsonl(INST)
    if not instances:
        raise SystemExit(f"missing instances: {INST}")

    pol_instances = pol_main_instances()
    api70 = load_scores(V4_MAIN, API70_PATHS)
    api8b = load_scores(None, API8B_PATHS)

    model_rows = []
    local_joined: dict[str, list[dict]] = {}
    for spec in MODELS:
        if spec.get("api70"):
            scores = api70
        elif spec.get("extra_paths"):
            scores = api8b
        else:
            scores = load_scores(spec["path"])
        joined = join_instances(instances, scores)
        pol_joined = join_pol_scores(pol_instances, scores)
        m = metrics_card(joined, pol_joined=pol_joined)
        row = {
            "slug": spec["slug"],
            "label": spec["label"],
            "params_b": spec["params_b"],
            "n_scored": len(joined),
            "n_instances_cohort": len(instances),
            **m,
        }
        if spec["slug"] == "llama31_8b_local":
            row["api8b_agreement"] = agreement_8b(scores, api8b, instances)
        if spec["slug"] in LOCAL_SLUGS:
            local_joined[spec["slug"]] = joined
        model_rows.append(row)

    intersection: set[str] | None = None
    if all(s in local_joined for s in LOCAL_SLUGS):
        sets = [local_c0_pass_bases(local_joined[s]) for s in LOCAL_SLUGS]
        if all(sets):
            intersection = set.intersection(*sets)
    intersection_rows: list[dict] = []
    if intersection:
        for spec in MODELS:
            if spec["slug"] not in LOCAL_SLUGS:
                continue
            if spec.get("api70") or spec.get("extra_paths"):
                continue
            scores = load_scores(spec["path"])
            joined = local_joined[spec["slug"]]
            pol_joined = join_pol_scores(pol_instances, scores)
            m = metrics_card(joined, cond_bases=intersection, pol_joined=pol_joined)
            intersection_rows.append(
                {
                    "slug": spec["slug"],
                    "label": spec["label"],
                    "params_b": spec["params_b"],
                    "n_intersection_c0_pass_bases": len(intersection),
                    **m,
                }
            )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "instances": len(instances),
        "bootstrap": {"n": N_BOOT, "seed": SEED, "method": "cluster by base_id"},
        "definitions": {
            "C0": "P(PASS | C0) on main_dose",
            "QI_all": "P(PASS | INV-unit, | C0 PASS) all conversions",
            "QI_nat": "P(PASS | INV-unit natural per nat3, | C0 PASS)",
            "NS_claim": "P(FAIL | E1-claim x2/x10 main, | C0 PASS)",
            "NS_evid": "P(FAIL | E1-evid x2/x10 main, | C0 PASS)",
            "NS_claim_T17_down2/down10": "P(FAIL | T17 E1-down2 or E1-down10, | C0 PASS)",
            "US_claim_x1000": "P(FAIL | E1-unit-claim x1000, | C0 PASS)",
            "US_evid_x1000": "P(FAIL | E1-unit-evid x1000, | C0 PASS)",
            "US_T17_unit_down": "P(FAIL | T17 E1-unit-down, | C0 PASS)",
            "Rephrase_PASS": "P(PASS | POL INV-claim rephrase, | POL C0 PASS) main pack",
            "T14_repr_PASS": "P(PASS | T14-repr-claim) t14 pack; by_family in T14_repr_by_family",
        },
        "models": model_rows,
        "intersection_c0_pass_bases": sorted(intersection) if intersection else [],
        "intersection_local_models": intersection_rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T19 scale sweep (RAGAS-NLI)",
        "",
        f"Cohort: `{INST.relative_to(ROOT)}` (n={len(instances)} instances). "
        "Cluster-bootstrap by `base_id`, seed 42, 1000 resamples (matches `compute_paper_numbers.py`).",
        "",
        "**Shared conditioning:** `n_c0_pass_bases` = bases with C0 PASS on main_dose (per model). "
        "QI/NS/US use that base set; row `bases=` is clustered units contributing to each metric.",
        "",
        "| Model | C0 | QI all | QI nat | NS claim | NS evid | NS ÷2 (T17) | NS ÷10 (T17) | "
        "US claim ×1k | US evid ×1k | US unit÷ (T17) | Rephrase (POL) | T14_repr |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in model_rows:
        lines.append(
            f"| {r['label']} | {fmt_pct(r['C0'])} | {fmt_pct(r['QI_all'])} | {fmt_pct(r['QI_nat'])} | "
            f"{fmt_pct(r['NS_claim'])} | {fmt_pct(r['NS_evid'])} | {fmt_pct(r['NS_claim_T17_down2'])} | "
            f"{fmt_pct(r['NS_claim_T17_down10'])} | {fmt_pct(r['US_claim_x1000'])} | {fmt_pct(r['US_evid_x1000'])} | "
            f"{fmt_pct(r['US_T17_unit_down'])} | {fmt_pct(r.get('Rephrase_PASS'))} | "
            f"{fmt_pct(r.get('T14_repr_PASS'))} |"
        )
    lines.append("")
    lines.append("Per model: `n_c0_pass_bases`, `n_pol_c0_pass_bases`, QI base counts in `notes/t19_scale_sweep.json`.")
    fam_lines: list[str] = []
    for r in model_rows:
        by_f = r.get("T14_repr_by_family") or {}
        if not by_f:
            continue
        parts = [f"{fam}: {fmt_pct(st)}" for fam, st in sorted(by_f.items())]
        fam_lines.append(f"- **{r['label']}** T14_repr by family: " + "; ".join(parts))
    if fam_lines:
        lines.append("")
        lines.append("**T14_repr by family** (when n>0):")
        lines.extend(fam_lines)

    if intersection_rows:
        lines.extend(
            [
                "",
                f"## Intersection (DOSE C0-PASS bases shared by {', '.join(LOCAL_SLUGS)})",
                "",
                f"`n_intersection_bases` = **{len(intersection)}** (same conditioning for all local sizes below).",
                "",
                "| Model | C0 | QI nat | NS evid | Rephrase (POL) | T14_repr |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for r in intersection_rows:
            lines.append(
                f"| {r['label']} | {fmt_pct(r['C0'])} | {fmt_pct(r['QI_nat'])} | "
                f"{fmt_pct(r['NS_evid'])} | {fmt_pct(r.get('Rephrase_PASS'))} | "
                f"{fmt_pct(r.get('T14_repr_PASS'))} |"
            )

    loc = next((r for r in model_rows if r["slug"] == "llama31_8b_local"), None)
    if loc and loc.get("api8b_agreement") and loc["api8b_agreement"].get("n"):
        ag = loc["api8b_agreement"]
        lines.extend(
            [
                "",
                f"**8B local vs API (T6-B Llama-3.1-8B) verdict agreement:** "
                f"{100 * (ag['agreement'] or 0):.1f}% "
                f"[{100 * (ag['ci_lo'] or 0):.1f}, {100 * (ag['ci_hi'] or 0):.1f}] "
                f"(n={ag['n']} overlapping scored instances).",
            ]
        )
    e2_any = any(r.get("E2_PASS") for r in model_rows)
    if not e2_any:
        lines.append("\n_E2: no E2 rows in T19 cohort._")

    OUT_MD.write_text("\n".join(lines) + "\n")

    try:
        import matplotlib.pyplot as plt

        OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
        plot_models = [r for r in model_rows if r["QI_nat"].get("rate") is not None]
        xs = [r["params_b"] for r in plot_models]
        for ax, key, title in zip(
            axes,
            ("QI_nat", "NS_evid", "US_evid_x1000"),
            ("QI nat (PASS)", "NS evid (FAIL)", "US evid ×1k (FAIL)"),
        ):
            ys = [r[key]["rate"] for r in plot_models]
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
