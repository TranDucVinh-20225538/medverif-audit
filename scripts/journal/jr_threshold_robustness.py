#!/usr/bin/env python3
"""(A) Threshold robustness for the small checkers + full bootstrap CIs for every card cell.

For each small checker with a continuous score on the main DOSE card cohort:
  1. default    - verdicts as stored (the paper's operating point; the threshold that best
                  reproduces them is reported).
  2. youden_cf  - threshold tuned by Youden's J on C0 (should PASS) vs value edits (E1-claim/E1-evid
                  x2/x10, should FAIL), CROSS-FITTED on a seeded 50/50 split of base_ids (each half is
                  evaluated with the threshold tuned on the other half).
  3. oracle     - full sweep over score quantiles on ALL data (optimistic upper bound): the threshold
                  that maximises min(QI_all, US_claim_up); also: does ANY threshold reach
                  QI_all >= 0.8 AND US_claim_up >= 0.8 (and the same with US_evid_up)?
  4. inversion floor (threshold-free) - share of bases whose correct unit CONVERSION scores <= the
                  wrong unit SWAP (x1000, same numeral) of the same base. No threshold can classify
                  both items correctly for those bases, so 1 - floor bounds the joint accuracy from
                  above. The numeral-bound argument predicts a high floor; we also report the
                  pairwise AUC P(s_conv > s_swap) over all conversion/swap pairs.
Card metrics use the paper's definitions (scripts/t15_card_report.metrics_block; C0-conditional,
base-clustered bootstrap). Also writes a CI table (B resamples, default 10000) for all card cells
of all canonical verifiers.

Outputs: notes/threshold_robustness.md, results/journal/threshold_robustness.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import JR, NOTES, ROOT, is_done, log, mark_done, read_jsonl  # noqa: E402

import analyze  # noqa: E402
import paper_numbers_final as pnf  # noqa: E402
from canonical_scores import _score_file_allowed, score_filename  # noqa: E402
from t15_card_report import (T7, _fail_groups, _natural_inv, _pass_groups, join_extra, join_rows,  # noqa: E402
                             load_main_dose_instances, metrics_block)
from verifier_labels import CANONICAL_VERIFIERS, verifier_display_name  # noqa: E402

STAGE = "A_threshold"
SMALL = ("t6a_minicheck_roberta", "t6a_minicheck_deberta", "t6a_alignscore_base", "v2a_minicheck",
         "v3_alignscore", "v2b_bespoke", "t6a_summac_zs", "t6a_summac_conv", "t6a_hhem", "t6a_granite_guardian")
KEYS = ("c0_pass_rate", "qi_all", "qi_nat", "ns", "us_claim_up", "us_evid_up", "us_claim_down", "us_evid_down")
LANE_B = ROOT / "results/raw/lane_b/main_e1_evid"
VALUE_NEG = {("E1-claim", "x2"), ("E1-claim", "x10"), ("E1-evid", "x2"), ("E1-evid", "x10")}


def score_map(slug: str) -> Tuple[Dict[str, float], Dict[str, str]]:
    scores, verdicts = {}, {}
    for iid, r in pnf.t13.merged_score_rows(slug).items():
        if r.get("score") is not None:
            scores[iid] = float(r["score"])
        if r.get("verdict") in ("PASS", "FAIL", "PARSE_FAIL"):
            verdicts[iid] = r["verdict"]
    names = [score_filename(slug), slug + ".jsonl"] + (["v2b_bespoke.jsonl"] if slug == "v2b_bespoke" else [])
    for name in names:
        p = LANE_B / name
        if not p.is_file() or not _score_file_allowed(p):
            continue
        for r in read_jsonl(p):
            iid = r.get("instance_id")
            if iid and r.get("score") is not None:
                scores.setdefault(iid, float(r["score"]))
            if iid and r.get("verdict") in ("PASS", "FAIL", "PARSE_FAIL"):
                verdicts.setdefault(iid, r["verdict"])
    return scores, verdicts


def card_rows(inst: List[dict], scores: Dict[str, float]) -> List[dict]:
    dummy = {i: "PASS" for i in scores}
    rows = join_rows(inst, dummy) + join_extra(inst, dummy, T7)
    for r in rows:
        r["score"] = scores[r["instance_id"]]
    return rows


def at_threshold(rows: List[dict], t: float, orient: int) -> List[dict]:
    out = []
    for r in rows:
        s = r["score"] * orient
        out.append(dict(r, verdict="PASS" if s >= t else "FAIL"))
    return out


def point_metrics(block: List[dict]) -> Dict[str, Optional[float]]:
    c0 = {r["base_id"] for r in block if r["condition"] == "C0" and r["verdict"] == "PASS"}

    def rate(groups):
        d = sum(x[1] for x in groups)
        return (sum(x[0] for x in groups) / d) if d else None

    return {
        "c0_pass_rate": rate(_pass_groups(block, lambda r: r.get("condition") == "C0")),
        "qi_all": rate(_pass_groups(block, lambda r: r["base_id"] in c0 and r.get("condition") == "INV-claim")),
        "qi_nat": rate(_pass_groups(block, lambda r: r["base_id"] in c0 and _natural_inv(r))),
        "ns": rate(_fail_groups(block, lambda r: r["base_id"] in c0 and r.get("condition") == "E1-evid")),
        "us_claim_up": rate(_fail_groups(block, lambda r: r["base_id"] in c0 and r.get("condition") == "E1-unit-claim"
                                         and r.get("magnitude") == "x1000")),
        "us_evid_up": rate(_fail_groups(block, lambda r: r["base_id"] in c0 and r.get("condition") == "E1-unit-evid"
                                        and r.get("magnitude") == "x1000")),
    }


def youden(rows: List[dict], orient: int) -> float:
    pos = sorted(r["score"] * orient for r in rows if r["condition"] == "C0")
    neg = sorted(r["score"] * orient for r in rows if (r["condition"], r.get("magnitude")) in VALUE_NEG)
    if not pos or not neg:
        return 0.5 * orient
    cands = sorted(set(pos) | set(neg))
    cuts = [cands[0] - 1e-9] + [(a + b) / 2 for a, b in zip(cands, cands[1:])] + [cands[-1] + 1e-9]
    best, best_t = -2.0, cuts[0]
    import bisect

    for t in cuts:
        tpr = 1 - bisect.bisect_left(pos, t) / len(pos)
        fpr = 1 - bisect.bisect_left(neg, t) / len(neg)
        j = tpr - fpr
        if j > best + 1e-12:
            best, best_t = j, t
    return best_t


def inversion_floor(rows: List[dict], orient: int) -> dict:
    conv = {r["base_id"]: r["score"] * orient for r in rows
            if r["condition"] == "INV-claim" and r.get("magnitude") == "unit_conversion"}
    nat = {r["base_id"] for r in rows if r["condition"] == "INV-claim" and _natural_inv(r)}
    out = {}
    for side, cond in (("claim", "E1-unit-claim"), ("evid", "E1-unit-evid")):
        swap = {r["base_id"]: r["score"] * orient for r in rows if r["condition"] == cond and r.get("magnitude") == "x1000"}
        common = sorted(set(conv) & set(swap))
        inv = [b for b in common if conv[b] <= swap[b]]
        cs, ss = list(conv.values()), list(swap.values())
        auc = None
        if cs and ss:
            gt = sum((1.0 if c > s else 0.5 if c == s else 0.0) for c in cs for s in ss)
            auc = gt / (len(cs) * len(ss))
        cn = [b for b in common if b in nat]
        out[side] = {"n_bases_paired": len(common), "floor": (len(inv) / len(common)) if common else None,
                     "max_joint_acc_bound": (1 - len(inv) / len(common)) if common else None,
                     "n_paired_natural": len(cn),
                     "floor_natural": (sum(1 for b in cn if conv[b] <= swap[b]) / len(cn)) if cn else None,
                     "auc_conv_vs_swap": auc}
    return out


def fmt(x, pct=True) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "NA"
    return "%.1f" % (100 * x) if pct else "%.3f" % x


def fmt_ci(st: dict) -> str:
    if not st or st.get("rate") is None:
        return "NA (n=%s)" % (st or {}).get("den", 0)
    lo, hi = st.get("lo"), st.get("hi")
    ci = " [%.1f, %.1f]" % (100 * lo, 100 * hi) if lo is not None else " [CI n/a]"
    return "%.1f%s (n=%d, q=%d)" % (100 * st["rate"], ci, st["den"], st["n_bases"])


def orientation(scores: Dict[str, float], verdicts: Dict[str, str]) -> Tuple[int, float, float]:
    """Return (orient, default_threshold, agreement) that best reproduces the stored verdicts."""
    ids = [i for i in scores if verdicts.get(i) in ("PASS", "FAIL")]
    best = (1, 0.5, -1.0)
    if not ids:
        return best
    for orient in (1, -1):
        pairs = sorted((scores[i] * orient, verdicts[i] == "PASS") for i in ids)
        n_pass_total = sum(p for _, p in pairs)
        # threshold between pairs[k-1] and pairs[k]: below -> FAIL, at/above -> PASS
        fail_below = 0
        pass_below = 0
        for k in range(len(pairs) + 1):
            agree = (k - pass_below) + (n_pass_total - pass_below)  # FAILs below + PASSes at/above
            if agree / len(pairs) > best[2] + 1e-12:
                if k == 0:
                    t = pairs[0][0] - 1e-9
                elif k == len(pairs):
                    t = pairs[-1][0] + 1e-9
                else:
                    t = (pairs[k - 1][0] + pairs[k][0]) / 2
                best = (orient, t, agree / len(pairs))
            if k < len(pairs):
                if pairs[k][1]:
                    pass_below += 1
                else:
                    fail_below += 1
    return best


def main() -> None:
    ap = argparse.ArgumentParser(description="threshold robustness (A)")
    ap.add_argument("--boot", type=int, default=10000, help="bootstrap resamples for CI tables")
    ap.add_argument("--grid", type=int, default=400, help="number of score quantiles in the oracle sweep")
    ap.add_argument("--seed", type=int, default=20261001)
    ap.add_argument("--out-md", default=str(NOTES / "threshold_robustness.md"))
    ap.add_argument("--out-json", default=str(JR / "threshold_robustness.json"))
    ap.add_argument("--checkers", default=",".join(SMALL))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if is_done(STAGE) and not args.force:
        log(STAGE, skipped="marker present")
        return
    analyze.N_BOOT = args.boot  # bootstrap_rate reads this module global
    inst = load_main_dose_instances()
    bases = sorted({r["base_id"] for r in inst})
    rng = random.Random(args.seed)
    half = set(rng.sample(bases, len(bases) // 2))
    res = {"boot": args.boot, "seed": args.seed, "grid": args.grid, "checkers": {}}
    md = ["# Threshold robustness of the small checkers (main DOSE card)", "",
          "Generated by `scripts/journal/jr_threshold_robustness.py` (seed %d; CIs: %d base-clustered bootstrap "
          "resamples; card definitions as in `scripts/t15_card_report.metrics_block`, C0-conditional)." % (args.seed, args.boot), "",
          "Operating points: **default** = stored verdicts; **Youden-CF** = Youden's J on C0 vs value edits "
          "(x2/x10, claim+evidence side), cross-fitted over a 50/50 base split; **oracle** = best min(QI_all, "
          "US_claim_up) over a %d-quantile sweep on all data (optimistic). **Inversion floor** = share of bases whose "
          "correct conversion scores <= the wrong x1000 unit swap of the same base (no threshold can get both right)." % args.grid, ""]
    summary = ["| checker | point | thr | C0 | QI_all | QI_nat | NS | US_claim↑ | US_evid↑ |", "|---|---|---|---|---|---|---|---|---|"]
    feas_lines = ["| checker | any t with QI_all≥0.8 & US_claim↑≥0.8 | any t with QI_all≥0.8 & US_evid↑≥0.8 | "
                  "max_t min(QI_all, US_claim↑) | inversion floor claim / evid (n) | AUC conv>swap claim / evid |",
                  "|---|---|---|---|---|---|"]
    detail = []
    for slug in [s.strip() for s in args.checkers.split(",") if s.strip()]:
        scores, verdicts = score_map(slug)
        rows = card_rows(inst, scores)
        if not rows:
            log(STAGE, checker=slug, skipped="no scored card rows")
            continue
        orient, t_def, agree = orientation({r["instance_id"]: r["score"] for r in rows}, verdicts)
        name = verifier_display_name(slug)
        # default = stored verdicts where present, else score >= reproduced threshold
        block_def = [dict(r, verdict=verdicts.get(r["instance_id"]) or ("PASS" if r["score"] * orient >= t_def else "FAIL"))
                     for r in rows]
        # Youden cross-fit
        ra = [r for r in rows if r["base_id"] in half]
        rb = [r for r in rows if r["base_id"] not in half]
        ta, tb = youden(ra, orient), youden(rb, orient)
        block_cf = at_threshold(ra, tb, orient) + at_threshold(rb, ta, orient)
        t_all = youden(rows, orient)
        # oracle sweep
        vals = sorted(r["score"] * orient for r in rows)
        qs = sorted(set([vals[min(len(vals) - 1, int(i * (len(vals) - 1) / args.grid))] for i in range(args.grid + 1)]))
        grid = [qs[0] - 1e-9] + [(a + b) / 2 for a, b in zip(qs, qs[1:])] + [qs[-1] + 1e-9]
        sweep = []
        for t in grid:
            m = point_metrics(at_threshold(rows, t, orient))
            sweep.append(dict(m, t=t))
        def ok(m, us):
            return m["qi_all"] is not None and m[us] is not None and m["qi_all"] >= 0.8 and m[us] >= 0.8
        feas_c = [m for m in sweep if ok(m, "us_claim_up")]
        feas_e = [m for m in sweep if ok(m, "us_evid_up")]
        mm = [m for m in sweep if m["qi_all"] is not None and m["us_claim_up"] is not None]
        best = max(mm, key=lambda m: min(m["qi_all"], m["us_claim_up"])) if mm else None
        block_or = at_threshold(rows, best["t"], orient) if best else []
        floor = inversion_floor(rows, orient)
        pts = OrderedPts = [("default", t_def, block_def), ("Youden-CF", (ta + tb) / 2, block_cf),
                            ("Youden-all", t_all, at_threshold(rows, t_all, orient)), ("oracle", best["t"] if best else None, block_or)]
        cres = {"display": name, "orientation": orient, "default_threshold_reproduced": t_def,
                "default_reproduction_agreement": agree, "youden_fold_thresholds": [ta, tb], "youden_all": t_all,
                "n_rows": len(rows), "inversion_floor": floor,
                "feasible_claim": [round(m["t"], 6) for m in feas_c][:50], "feasible_evid": [round(m["t"], 6) for m in feas_e][:50],
                "oracle": best, "points": {}}
        for pname, thr, blk in pts:
            if not blk:
                continue
            m = metrics_block(blk, set())
            cres["points"][pname] = {"threshold": thr, **{k: {kk: m[k].get(kk) for kk in ("rate", "lo", "hi", "den", "n_bases")} for k in KEYS}}
            summary.append("| %s | %s | %s | %s |" % (name, pname, "NA" if thr is None else "%.4g" % (thr * orient),
                                                      " | ".join(fmt(m[k].get("rate")) for k in KEYS[:6])))
            detail.append("| %s | %s | %s |" % (name, pname, " | ".join(fmt_ci(m[k]) for k in KEYS[:6])))
        res["checkers"][slug] = cres
        feas_lines.append("| %s | %s | %s | %s | %s / %s (n=%s/%s) | %s / %s |" % (
            name, ("YES (%d thresholds)" % len(feas_c)) if feas_c else "no",
            ("YES (%d thresholds)" % len(feas_e)) if feas_e else "no",
            fmt(min(best["qi_all"], best["us_claim_up"])) if best else "NA",
            fmt(floor["claim"]["floor"]), fmt(floor["evid"]["floor"]), floor["claim"]["n_bases_paired"],
            floor["evid"]["n_bases_paired"], fmt(floor["claim"]["auc_conv_vs_swap"], False),
            fmt(floor["evid"]["auc_conv_vs_swap"], False)))
        log(STAGE, checker=slug, rows=len(rows), orient=orient, t_default=t_def, agree=round(agree, 4),
            feasible_claim=len(feas_c), floor_claim=floor["claim"]["floor"])
    md += ["## Can any threshold satisfy QI and US together?", ""] + feas_lines + [""]
    md += ["## Card cells at each operating point (point estimates, %)", ""] + summary + [""]
    md += ["Thresholds are in the checker's native score scale (for checkers whose stored verdicts imply "
           "'lower score = PASS', the comparison is inverted; see JSON `orientation`).", ""]
    md += ["## Same, with %d-resample bootstrap CIs" % args.boot, "",
           "| checker | point | C0 | QI_all | QI_nat | NS | US_claim↑ | US_evid↑ |", "|---|---|---|---|---|---|---|---|"] + detail + [""]

    # full CI table for ALL canonical verifiers at their stored verdicts
    md += ["## Full bootstrap CIs, all card cells, all canonical verifiers (stored verdicts)", "",
           "| verifier | " + " | ".join(KEYS) + " |", "|---|" + "---|" * len(KEYS)]
    res["card_ci"] = {}
    for slug in CANONICAL_VERIFIERS:
        v = pnf.card_verdicts(slug)
        block = join_rows(inst, v) + join_extra(inst, v, T7)
        m = metrics_block(block, set())
        if m["qi_all"].get("rate") is None:
            continue
        res["card_ci"][slug] = {k: {kk: m[k].get(kk) for kk in ("rate", "lo", "hi", "den", "n_bases")} for k in KEYS}
        md.append("| %s | %s |" % (verifier_display_name(slug), " | ".join(fmt_ci(m[k]) for k in KEYS)))
    missing = [(s, k) for s, d in res["card_ci"].items() for k in KEYS if d[k]["rate"] is not None and d[k]["lo"] is None]
    md += ["", "Cells with a point estimate but no CI (fewer than 2 bases): %s" % (missing or "none"), ""]
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text("\n".join(md) + "\n", encoding="utf-8")
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
    if not args.force or "/tmp" not in args.out_md:
        mark_done(STAGE, out_md=args.out_md)
    log(STAGE, wrote=args.out_md)


if __name__ == "__main__":
    main()
