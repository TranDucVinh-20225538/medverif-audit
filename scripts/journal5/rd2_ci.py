#!/usr/bin/env python3
"""(RD2-8) Bootstrap CIs and paired McNemar tests for the RD2 run.  CPU, numpy/pandas/scipy, Python >= 3.8.

Reads the per-instance RD2 scoring outputs (paths relative to --rd2-dir, default results/journal5/rd2):
  real_dose/instances.jsonl                     instance_id, qid, drug, auto_class, generator, answer_condition
  real_dose/scores/<checker>.jsonl              7 paper checkers (5 small + RAGAS-NLI + MedScore)
  real_dose/unf/scores_unf_v{1,2}/<small>.jsonl UNF v1/v2 re-scores of the changed rows (5 small checkers)
  judges/<judge>__rd2.jsonl                     chain-3 local LLM judges
  ft/<model>__rd2_raw.jsonl                     chain-1 FT checkers (+ same-path base), raw text
  ft/<model>__rd2unf_unf.jsonl / _unf_v2.jsonl  FT checkers on the UNF v1 / v2 texts (changed rows)
  basis_check/per_item.jsonl                    frozen basis check (flag_full / flag_strict)

Verdicts are read as in rd2_report.py / j3_common.verdict_map: stored verdict (PASS/FAIL/PARSE_FAIL) wins, else
score > 0.5; last row per instance wins.  PARSE_FAIL is excluded from the denominator and counted.  UNF rows not
re-scored keep their raw verdicts (prereg P3b).  Basis check: PASS = not flagged (pass/abstain/no_dose all count as
PASS, as in rd2_report.py's recall).

Reference sets.  Default = PROVISIONAL auto labels (error = rd_extract unit_error + basis_error, non-error = auto
correct), exactly as rd2_report.py without --adjudicated.  After adjudication pass --labels CSV with columns
instance_id,ref (ref in {error, nonerror}; any other value = excluded), e.g. built from the adjudicated sheet.

Outputs (--out-dir, default <rd2-dir>/ci):
  rd2_ci_rates.csv    one row per system x set: PASS k/n, rate, 95% percentile cluster-bootstrap CI (by qid = primary;
                      by drug = prereg's secondary clustering), parse fails, PASS rate with PARSE_FAIL counted as FAIL
  rd2_ci_mcnemar.csv  paired McNemar (exact binomial if discordant < 25, else chi-square with continuity correction)
                      for each FT model vs its same-path base and each UNF variant vs raw, on the error and non-error
                      set; Holm correction over all tests (p_holm_all) and within comparison family x set
                      (p_holm_family); delta PASS rate with paired cluster-bootstrap CI
  rd2_ci.md           markdown tables;  rd2_ci_meta.json  settings + input sha256

HPC (the vllm env has a site-packages package called `scripts`, so run the file, not `-m`):
  $MEDVERIF_PYTHON scripts/journal5/rd2_ci.py --n-boot 10000
"""

from __future__ import print_function

import argparse
import hashlib
import json
import os
import sys
import time
from collections import OrderedDict

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_RD2 = os.path.join(ROOT, "results", "journal5", "rd2")

PAPER = OrderedDict([("MiniCheck-RoBERTa", "t6_minicheck_roberta"), ("MiniCheck-DeBERTa", "t6_minicheck_deberta"),
                     ("AlignScore-base", "t6_alignscore_base"), ("MiniCheck-Flan-T5-Large", "v2a_minicheck"),
                     ("AlignScore-large", "v3_alignscore"), ("Llama-3.3-70B RAGAS-NLI", "v4_ragas_nli"),
                     ("MedScore (Mistral-Small-24B)", "v1_medscore")])
SMALL = list(PAPER.values())[:5]
FT_FAMILIES = ("minicheck_ft5", "alignscore_large")
FT_RATIOS = ("r0.5", "r1", "r2")
UNF_FILES = OrderedDict([("unf_v1", "unf"), ("unf_v2", "unf_v2")])  # FT pack file suffix per variant
SETS = ("error", "nonerror")
EXACT_BELOW = 25


