#!/usr/bin/env python3
"""(UNF-3) Before/after report for the unit-normalization fix (CPU, no models, no API).

before = each checker's verdict on the ORIGINAL text, after = verdict on the UNF text.  Rows UNF
does not change have identical input on both sides, so they keep the paper's stored score on both
sides; rows UNF changes are scored twice in the SAME run/env (scores/orig + scores/unf), so every
before/after difference is caused by the text change only.  Env agreement of the re-scored
originals with the paper's stored verdicts is reported per checker.

Metrics (paper definitions, scripts/t15_card_report.metrics_block; C0-conditional, base-clustered
bootstrap CIs, --boot resamples): C0 pass, QI_all, QI_nat, NS (E1-evid), US_claim_up, US_evid_up
(T7 x1000), US_claim_down, US_evid_down (T17 unit-down); plus NS_claim (E1-claim x2/x10 FAIL), E2
PASS (faithful-but-wrong; higher = worse), inversion floor / AUC (conversion vs x1000 swap, claim and
evidence side), and a robustness variant without weak-contrast E1/E2 rows.  Paired deltas
(after - before) get their own base-clustered bootstrap CI (same resampled bases on both sides).

Outputs: notes/unit_normalization_fix.md, results/journal2/unf/unf_report.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT / "src", ROOT / "analysis", ROOT / "scripts", ROOT / "scripts/journal", HERE):
    sys.path.insert(0, str(p))

import analyze  # noqa: E402
from analyze import read_jsonl  # noqa: E402
from dose_weak_contrast import flag_weak_e1_contrast  # noqa: E402
from t15_card_report import _natural_inv, metrics_block  # noqa: E402
from unf_build import cohort  # noqa: E402

RES = ROOT / "results/journal2/unf"
NOTE = ROOT / "notes/unit_normalization_fix.md"
CHECKERS = [("t6a_minicheck_roberta", "MiniCheck-RoBERTa"), ("t6a_minicheck_deberta", "MiniCheck-DeBERTa"),
            ("t6a_alignscore_base", "AlignScore-base"), ("v2a_minicheck", "MiniCheck-Flan-T5-Large"),
            ("v3_alignscore", "AlignScore-large")]
CARD = ("c0_pass_rate", "qi_all", "qi_nat", "ns", "us_claim_up", "us_evid_up", "us_claim_down", "us_evid_down")
EXTRA = ("ns_claim", "e2_pass")


def paper_scores(slug: str):
    try:
        import jr_threshold_robustness as J

        return J.score_map(slug)
    except Exception as exc:  # noqa: BLE001
        print("paper scores unavailable for %s: %s" % (slug, exc))
        return {}, {}


def preds():
    """metric -> (row predicate, success verdict). Evaluated on C0-PASS bases (except c0_pass_rate)."""
    def cond(c, mag=None, side=None):
        return lambda r: r.get("condition") == c and (mag is None or r.get("magnitude") == mag) and \
            (side is None or ("__%s__" % side) in r.get("instance_id", ""))
    return {
        "c0_pass_rate": (cond("C0"), "PASS"), "qi_all": (cond("INV-claim"), "PASS"), "qi_nat": (_natural_inv, "PASS"),
        "ns": (cond("E1-evid"), "FAIL"), "us_claim_up": (cond("E1-unit-claim", "x1000"), "FAIL"),
        "us_evid_up": (cond("E1-unit-evid", "x1000"), "FAIL"), "us_claim_down": (cond("E1-unit-down", side="claim"), "FAIL"),
        "us_evid_down": (cond("E1-unit-down", side="evid"), "FAIL"), "ns_claim": (cond("E1-claim"), "FAIL"),
        "e2_pass": (cond("E2"), "PASS")}


def per_base(block):
    """base -> metric -> (k, n), C0-conditional like the card."""
    P = preds()
    by = defaultdict(list)
    for r in block:
        if r.get("verdict") in ("PASS", "FAIL"):
            by[r["base_id"]].append(r)
    out = {}
    for b, rows in by.items():
        c0 = any(r["condition"] == "C0" and r["verdict"] == "PASS" for r in rows)
        d = {}
        for m, (pr, ok) in P.items():
            sel = [r for r in rows if pr(r)] if (m == "c0_pass_rate" or c0) else []
            d[m] = (sum(r["verdict"] == ok for r in sel), len(sel))
        out[b] = d
    return out


def rate(pb, bases, m):
    k = sum(pb[b][m][0] for b in bases if b in pb)
    n = sum(pb[b][m][1] for b in bases if b in pb)
    return (k / n) if n else None


def paired_delta(pb0, pb1, metrics, n_boot, seed):
    bases = sorted(set(pb0) | set(pb1))
    rng = random.Random(seed)
    point = {m: (None if rate(pb1, bases, m) is None or rate(pb0, bases, m) is None else rate(pb1, bases, m) - rate(pb0, bases, m))
             for m in metrics}
    draws = {m: [] for m in metrics}
    for _ in range(n_boot):
        s = [bases[rng.randrange(len(bases))] for _ in bases]
        for m in metrics:
            a, b = rate(pb0, s, m), rate(pb1, s, m)
            if a is not None and b is not None:
                draws[m].append(b - a)
    out = {}
    for m in metrics:
        d = sorted(draws[m])
        out[m] = {"delta": point[m], "lo": d[int(0.025 * (len(d) - 1))] if len(d) > 10 else None,
                  "hi": d[int(0.975 * (len(d) - 1))] if len(d) > 10 else None}
    return out


def floor(rows, side):
    conv = {r["base_id"]: r["score"] for r in rows if r["condition"] == "INV-claim" and r.get("score") is not None}
    cond = "E1-unit-claim" if side == "claim" else "E1-unit-evid"
    swap = {r["base_id"]: r["score"] for r in rows if r["condition"] == cond and r.get("magnitude") == "x1000" and r.get("score") is not None}
    common = sorted(set(conv) & set(swap))
    if not common:
        return {"n": 0, "floor": None, "auc": None}
    inv = sum(1 for b in common if conv[b] <= swap[b])
    cs, ss = list(conv.values()), list(swap.values())
    auc = sum((1.0 if c > s else 0.5 if c == s else 0.0) for c in cs for s in ss) / (len(cs) * len(ss))
    return {"n": len(common), "floor": inv / len(common), "auc": auc}


_NUMLEAD = __import__("re").compile(r"^\s*[\d.,]+(?:\s*(?:-|–|—|to)\s*[\d.,]+)?\s*")


def _unit_part(t: str) -> str:
    return _NUMLEAD.sub("", t) or t


def pct(x):
    return "NA" if x is None else "%.1f" % (100 * x)


def cell(st):
    if not st or st.get("rate") is None:
        return "NA"
    lo, hi = st.get("lo"), st.get("hi")
    return "%s [%s, %s] (n=%d)" % (pct(st["rate"]), pct(lo), pct(hi), st["den"]) if lo is not None else "%s (n=%d)" % (pct(st["rate"]), st["den"])


def simple_stat(pb, m):
    bases = sorted(pb)
    k = sum(pb[b][m][0] for b in bases)
    n = sum(pb[b][m][1] for b in bases)
    groups = [pb[b][m] for b in bases if pb[b][m][1]]
    if not n:
        return {"rate": None, "den": 0}
    st = analyze.bootstrap_rate(groups)
    return {"rate": k / n, "lo": st.get("lo"), "hi": st.get("hi"), "den": n}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--delta-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261001)
    ap.add_argument("--scores", default=str(RES / "scores"))
    ap.add_argument("--out-md", default=str(NOTE))
    ap.add_argument("--out-json", default=str(RES / "unf_report.json"))
    ap.add_argument("--checkers", default=",".join(c for c, _ in CHECKERS))
    args = ap.parse_args()
    analyze.N_BOOT = args.boot
    rows = cohort()
    unf = {r["instance_id"]: r for r in read_jsonl(ROOT / "data/journal2/unf/cohort_unf.jsonl")}
    if not unf:
        raise SystemExit("run scripts/journal2/unf_build.py first")
    weak = {r["instance_id"] for r in rows if flag_weak_e1_contrast(r).get("weak_e1_contrast")}
    sdir = Path(args.scores)
    names = dict(CHECKERS)
    res = {"boot": args.boot, "delta_boot": args.delta_boot, "n_rows": len(rows),
           "n_changed": sum(1 for r in unf.values() if r.get("unf_changed")), "n_weak_rows": len(weak), "checkers": {}}
    edits = Counter()
    for r in unf.values():
        for e in r.get("unf_edits") or []:
            edits["%s→%s" % (_unit_part(e["from"]), _unit_part(e["to"]))] += 1
    md_main, md_extra, md_floor, md_rob, md_env = [], [], [], [], []
    for slug in [s for s in args.checkers.split(",") if s]:
        name = names.get(slug, slug)
        so = {r["instance_id"]: r for r in read_jsonl(sdir / "orig" / (slug + ".jsonl"))}
        su = {r["instance_id"]: r for r in read_jsonl(sdir / "unf" / (slug + ".jsonl"))}
        if not su:
            md_main.append("| %s | not scored yet |" % name)
            continue
        pscore, pverd = paper_scores(slug)
        b0, b1, missing = [], [], Counter()
        agree = [0, 0]
        for r in rows:
            iid = r["instance_id"]
            if unf[iid].get("unf_changed"):
                o, u = so.get(iid), su.get(iid)
                if not o or not u:
                    missing["changed_unscored"] += 1
                    continue
                if pverd.get(iid) in ("PASS", "FAIL"):
                    agree[0] += pverd[iid] == o["verdict"]
                    agree[1] += 1
                b0.append(dict(r, verdict=o["verdict"], score=o["score"]))
                b1.append(dict(r, verdict=u["verdict"], score=u["score"]))
            else:
                v = pverd.get(iid) or (so.get(iid) or {}).get("verdict")
                s = pscore.get(iid, (so.get(iid) or {}).get("score"))
                if v not in ("PASS", "FAIL", "PARSE_FAIL"):
                    missing["unchanged_no_paper_score"] += 1
                    continue
                b0.append(dict(r, verdict=v, score=s))
                b1.append(dict(r, verdict=v, score=s))
        m0, m1 = metrics_block(b0, set()), metrics_block(b1, set())
        pb0, pb1 = per_base(b0), per_base(b1)
        metrics = list(CARD) + list(EXTRA)
        dl = paired_delta(pb0, pb1, metrics, args.delta_boot, args.seed)
        ex0 = {m: simple_stat(pb0, m) for m in EXTRA}
        ex1 = {m: simple_stat(pb1, m) for m in EXTRA}
        nb0, nb1 = [r for r in b0 if r["instance_id"] not in weak], [r for r in b1 if r["instance_id"] not in weak]
        r0, r1 = metrics_block(nb0, set()), metrics_block(nb1, set())
        f = {side: (floor(b0, side), floor(b1, side)) for side in ("claim", "evid")}
        key = lambda st: {k: st.get(k) for k in ("rate", "lo", "hi", "den", "n_bases")}  # noqa: E731
        res["checkers"][slug] = {"display": name, "missing": dict(missing), "env_agreement_changed_rows": agree,
                                 "before": {m: key(m0[m]) for m in CARD} | ex0, "after": {m: key(m1[m]) for m in CARD} | ex1,
                                 "delta": dl, "no_weak_before": {m: key(r0[m]) for m in CARD},
                                 "no_weak_after": {m: key(r1[m]) for m in CARD}, "inversion": f}
        for m in CARD:
            d = dl[m]
            md_main.append("| %s | %s | %s | %s | %s |" % (name, m, cell(m0[m]), cell(m1[m]),
                           "NA" if d["delta"] is None else "%+.1f [%s, %s]" % (100 * d["delta"], pct(d["lo"]), pct(d["hi"]))))
        for m in EXTRA:
            d = dl[m]
            md_extra.append("| %s | %s | %s | %s | %s |" % (name, m, cell(ex0[m]), cell(ex1[m]),
                            "NA" if d["delta"] is None else "%+.1f [%s, %s]" % (100 * d["delta"], pct(d["lo"]), pct(d["hi"]))))
        md_floor.append("| %s | %s → %s (n=%d) | %s → %s | %s → %s (n=%d) | %s → %s |" % (
            name, pct(f["claim"][0]["floor"]), pct(f["claim"][1]["floor"]), f["claim"][0]["n"],
            "NA" if f["claim"][0]["auc"] is None else "%.3f" % f["claim"][0]["auc"], "NA" if f["claim"][1]["auc"] is None else "%.3f" % f["claim"][1]["auc"],
            pct(f["evid"][0]["floor"]), pct(f["evid"][1]["floor"]), f["evid"][0]["n"],
            "NA" if f["evid"][0]["auc"] is None else "%.3f" % f["evid"][0]["auc"], "NA" if f["evid"][1]["auc"] is None else "%.3f" % f["evid"][1]["auc"]))
        md_rob.append("| %s | %s |" % (name, " | ".join("%s → %s" % (pct(r0[m].get("rate")), pct(r1[m].get("rate"))) for m in CARD[:6])))
        md_env.append("| %s | %d/%d | %s |" % (name, agree[0], agree[1], dict(missing) or "-"))
    md = ["# Unit-normalization fix (UNF): before/after for the small checkers", "",
          "Generated by `scripts/journal2/unf_report.py`. Normalizer: `src/unit_norm_fix.py` (evidence-anchored common unit; "
          "selftest `python src/unit_norm_fix.py`). Packs: `data/journal2/unf/` (%d rows over the main DOSE card cohort + T7 "
          "x1000 + T17 unit-down; %d changed by UNF). Scores: `results/journal2/unf/scores/{orig,unf}/` (changed rows scored "
          "twice in the same run; unchanged rows keep the paper's stored score on both sides)." % (res["n_rows"], res["n_changed"]),
          "", "CIs: base-clustered bootstrap (%d resamples) per side; Δ = after − before in points with a paired base-clustered "
          "bootstrap CI (%d resamples). QI/E2: PASS rates; NS/US: FAIL rates; all C0-conditional (the base's C0 must PASS on "
          "that side)." % (args.boot, args.delta_boot), "",
          "## Card metrics", "", "| checker | metric | before | after | Δ (pp) [95% CI] |", "|---|---|---|---|---|"] + md_main + \
         ["", "## Value edits and faithful-but-wrong (what UNF should NOT change)", "",
          "| checker | metric | before | after | Δ (pp) [95% CI] |", "|---|---|---|---|---|"] + md_extra + \
         ["", "`ns_claim` = FAIL on E1-claim x2/x10 (wrong numeral in the claim); `e2_pass` = PASS on E2 (claim and evidence edited "
          "consistently; higher = worse).", "",
          "## Inversion (threshold-free): share of bases whose correct conversion scores ≤ the x1000 swap", "",
          "| checker | floor claim before → after | AUC conv>swap claim | floor evid before → after | AUC conv>swap evid |",
          "|---|---|---|---|---|"] + md_floor + \
         ["", "## Robustness: weak-contrast E1/E2 rows excluded (%d rows), point estimates before → after" % res["n_weak_rows"], "",
          "| checker | " + " | ".join(CARD[:6]) + " |", "|---|" + "---|" * 6] + md_rob + \
         ["", "## Env check: re-scored ORIGINAL text vs the paper's stored verdicts (changed rows)", "",
          "| checker | agree | missing |", "|---|---|---|"] + md_env + \
         ["", "## Most frequent UNF rewrites (unit part, both texts)", "",
          ", ".join("`%s` %d" % kv for kv in edits.most_common(15)), "",
          "## What UNF cannot fix (by construction)", "",
          "- **Value errors** (wrong numeral, same unit): UNF leaves them as they are; `ns_claim`/`ns` should not move "
          "(any change there is a side effect of rewriting other doses in the same text).",
          "- **Faithful-but-wrong evidence (E2)**: claim and evidence agree after normalization, so a checker that PASSes them "
          "before still PASSes them; E2 needs an external reference, not normalization.",
          "- **IU/units ↔ mass, per-dose ↔ per-day, mEq ↔ mg**: need a drug-specific factor or the dosing frequency; UNF "
          "only aliases these (IU/U/units → units).",
          "- **Inexact time conversions** (e.g. per week → per day with a non-terminating decimal) are left unconverted.",
          "- **QI after UNF is high by construction**: a correct conversion is rewritten into the evidence's unit, i.e. "
          "usually into the C0 claim itself, and QI is conditional on C0 PASS. This shows the preprocessing works, not "
          "that the checker learned unit equivalence.",
          "- UNF changes surface form only; it does not make a checker understand units. After UNF a unit swap becomes a "
          "x1000 numeral mismatch, so the post-fix US rates are bounded by each checker's numeral sensitivity (NS).", ""]
    Path(args.out_md).write_text("\n".join(md) + "\n", encoding="utf-8")
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(res, indent=1, default=str) + "\n")
    print("\n".join(md[:40]))


if __name__ == "__main__":
    main()
