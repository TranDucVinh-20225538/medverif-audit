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

V4_MAIN = ROOT / "results/raw/v4_ragas_nli.llama.jsonl"
V4_T14 = ROOT / "results/raw/t14/v4_ragas_nli.jsonl"
API8B_PATHS = [
    ROOT / "results/raw/t7/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/t6b/full/v6_ragas_llama31_8b.jsonl",
    ROOT / "results/raw/e2_main/v6_ragas_llama31_8b.jsonl",
]


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


def metrics_card(joined: list[dict]) -> dict:
    main = [r for r in joined if r.get("t19_pack") == "main_dose"]
    c0_stat = _pack_stat(_groups(main, lambda r: r["condition"] == "C0"))
    cond = _c0_pass_bases(main)

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

    repr_rows = [r for r in joined if r.get("t19_pack") == "t14" and r.get("condition") == "T14-repr-claim"]
    rephrase_stat = (
        _pack_stat(_groups(joined, lambda r: r.get("t19_pack") == "t14" and r.get("condition") == "T14-repr-claim"))
        if repr_rows
        else None
    )

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
        "E2_PASS": e2_stat,
        "Rephrase_PASS": rephrase_stat,
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


def main() -> None:
    instances = read_jsonl(INST)
    if not instances:
        raise SystemExit(f"missing instances: {INST}")

    api70 = load_scores(V4_MAIN, [V4_T14])
    api8b = load_scores(None, API8B_PATHS)

    model_rows = []
    for spec in MODELS:
        if spec.get("api70"):
            scores = api70
        elif spec.get("extra_paths"):
            scores = api8b
        else:
            scores = load_scores(spec["path"])
        joined = join_instances(instances, scores)
        m = metrics_card(joined)
        row = {
            "slug": spec["slug"],
            "label": spec["label"],
            "params_b": spec["params_b"],
            "n_scored": len(joined),
            "n_instances_cohort": len(instances),
            **m,
        }
        if spec["slug"] == "llama31_8b_local":
            local_scores = scores
            row["api8b_agreement"] = agreement_8b(local_scores, api8b, instances)
        model_rows.append(row)

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
        },
        "models": model_rows,
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
        "US claim ×1k | US evid ×1k | US unit÷ (T17) | Rephrase |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in model_rows:
        lines.append(
            f"| {r['label']} | {fmt_pct(r['C0'])} | {fmt_pct(r['QI_all'])} | {fmt_pct(r['QI_nat'])} | "
            f"{fmt_pct(r['NS_claim'])} | {fmt_pct(r['NS_evid'])} | {fmt_pct(r['NS_claim_T17_down2'])} | "
            f"{fmt_pct(r['NS_claim_T17_down10'])} | {fmt_pct(r['US_claim_x1000'])} | {fmt_pct(r['US_evid_x1000'])} | "
            f"{fmt_pct(r['US_T17_unit_down'])} | {fmt_pct(r.get('Rephrase_PASS'))} |"
        )
    lines.append("")
    lines.append("Per model: `n_c0_pass_bases`, `n_bases_qi_all`, `n_bases_qi_nat` in `notes/t19_scale_sweep.json`.")

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