# ----------------------------------------------------------------------------------------------------------- io
def read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def verdict_map(path):
    """Stored verdict wins; else score > 0.5.  Last row per id wins (= j3_common.verdict_map)."""
    out = {}
    for r in read_jsonl(path):
        v = r.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[r["instance_id"]] = v
        elif r.get("score") is not None:
            out[r["instance_id"]] = "PASS" if float(r["score"]) > 0.5 else "FAIL"
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_instances(rd2_dir):
    rows = read_jsonl(os.path.join(rd2_dir, "real_dose", "instances.jsonl"))
    if not rows:
        raise SystemExit("no instances in %s" % os.path.join(rd2_dir, "real_dose", "instances.jsonl"))
    df = pd.DataFrame([{"instance_id": r["instance_id"], "qid": r.get("qid") or r.get("base_id"),
                        "drug": r.get("drug") or r.get("base_id"), "auto_class": r.get("auto_class")} for r in rows])
    if df["instance_id"].duplicated().any():
        raise SystemExit("duplicate instance_id in instances.jsonl")
    return df.set_index("instance_id")


def reference(inst, labels_csv=None):
    """-> Series instance_id -> 'error' / 'nonerror' / '' (excluded), and a description."""
    if labels_csv:
        lab = pd.read_csv(labels_csv, dtype=str).fillna("")
        ref = pd.Series("", index=inst.index)
        lab = lab[lab["instance_id"].isin(inst.index)]
        ref.loc[lab["instance_id"].values] = lab["ref"].str.strip().str.lower().values
        ref[~ref.isin(SETS)] = ""
        return ref, "labels from %s" % labels_csv
    ac = inst["auto_class"]
    ref = pd.Series("", index=inst.index)
    ref[ac.isin(["unit_error", "basis_error"])] = "error"
    ref[ac == "correct"] = "nonerror"
    return ref, "PROVISIONAL auto labels (rd_extract: error = unit_error+basis_error, non-error = correct)"


def systems(rd2_dir):
    """-> list of (family, name, {instance_id: verdict}) in report order.  Missing files are skipped."""
    out = []
    sc = os.path.join(rd2_dir, "real_dose", "scores")
    raw_small = {}
    for name, f in PAPER.items():
        vm = verdict_map(os.path.join(sc, f + ".jsonl"))
        if vm:
            out.append(("paper_checker", name, vm))
            raw_small[f] = vm
    jd = os.path.join(rd2_dir, "judges")
    if os.path.isdir(jd):
        for fn in sorted(os.listdir(jd)):
            if fn.endswith("__rd2.jsonl"):
                out.append(("llm_judge", fn.split("__")[0], verdict_map(os.path.join(jd, fn))))
    ftd = os.path.join(rd2_dir, "ft")
    raw_ft = OrderedDict()
    for fam in FT_FAMILIES:
        for r in ("base",) + FT_RATIOS:
            nm = "%s_%s" % (fam, r)
            vm = verdict_map(os.path.join(ftd, "%s__rd2_raw.jsonl" % nm))
            if vm:
                raw_ft[nm] = vm
                out.append(("ft", "FT " + nm, vm))
    for var, suf in UNF_FILES.items():
        for f in SMALL:
            ch = verdict_map(os.path.join(rd2_dir, "real_dose", "unf", "scores_" + var, f + ".jsonl"))
            if f in raw_small and ch:
                vm = dict(raw_small[f])
                vm.update(ch)
                out.append(("unf", "%s %s" % (f, var), vm))
        for nm, raw in raw_ft.items():
            ch = verdict_map(os.path.join(ftd, "%s__rd2unf_%s.jsonl" % (nm, suf)))
            if ch:
                vm = dict(raw)
                vm.update(ch)
                out.append(("unf", "FT %s %s" % (nm, var), vm))
    bc = read_jsonl(os.path.join(rd2_dir, "basis_check", "per_item.jsonl"))
    if bc:
        for v in ("full", "strict"):
            out.append(("basis_check", "basis_check_%s" % v,
                        {r["instance_id"]: ("FAIL" if r.get("flag_" + v) else "PASS") for r in bc}))
    return out


def pairs(names):
    """-> list of (family, base_name, other_name) present in `names`."""
    out = []
    for fam in FT_FAMILIES:
        b = "FT %s_base" % fam
        for r in FT_RATIOS:
            o = "FT %s_%s" % (fam, r)
            if b in names and o in names:
                out.append(("ft_vs_base", b, o))
    for var in UNF_FILES:
        for f in SMALL:
            base = next((k for k, v in PAPER.items() if v == f), None)
            o = "%s %s" % (f, var)
            if base in names and o in names:
                out.append(("unf_vs_raw", base, o))
        for fam in FT_FAMILIES:
            for r in ("base",) + FT_RATIOS:
                b, o = "FT %s_%s" % (fam, r), "FT %s_%s %s" % (fam, r, var)
                if b in names and o in names:
                    out.append(("unf_vs_raw", b, o))
    return out


