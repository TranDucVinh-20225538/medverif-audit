#!/usr/bin/env python3
"""(AT-2) Mechanism report: attribution summaries, occlusion effects, surface-overlap test, heatmaps.

1. IG / attention-rollout group shares (claim & evidence x number/unit/drug/other), mean per model x
   condition with base-clustered bootstrap CIs; per-token importance ratio vs 'other' tokens.
2. Occlusion: mean change in support probability when the claim's unit / number / drug or the
   evidence's unit is removed (per model x condition).
3. Surface-overlap test (threshold-free, base fixed effects), for the attribution models AND for every
   canonical verifier's stored card scores: y = support log-odds (or PASS indicator for verdict-only
   judges) on claim-side items C0, INV-conv, x1000 unit swap, x2/x10 value edits, regressed on
     num_overlap (claim dose numeral == evidence dose numeral), unit_overlap (same unit),
     correct (same quantity after unit conversion).
   If the checker read quantities, `correct` would dominate; if it matches surface tokens,
   `num_overlap` dominates and the fitted swap-minus-conversion gap (b_num - b_correct) > 0 predicts
   the inversion. Within-base R^2 of surface-only vs quantity-only models is also reported.
4. Heatmaps of claim-token IG for a few matched bases (C0 / correct conversion / unit swap).
Outputs: notes/attribution_mechanism.md, results/journal2/attribution/summary.json, figures/*.png
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT / "src", ROOT / "analysis", ROOT / "scripts", ROOT / "scripts/journal", HERE):
    sys.path.insert(0, str(p))

import numpy as np  # noqa: E402

from unit_norm_fix import canonical_quantity, find_spans  # noqa: E402

ATD = ROOT / "results/journal2/attribution"
NOTE = ROOT / "notes/attribution_mechanism.md"
GROUPS = [s + "_" + g for s in ("claim", "evidence") for g in ("number", "unit", "drug", "other")]
COND_ORDER = ["C0", "INV-conv", "swap-claim", "value-x10", "swap-evid"]
DISPLAY = {"mc_roberta": "MiniCheck-RoBERTa", "mc_deberta": "MiniCheck-DeBERTa", "mc_ft5": "MiniCheck-Flan-T5",
           "as_large": "AlignScore-large", "as_base": "AlignScore-base"}


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).is_file() else []


def boot_mean(by_base: dict, n=2000, seed=20261001):
    keys = [k for k, v in by_base.items() if v]
    if not keys:
        return None, None, None
    allv = [x for k in keys for x in by_base[k]]
    m = sum(allv) / len(allv)
    if len(keys) < 2:
        return m, None, None
    rng = random.Random(seed)
    draws = []
    for _ in range(n):
        s = [x for _ in keys for x in by_base[keys[rng.randrange(len(keys))]]]
        draws.append(sum(s) / len(s))
    draws.sort()
    return m, draws[int(0.025 * (n - 1))], draws[int(0.975 * (n - 1))]


def f3(m, lo, hi, pct=True):
    if m is None:
        return "NA"
    k = 100 if pct else 1
    return ("%.1f [%.1f, %.1f]" % (k * m, k * lo, k * hi)) if lo is not None else "%.1f" % (k * m)


# ------------------------------------------------------------ surface features
def _num_unit(span: str):
    sp = find_spans(span or "")
    if not sp:
        return None
    s = sp[0]
    return (str(s.n1.normalize()), str(s.n2.normalize()) if s.n2 is not None else ""), (s.unit, s.kg, s.m2, s.conc, s.time)


def features(r: dict):
    c, e = _num_unit(r.get("claim_span")), _num_unit(r.get("evidence_span"))
    if not c or not e:
        return None
    cq, eq = canonical_quantity(r["claim_span"]), canonical_quantity(r["evidence_span"])
    correct = bool(cq and eq and cq[0] == eq[0] and cq[1] == eq[1] and cq[2] == eq[2])
    return {"num_overlap": float(c[0] == e[0]), "unit_overlap": float(c[1] == e[1]), "correct": float(correct)}


def fe_ols(rows, cols, n_boot=1000, seed=20261001):
    """rows: dicts with base_id, y, features. Base fixed effects by demeaning. Coefs + cluster bootstrap CI."""
    by = defaultdict(list)
    for r in rows:
        by[r["base_id"]].append(r)
    by = {b: v for b, v in by.items() if len(v) >= 2}

    def fit(bases):
        X, Y = [], []
        for b in bases:
            g = by[b]
            xm = [sum(r[c] for r in g) / len(g) for c in cols]
            ym = sum(r["y"] for r in g) / len(g)
            for r in g:
                X.append([r[c] - m for c, m in zip(cols, xm)])
                Y.append(r["y"] - ym)
        X, Y = np.array(X), np.array(Y)
        if len(Y) < len(cols) + 2:
            return None, None
        beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
        ss = float((Y ** 2).sum())
        r2 = 1 - float(((Y - X @ beta) ** 2).sum()) / ss if ss > 0 else None
        return beta, r2

    bases = sorted(by)
    beta, r2 = fit(bases)
    if beta is None:
        return None
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        s = [bases[rng.randrange(len(bases))] for _ in bases]
        # duplicate bases need distinct keys for demeaning -> fit on the multiset
        b2, _ = fit_multiset(by, s, cols)
        if b2 is not None:
            draws.append(b2)
    draws = np.array(draws)
    ci = {c: (float(np.percentile(draws[:, i], 2.5)), float(np.percentile(draws[:, i], 97.5))) for i, c in enumerate(cols)} if len(draws) else {}
    out = {"n_rows": sum(len(by[b]) for b in bases), "n_bases": len(bases), "r2_within": r2,
           "coef": {c: float(beta[i]) for i, c in enumerate(cols)}, "ci": ci}
    if "num_overlap" in cols and "correct" in cols:
        i, j = cols.index("num_overlap"), cols.index("correct")
        d = draws[:, i] - draws[:, j] if len(draws) else []
        out["swap_minus_conv_pred"] = float(beta[i] - beta[j])
        out["swap_minus_conv_ci"] = (float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))) if len(d) else None
    return out


def fit_multiset(by, bases, cols):
    X, Y = [], []
    for b in bases:
        g = by[b]
        xm = [sum(r[c] for r in g) / len(g) for c in cols]
        ym = sum(r["y"] for r in g) / len(g)
        for r in g:
            X.append([r[c] - m for c, m in zip(cols, xm)])
            Y.append(r["y"] - ym)
    X, Y = np.array(X), np.array(Y)
    if len(Y) < len(cols) + 2:
        return None, None
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return beta, None


def logit(p):
    p = min(max(float(p), 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def claim_items():
    from analyze import read_jsonl as rj
    from t15_card_report import T7, load_main_dose_instances

    keep = {("C0", "none"): "C0", ("INV-claim", "unit_conversion"): "INV-conv", ("E1-unit-claim", "x1000"): "swap-claim",
            ("E1-claim", "x2"): "value-x2", ("E1-claim", "x10"): "value-x10"}
    rows = list(load_main_dose_instances()) + [r for r in rj(T7) if r.get("valid", True)]
    out = []
    for r in rows:
        c = keep.get((r.get("condition"), r.get("magnitude")))
        if not c:
            continue
        f = features(r)
        if f:
            out.append(dict(f, instance_id=r["instance_id"], base_id=r["base_id"], cond=c))
    return out


def stored_overlap_tests(items, n_boot):
    import paper_numbers_final as pnf
    from verifier_labels import CANONICAL_VERIFIERS, verifier_display_name

    try:
        import jr_threshold_robustness as J
    except Exception:  # noqa: BLE001
        J = None
    res = {}
    for slug in CANONICAL_VERIFIERS:
        if slug in ("t6a_hhem", "t6a_summac_conv"):  # node30-only, excluded from analyses (decision M)
            continue
        scores = J.score_map(slug)[0] if J else {}
        verd = pnf.card_verdicts(slug)
        cont = sum(1 for it in items if it["instance_id"] in scores) >= 0.9 * len(items) and \
            len({round(v, 3) for v in scores.values()}) > 3
        rows = []
        for it in items:
            if cont and it["instance_id"] in scores:
                rows.append(dict(it, y=logit(scores[it["instance_id"]])))
            elif not cont and verd.get(it["instance_id"]) in ("PASS", "FAIL"):
                rows.append(dict(it, y=1.0 if verd[it["instance_id"]] == "PASS" else 0.0))
        if len(rows) < 50:
            continue
        full = fe_ols(rows, ["num_overlap", "unit_overlap", "correct"], n_boot)
        surf = fe_ols(rows, ["num_overlap", "unit_overlap"], 0) or {}
        sem = fe_ols(rows, ["correct"], 0) or {}
        if full:
            res[slug] = dict(full, display=verifier_display_name(slug), y="logodds" if cont else "PASS (LPM)",
                             r2_surface_only=surf.get("r2_within"), r2_quantity_only=sem.get("r2_within"))
    return res


def heatmaps(recs_by_model, outdir: Path, n_bases=3):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import cm, colors
    except Exception as exc:  # noqa: BLE001
        print("no matplotlib (%s); skipping figures" % exc)
        return []
    outdir.mkdir(parents=True, exist_ok=True)
    made = []
    for model, recs in recs_by_model.items():
        by = defaultdict(dict)
        for r in recs:
            by[r["base_id"]][r["cond"]] = r
        bases = [b for b in sorted(by) if {"C0", "INV-conv", "swap-claim"} <= set(by[b])][:n_bases]
        for b in bases:
            fig, axes = plt.subplots(3, 1, figsize=(12, 3.2))
            for ax, cond in zip(axes, ("C0", "INV-conv", "swap-claim")):
                r = by[b][cond]
                toks = r["claim_tokens"]
                vals = [t[1] for t in toks]
                vmax = max(1e-9, max(abs(v) for v in vals))
                norm = colors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
                x = 0.0
                ax.set_axis_off()
                ax.set_title("%s | %s | p(support)=%.3f" % (cond, r["claim_span"], r["prob"]), fontsize=8, loc="left")
                for tok, v, *_ in toks:
                    t = tok.replace("Ġ", " ").replace("▁", " ")
                    w_ = max(0.012, 0.0085 * len(t))
                    ax.add_patch(plt.Rectangle((x, 0.1), w_, 0.8, color=cm.RdBu_r(norm(v))))
                    ax.text(x + w_ / 2, 0.5, t.strip(), ha="center", va="center", fontsize=6)
                    x += w_ + 0.002
                ax.set_xlim(0, max(1.0, x))
                ax.set_ylim(0, 1)
            fig.suptitle("%s, base %s: claim-token integrated gradients (red = toward SUPPORT)" % (DISPLAY.get(model, model), b), fontsize=9)
            p = outdir / ("ig_%s_%s.png" % (model, b))
            fig.savefig(p, dpi=150, bbox_inches="tight")
            plt.close(fig)
            made.append(str(p.relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p))
    return made


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atdir", default=str(ATD))
    ap.add_argument("--out-md", default=str(NOTE))
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--no-stored", action="store_true", help="skip the stored-score overlap test (smoke)")
    args = ap.parse_args()
    atd = Path(args.atdir)
    recs = {}
    for p in sorted(atd.glob("attr_*.jsonl")):
        rr = read_jsonl(p)
        if rr:
            recs[rr[0]["model"]] = rr
    summ = {"models": {}, "overlap_attr_models": {}, "overlap_stored": {}}
    md = ["# Mechanism: token attributions and the surface-overlap test (small checkers)", "",
          "Generated by `scripts/journal2/at_report.py` from `results/journal2/attribution/attr_*.jsonl` "
          "(`scripts/journal2/at_attribution.py`). Items: main DOSE card bases; conditions C0, INV-conv (correct unit "
          "conversion), swap-claim (x1000 unit swap, same numeral), value-x10, swap-evid. CIs: base-clustered bootstrap.", ""]
    for model, rr in recs.items():
        name = DISPLAY.get(model, model)
        repro = [abs(r["prob"] - r["score_stored"]) for r in rr if r.get("score_stored") is not None]
        gaps = [abs(r["ig_completeness_gap"]) / max(1e-6, abs(r["logodds"] - r["logodds_baseline"])) for r in rr]
        ms = {"n_items": len(rr), "repro_max_abs_diff": max(repro) if repro else None,
              "repro_n_within_1e-3": sum(d <= 1e-3 for d in repro), "repro_n": len(repro),
              "ig_rel_completeness_gap_median": sorted(gaps)[len(gaps) // 2] if gaps else None}
        md += ["## %s" % name, "",
               "Single-pass score reproduces the stored paper score within 1e-3 for %d/%d items (max |diff| %s); median "
               "relative IG completeness gap %.3f." % (ms["repro_n_within_1e-3"], ms["repro_n"],
                                                       "%.2g" % ms["repro_max_abs_diff"] if repro else "NA",
                                                       ms["ig_rel_completeness_gap_median"] or 0), ""]
        for meth in ("ig", "rollout"):
            if not any(r.get(meth) for r in rr):
                continue
            md += ["**%s: share of |attribution| (%%), mean [95%% CI]**" % ("Integrated gradients" if meth == "ig" else "Attention rollout"), "",
                   "| cond | n | " + " | ".join(GROUPS) + " | unit/other per-token ratio (claim) | number/other per-token ratio (claim) |",
                   "|---|---|" + "---|" * (len(GROUPS) + 2)]
            for cond in COND_ORDER:
                cr = [r for r in rr if r["cond"] == cond and r.get(meth)]
                if not cr:
                    continue
                cells = []
                for g in GROUPS:
                    by = defaultdict(list)
                    for r in cr:
                        by[r["base_id"]].append(r[meth]["share"].get(g, 0.0))
                    m = boot_mean(by, args.boot)
                    cells.append(f3(*m))
                    ms.setdefault(meth, {}).setdefault(cond, {})[g] = m
                ratios = []
                for g in ("claim_unit", "claim_number"):
                    by = defaultdict(list)
                    for r in cr:
                        sh, nt = r[meth]["share"], r[meth]["n_tokens"]
                        if nt.get(g) and nt.get("claim_other") and sh.get("claim_other"):
                            by[r["base_id"]].append((sh.get(g, 0) / nt[g]) / (sh["claim_other"] / nt["claim_other"]))
                    m = boot_mean(by, args.boot)
                    ratios.append(f3(*m, pct=False))
                    ms.setdefault(meth + "_ratio", {}).setdefault(cond, {})[g] = m
                md.append("| %s | %d | %s | %s |" % (cond, len(cr), " | ".join(cells), " | ".join(ratios)))
            md.append("")
        md += ["**Occlusion: mean Δ p(support) (points) [95% CI]**", "",
               "| cond | claim unit removed | claim number removed | claim drug → 'the drug' | evidence unit removed |", "|---|---|---|---|---|"]
        for cond in COND_ORDER:
            cr = [r for r in rr if r["cond"] == cond]
            if not cr:
                continue
            cells = []
            for v in ("claim_unit_removed", "claim_number_removed", "claim_drug_masked", "evid_unit_removed"):
                by = defaultdict(list)
                for r in cr:
                    if v in r["occlusion"]:
                        by[r["base_id"]].append(r["occlusion"][v]["dprob"])
                m = boot_mean(by, args.boot)
                cells.append(f3(*m) + (" (n=%d)" % sum(len(x) for x in by.values()) if m[0] is not None else ""))
                ms.setdefault("occlusion", {}).setdefault(cond, {})[v] = m
            md.append("| %s | %s |" % (cond, " | ".join(cells)))
        # inversion on this run's probabilities
        by = defaultdict(dict)
        for r in rr:
            by[r["base_id"]][r["cond"]] = r["prob"]
        pairs = [(v["INV-conv"], v["swap-claim"]) for v in by.values() if "INV-conv" in v and "swap-claim" in v]
        ms["inversion_floor_claim"] = (sum(c <= s for c, s in pairs) / len(pairs)) if pairs else None
        md += ["", "Inversion on these probabilities (claim side): %s of %d bases score the correct conversion ≤ the unit swap."
               % ("NA" if not pairs else "%.1f%%" % (100 * ms["inversion_floor_claim"]), len(pairs)), ""]
        summ["models"][model] = ms
    # surface-overlap test
    items = claim_items()
    md += ["## Surface-overlap test (base fixed effects)", "",
           "Claim-side items: C0, INV-conv, x1000 swap, x2/x10 value edits; features from the edited claim dose vs the "
           "evidence dose: `num_overlap` (same numeral), `unit_overlap` (same unit), `correct` (same quantity after "
           "conversion). C0 = (1,1,1), correct conversion = (0,0,1), unit swap = (1,0,0), value edit = (0,1,0). y = support "
           "log-odds (continuous checkers) or PASS (verdict-only judges; linear probability). `swap−conv` = fitted score of a "
           "unit swap minus a correct conversion (b_num − b_correct): > 0 means surface overlap alone predicts the inversion.", "",
           "| checker | y | n (bases) | b_num [CI] | b_unit [CI] | b_correct [CI] | swap−conv [CI] | R² within: full / surface-only / quantity-only |",
           "|---|---|---|---|---|---|---|---|"]

    def row(name, y, o):
        ci = o.get("ci", {})
        g = lambda c: "%.2f [%.2f, %.2f]" % (o["coef"][c], *ci[c]) if c in ci else "%.2f" % o["coef"][c]  # noqa: E731
        sc = o.get("swap_minus_conv_ci")
        return "| %s | %s | %d (%d) | %s | %s | %s | %s | %s / %s / %s |" % (
            name, y, o["n_rows"], o["n_bases"], g("num_overlap"), g("unit_overlap"), g("correct"),
            "%.2f [%.2f, %.2f]" % (o["swap_minus_conv_pred"], *sc) if sc else "%.2f" % o["swap_minus_conv_pred"],
            *("NA" if x is None else "%.2f" % x for x in (o.get("r2_within"), o.get("r2_surface_only"), o.get("r2_quantity_only"))))

    item_by_id = {it["instance_id"]: it for it in items}
    for model, rr in recs.items():
        rows = [dict(item_by_id[r["item_id"]], y=r["logodds"]) for r in rr if r["item_id"] in item_by_id]
        if len(rows) < 8:
            continue
        o = fe_ols(rows, ["num_overlap", "unit_overlap", "correct"], args.boot // 2)
        if not o:
            continue
        o["r2_surface_only"] = (fe_ols(rows, ["num_overlap", "unit_overlap"], 0) or {}).get("r2_within")
        o["r2_quantity_only"] = (fe_ols(rows, ["correct"], 0) or {}).get("r2_within")
        summ["overlap_attr_models"][model] = o
        md.append(row(DISPLAY.get(model, model) + " (this run)", "logodds", o))
    if not args.no_stored:
        st = stored_overlap_tests(items, args.boot // 2)
        summ["overlap_stored"] = st
        for slug, o in st.items():
            md.append(row(o["display"] + " (stored)", o["y"], o))
    md += ["", "Note: the attribution run covers C0 / INV-conv / swap-claim / value-x10 only (no x2); stored-score rows use all five.", ""]
    figs = heatmaps(recs, atd / "figures")
    summ["figures"] = figs
    if figs:
        md += ["## Example heatmaps", ""] + ["- `%s`" % f for f in figs] + [""]
    md += ["## Reading guide / caveats", "",
           "- Token groups are character-matched: numbers/units = the dose spans found by `src/unit_norm_fix.find_spans`, "
           "drug = generic-name lexicon / suffix rules / `text_utils.DRUG_RE` (drug detection is incomplete for brand names "
           "and descriptions such as 'a medication').",
           "- IG baseline = pad embeddings with special tokens kept; shares use |attribution|. Rollout is not defined for the "
           "encoder-decoder Flan-T5 and is omitted there.",
           "- Occlusion removes tokens (ungrammatical inputs); it measures reliance, not correctness.",
           "- The overlap regression is observational across perturbation types built from the same bases; the features are "
           "near-deterministic functions of condition, so it is a structured contrast, not a causal model.", ""]
    Path(args.out_md).write_text("\n".join(md) + "\n", encoding="utf-8")
    (atd / "summary.json").write_text(json.dumps(summ, indent=1, default=str) + "\n")
    print("\n".join(md[:60]))


if __name__ == "__main__":
    main()