# ------------------------------------------------------------------------------------------------------ statistics
def cluster_weights(n_clusters, n_boot, rng):
    """B x C matrix: how often each cluster is drawn in each resample (cluster bootstrap with replacement)."""
    idx = rng.integers(0, n_clusters, size=(n_boot, n_clusters))
    flat = (idx + (np.arange(n_boot, dtype=np.int64)[:, None] * n_clusters)).ravel()
    return np.bincount(flat, minlength=n_boot * n_clusters).reshape(n_boot, n_clusters).astype(np.float64)


def boot_rate_ci(k_c, n_c, W, alpha=0.05):
    """Percentile CI of sum(W*k)/sum(W*n).  k_c, n_c: per-cluster counts aligned with W's columns."""
    kb, nb = W.dot(k_c), W.dot(n_c)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = kb / nb
    r = r[nb > 0]
    if r.size == 0:
        return (float("nan"), float("nan"))
    return (float(np.percentile(r, 100 * alpha / 2)), float(np.percentile(r, 100 * (1 - alpha / 2))))


def mcnemar(b, c, exact_below=EXACT_BELOW):
    """Two-sided McNemar on discordant counts b, c.  Exact binomial if b+c < exact_below, else chi-square with
    continuity correction.  -> (p, method, statistic)."""
    n = int(b) + int(c)
    if n == 0:
        return 1.0, "exact", float("nan")
    if n < exact_below:
        p = min(1.0, 2.0 * float(stats.binom.cdf(min(b, c), n, 0.5)))
        return p, "exact", float(min(b, c))
    chi2 = (abs(b - c) - 1.0) ** 2 / n
    return float(stats.chi2.sf(chi2, 1)), "chi2_cc", float(chi2)


def holm(pvals):
    """Holm step-down adjusted p-values (monotone, capped at 1); NaNs stay NaN."""
    p = np.asarray(pvals, dtype=float)
    out = np.full(p.shape, np.nan)
    ok = np.where(~np.isnan(p))[0]
    m = ok.size
    if m == 0:
        return out
    order = ok[np.argsort(p[ok], kind="mergesort")]
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        out[i] = min(1.0, running)
    return out


# ------------------------------------------------------------------------------------------------------------ main
def run(rd2_dir, out_dir, n_boot=10000, seed=20261002, labels_csv=None, write=True):
    t0 = time.time()
    inst = load_instances(rd2_dir)
    ref, ref_desc = reference(inst, labels_csv)
    sysl = systems(rd2_dir)
    if not sysl:
        raise SystemExit("no score files under %s" % rd2_dir)
    names = [s[1] for s in sysl]
    vmaps = dict((s[1], s[2]) for s in sysl)

    # per set and clustering: cluster index + bootstrap weights (shared by all systems -> paired deltas are coherent)
    boot = {}
    for si, st in enumerate(SETS):
        ids = ref.index[ref == st]
        for ci, ckey in enumerate(("qid", "drug")):
            lab = inst.loc[ids, ckey].astype(str)
            uniq = np.array(sorted(lab.unique()))
            pos = pd.Series(np.arange(uniq.size), index=uniq)
            cidx = pos.loc[lab.values].values if len(ids) else np.zeros(0, dtype=int)
            rng = np.random.default_rng([seed, si, ci])
            W = cluster_weights(max(uniq.size, 1), n_boot, rng) if uniq.size else np.zeros((n_boot, 1))
            boot[(st, ckey)] = (pd.Series(cidx, index=ids), uniq.size, W)

    def cluster_counts(st, ckey, ids, hits):
        cser, nc, _ = boot[(st, ckey)]
        c = cser.loc[ids].values
        return (np.bincount(c, weights=hits, minlength=max(nc, 1)),
                np.bincount(c, minlength=max(nc, 1)).astype(float))

    rows = []
    for fam, name, vm in sysl:
        for st in SETS:
            ids_all = ref.index[ref == st]
            v = pd.Series([vm.get(i, "MISSING") for i in ids_all], index=ids_all, dtype=object)
            valid = v.isin(["PASS", "FAIL"])
            ids = ids_all[valid.values]
            hits = (v[valid] == "PASS").values.astype(float)
            k, n = int(hits.sum()), int(len(ids))
            rec = OrderedDict([("family", fam), ("system", name), ("set", st), ("k_pass", k), ("n", n),
                               ("pass_rate", k / n if n else float("nan"))])
            for ckey in ("qid", "drug"):
                if n:
                    kc, nc = cluster_counts(st, ckey, ids, hits)
                    lo, hi = boot_rate_ci(kc, nc, boot[(st, ckey)][2])
                else:
                    lo = hi = float("nan")
                rec["ci_lo_%s" % ckey], rec["ci_hi_%s" % ckey] = lo, hi
            rec["n_clusters_qid"] = int(len(set(inst.loc[ids, "qid"]))) if n else 0
            rec["parse_fail"] = int((v == "PARSE_FAIL").sum())
            rec["missing"] = int((v == "MISSING").sum())
            denom = n + rec["parse_fail"]
            rec["pass_rate_parsefail_as_fail"] = k / denom if denom else float("nan")
            rows.append(rec)
    rates = pd.DataFrame(rows)

    mrows = []
    for fam, bname, oname in pairs(names):
        bvm, ovm = vmaps[bname], vmaps[oname]
        for st in SETS:
            ids_all = ref.index[ref == st]
            keep = [i for i in ids_all if bvm.get(i) in ("PASS", "FAIL") and ovm.get(i) in ("PASS", "FAIL")]
            bp = np.array([bvm[i] == "PASS" for i in keep], dtype=bool)
            op = np.array([ovm[i] == "PASS" for i in keep], dtype=bool)
            b = int((bp & ~op).sum())   # base PASS, other FAIL
            c = int((~bp & op).sum())   # base FAIL, other PASS
            p, method, stat = mcnemar(b, c)
            n = len(keep)
            d = (op.astype(float) - bp.astype(float))
            if n:
                kc, nc = cluster_counts(st, "qid", pd.Index(keep), d)
                W = boot[(st, "qid")][2]
                db = W.dot(kc) / np.where(W.dot(nc) > 0, W.dot(nc), np.nan)
                db = db[~np.isnan(db)]
                dlo, dhi = float(np.percentile(db, 2.5)), float(np.percentile(db, 97.5))
            else:
                dlo = dhi = float("nan")
            mrows.append(OrderedDict([
                ("comparison", fam), ("base", bname), ("other", oname), ("set", st), ("n_paired", n),
                ("base_pass", int(bp.sum())), ("other_pass", int(op.sum())),
                ("base_pass_rate", bp.mean() if n else float("nan")), ("other_pass_rate", op.mean() if n else float("nan")),
                ("delta_pass_rate", d.mean() if n else float("nan")), ("delta_ci_lo_qid", dlo), ("delta_ci_hi_qid", dhi),
                ("b_base_pass_other_fail", b), ("c_base_fail_other_pass", c), ("discordant", b + c),
                ("method", method), ("statistic", stat), ("p", p)]))
    mc = pd.DataFrame(mrows)
    if len(mc):
        mc["p_holm_all"] = holm(mc["p"].values)
        mc["p_holm_family"] = np.nan
        for _, g in mc.groupby(["comparison", "set"]):
            mc.loc[g.index, "p_holm_family"] = holm(g["p"].values)

    meta = OrderedDict([("generated", time.strftime("%Y-%m-%dT%H:%M:%S%z")), ("script", "scripts/journal5/rd2_ci.py"),
                        ("rd2_dir", os.path.relpath(rd2_dir, ROOT) if rd2_dir.startswith(ROOT) else rd2_dir),
                        ("reference", ref_desc), ("n_instances", int(len(inst))),
                        ("n_error", int((ref == "error").sum())), ("n_nonerror", int((ref == "nonerror").sum())),
                        ("n_boot", int(n_boot)), ("seed", int(seed)),
                        ("bootstrap", "percentile 95%, cluster resampling with replacement within each set; "
                                      "primary cluster = qid, secondary = drug"),
                        ("mcnemar", "two-sided; exact binomial if discordant < %d else chi-square with continuity "
                                    "correction; ignores clustering" % EXACT_BELOW),
                        ("holm", "p_holm_all over all %d tests; p_holm_family within (comparison, set)" % len(mc)),
                        ("instances_sha256", sha256_file(os.path.join(rd2_dir, "real_dose", "instances.jsonl"))),
                        ("elapsed_s", None)])
    meta["elapsed_s"] = round(time.time() - t0, 1)
    if write:
        os.makedirs(out_dir, exist_ok=True)
        rates.to_csv(os.path.join(out_dir, "rd2_ci_rates.csv"), index=False, float_format="%.6f")
        mc.to_csv(os.path.join(out_dir, "rd2_ci_mcnemar.csv"), index=False, float_format="%.6g")
        with open(os.path.join(out_dir, "rd2_ci_meta.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=1)
            fh.write("\n")
        with open(os.path.join(out_dir, "rd2_ci.md"), "w", encoding="utf-8") as fh:
            fh.write(markdown(rates, mc, meta))
    return rates, mc, meta


def _pct(x):
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else "%.1f" % (100 * x)


def markdown(rates, mc, meta):
    prov = meta["reference"].startswith("PROVISIONAL")
    L = ["# RD2 bootstrap CIs and paired McNemar tests%s" % (" — PROVISIONAL (auto labels)" if prov else ""), "",
         "Generated %s by `scripts/journal5/rd2_ci.py`. Reference: %s. Instances %d; error set %d; non-error set %d. "
         "%d cluster-bootstrap resamples (seed %d), percentile 95%% CI, clustered by question id (qid); drug-clustered "
         "CIs are in rd2_ci_rates.csv. PARSE_FAIL excluded from the denominator (count shown). Basis check: PASS = not "
         "flagged." % (meta["generated"], meta["reference"], meta["n_instances"], meta["n_error"], meta["n_nonerror"],
                       meta["n_boot"], meta["seed"]), "",
         "## PASS rates", "", "| family | system | PASS on errors [95% CI] | PASS on non-errors [95% CI] | parse fails (err / non-err) |",
         "|---|---|---|---|---|"]
    for (fam, name), g in rates.groupby(["family", "system"], sort=False):
        cells = []
        pf = []
        for st in SETS:
            r = g[g["set"] == st].iloc[0]
            cells.append("%d/%d = %s%% [%s, %s]" % (r["k_pass"], r["n"], _pct(r["pass_rate"]), _pct(r["ci_lo_qid"]),
                                                   _pct(r["ci_hi_qid"])))
            pf.append(str(int(r["parse_fail"])))
        L.append("| %s | %s | %s | %s | %s |" % (fam, name, cells[0], cells[1], " / ".join(pf)))
    if len(mc):
        L += ["", "## Paired McNemar (other vs base; PASS = checker accepts the answer)", "",
              "Discordant b = base PASS & other FAIL, c = base FAIL & other PASS. Exact binomial if b+c < %d, else "
              "chi-square with continuity correction. Holm over all %d tests (p_holm_all) and within comparison x set "
              "(p_holm_family). Δ = other − base PASS rate, 95%% qid-cluster bootstrap CI. McNemar ignores clustering."
              % (EXACT_BELOW, len(mc)), "",
              "| comparison | base | other | set | n | base PASS % | other PASS % | Δ pp [95% CI] | b / c | method | p | p_holm_all | p_holm_family |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in mc.iterrows():
            L.append("| %s | %s | %s | %s | %d | %s | %s | %s [%s, %s] | %d / %d | %s | %.3g | %.3g | %.3g |" % (
                r["comparison"], r["base"], r["other"], r["set"], r["n_paired"], _pct(r["base_pass_rate"]),
                _pct(r["other_pass_rate"]), _pct(r["delta_pass_rate"]), _pct(r["delta_ci_lo_qid"]),
                _pct(r["delta_ci_hi_qid"]), r["b_base_pass_other_fail"], r["c_base_fail_other_pass"], r["method"],
                r["p"], r["p_holm_all"], r["p_holm_family"]))
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rd2-dir", default=os.environ.get("MEDVERIF_RD2_DIR") or DEFAULT_RD2)
    ap.add_argument("--out-dir", default="", help="default <rd2-dir>/ci")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261002)
    ap.add_argument("--labels", default="", help="optional CSV instance_id,ref (error/nonerror) replacing auto labels")
    a = ap.parse_args(argv)
    rd2 = os.path.abspath(a.rd2_dir)
    out = os.path.abspath(a.out_dir) if a.out_dir else os.path.join(rd2, "ci")
    rates, mc, meta = run(rd2, out, n_boot=a.n_boot, seed=a.seed, labels_csv=a.labels or None)
    print("rd2_ci: %d rate rows, %d McNemar tests, n_boot=%d, %.1fs -> %s" % (len(rates), len(mc), a.n_boot,
                                                                            meta["elapsed_s"], out))


if __name__ == "__main__":
    main()
