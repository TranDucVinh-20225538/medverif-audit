#!/usr/bin/env python3
"""(RD2 amendment 1, Parts C + D) Extra pre-adjudication analyses on BOTH automatic label sets.

Label sets: v1 = pre-registered extractor (rd_extract.classify), v2 = amendment-1 m2 pre-pass
(results/journal5/rd2/amend1/labels_v2.jsonl).  Reference sets per label set: error = unit_error + basis_error,
correct = correct (as rd2_ci.py / rd2_report.py).  Verdicts, systems, McNemar, Holm and the cluster bootstrap are
imported unchanged from scripts/journal5/rd2_ci.py.

C1  PASS on errors / on correct within closed-book and within grounded answers (question-clustered bootstrap, 10,000,
    seed 20261002) for the main-table systems and the FT models; closed-only FT vs base McNemar.
C2  error subtypes (unit_swap / per_kg / per_m2 / rest) and the direction "absolute dose where the label gives a per-kg
    or per-m2 dose" vs the reverse under ONE rule (classifier's primary answer dose vs the label dose it was matched to),
    with two alternative rules for reconciliation.
C3  booktabs tables: rd2full.tex (Wilson, drug-cluster bootstrap 5,000, question-cluster bootstrap 10,000; parse fails and
    PF = FAIL), rd2paired.tex (64 paired comparisons), rd2gen.tex (generator x condition).
C4  no-dose sensitivity (parseable no-dose answers under their v2 class).
D   paper_numbers_rd2.json / .md.

Outputs: results/journal5/rd2/analysis/.   Usage:  python scripts/journal5/rd2_analysis_extra.py
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from collections import Counter, OrderedDict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rd2_ci as R  # noqa: E402
from rd2_relabel_v2 import QUESTIONS, RD2, classify, classify_v2, read_jsonl  # noqa: E402
from unit_norm_fix import find_spans  # noqa: E402

ROOT = R.ROOT
RD2_DIR = R.DEFAULT_RD2
AM = os.path.join(RD2_DIR, "amend1")
OUT = os.path.join(RD2_DIR, "analysis")
SEED = 20261002
NB_QID, NB_DRUG = 10000, 5000
LSETS = ("v1", "v2")
SUBSETS = ("all", "closed", "grounded")
SETS = ("error", "nonerror")
UNIT_TYPE = ("unit_error", "basis_error")
MAIN = list(R.PAPER) + ["medgemma_27b", "baichuan_m2_32b", "basis_check_full", "basis_check_strict"]
FT = ["FT %s_%s" % (f, r) for f in R.FT_FAMILIES for r in ("base",) + R.FT_RATIOS]
TABLE_FAMILIES = ("paper_checker", "llm_judge", "ft", "basis_check")
REL = os.path.relpath


def rel(p):
    return REL(p, ROOT)


# ------------------------------------------------------------------------------------------------------------ data
def load():
    lab = pd.DataFrame(read_jsonl(os.path.join(AM, "labels_v2.jsonl"))).set_index("instance_id")
    inst = {r["instance_id"]: r for r in read_jsonl(os.path.join(RD2_DIR, "real_dose", "instances.jsonl"))}
    for iid, r in inst.items():  # scored instances carry the frozen v1 label
        assert lab.at[iid, "class_v1"] == r["auto_class"] and lab.at[iid, "subtype_v1"] == r.get("auto_subtype", ""), iid
    lab["scored"] = lab.index.isin(list(inst))
    return lab


def reference(lab, L):
    c = lab["class_" + L]
    ref = pd.Series("", index=lab.index)
    ref[c.isin(UNIT_TYPE)] = "error"
    ref[c == "correct"] = "nonerror"
    ref[~lab["scored"]] = ""
    return ref


def wilson(k, n, z=1.959963984540054):
    if not n:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


class Boot:
    """Cluster-bootstrap weight matrices shared by all systems for one (label set, subset, set, cluster key).
    Seeding for (v1, all) equals rd2_ci.py ([seed, set index, cluster index]) so those CIs reproduce rd2_ci_rates.csv
    whenever the number of resamples is the same."""

    def __init__(self, lab):
        self.lab, self.cache = lab, {}

    def get(self, L, sub, st, ids, ckey, nb):
        key = (L, sub, st, ckey, nb)
        if key not in self.cache:
            labs = self.lab.loc[ids, ckey].astype(str)
            uniq = np.array(sorted(labs.unique()))
            pos = pd.Series(np.arange(uniq.size), index=uniq)
            cidx = pd.Series(pos.loc[labs.values].values if len(ids) else np.zeros(0, int), index=ids)
            li, si, ci, bi = LSETS.index(L), SETS.index(st), ("qid", "drug").index(ckey), SUBSETS.index(sub)
            sk = [SEED, si, ci] + ([li, bi] if (li, bi) != (0, 0) else [])
            W = R.cluster_weights(max(uniq.size, 1), nb, np.random.default_rng(sk))
            self.cache[key] = (cidx, max(uniq.size, 1), W)
        return self.cache[key]

    def ci(self, L, sub, st, all_ids, ckey, nb, ids, vals):
        cidx, nc, W = self.get(L, sub, st, all_ids, ckey, nb)
        c = cidx.loc[ids].values
        kc = np.bincount(c, weights=vals, minlength=nc)
        n_c = np.bincount(c, minlength=nc).astype(float)
        return R.boot_rate_ci(kc, n_c, W) if len(ids) else (float("nan"), float("nan"))

    def delta_ci(self, L, sub, st, all_ids, ids, d):
        cidx, nc, W = self.get(L, sub, st, all_ids, "qid", NB_QID)
        c = cidx.loc[ids].values
        kc, n_c = np.bincount(c, weights=d, minlength=nc), np.bincount(c, minlength=nc).astype(float)
        nb = W.dot(n_c)
        db = W.dot(kc) / np.where(nb > 0, nb, np.nan)
        db = db[~np.isnan(db)]
        return (float(np.percentile(db, 2.5)), float(np.percentile(db, 97.5))) if db.size else (float("nan"), float("nan"))


def subset_ids(lab, ref, st, sub):
    m = ref == st
    if sub != "all":
        m &= lab["condition"] == sub
    return lab.index[m]


def rate_rows(lab, boot, sysl, names, subsets, drug=False):
    rows = []
    for L in LSETS:
        ref = reference(lab, L)
        for sub in subsets:
            for fam, name, vm in sysl:
                if name not in names:
                    continue
                for st in SETS:
                    all_ids = subset_ids(lab, ref, st, sub)
                    v = pd.Series([vm.get(i, "MISSING") for i in all_ids], index=all_ids, dtype=object)
                    ok = v.isin(["PASS", "FAIL"]).values
                    ids = all_ids[ok]
                    hits = (v[ok] == "PASS").values.astype(float)
                    k, n = int(hits.sum()), len(ids)
                    wl, wh = wilson(k, n)
                    ql, qh = boot.ci(L, sub, st, all_ids, "qid", NB_QID, ids, hits)
                    rec = OrderedDict([("label_set", L), ("subset", sub), ("family", fam), ("system", name), ("set", st),
                                       ("k_pass", k), ("n", n), ("pass_rate", k / n if n else float("nan")),
                                       ("wilson_lo", wl), ("wilson_hi", wh), ("qid_lo", ql), ("qid_hi", qh)])
                    if drug:
                        rec["drug_lo"], rec["drug_hi"] = boot.ci(L, sub, st, all_ids, "drug", NB_DRUG, ids, hits)
                    pf = int((v == "PARSE_FAIL").sum())
                    rec.update([("n_clusters_qid", int(lab.loc[ids, "qid"].nunique()) if n else 0), ("parse_fail", pf),
                                ("missing", int((v == "MISSING").sum())),
                                ("pass_rate_pf_as_fail", k / (n + pf) if n + pf else float("nan"))])
                    rows.append(rec)
    return pd.DataFrame(rows)


def paired_rows(lab, boot, vmaps, pairs, subsets):
    rows = []
    for L in LSETS:
        ref = reference(lab, L)
        for sub in subsets:
            for fam, bname, oname in pairs:
                bvm, ovm = vmaps[bname], vmaps[oname]
                for st in SETS:
                    all_ids = subset_ids(lab, ref, st, sub)
                    keep = pd.Index([i for i in all_ids if bvm.get(i) in ("PASS", "FAIL") and ovm.get(i) in ("PASS", "FAIL")])
                    bp = np.array([bvm[i] == "PASS" for i in keep], bool)
                    op = np.array([ovm[i] == "PASS" for i in keep], bool)
                    b, c = int((bp & ~op).sum()), int((~bp & op).sum())
                    p, method, stat = R.mcnemar(b, c)
                    d = op.astype(float) - bp.astype(float)
                    lo, hi = boot.delta_ci(L, sub, st, all_ids, keep, d) if len(keep) else (float("nan"),) * 2
                    n = len(keep)
                    rows.append(OrderedDict([
                        ("label_set", L), ("subset", sub), ("comparison", fam), ("base", bname), ("other", oname), ("set", st),
                        ("n_paired", n), ("base_pass_rate", bp.mean() if n else float("nan")),
                        ("other_pass_rate", op.mean() if n else float("nan")), ("delta_pass_rate", d.mean() if n else float("nan")),
                        ("delta_ci_lo_qid", lo), ("delta_ci_hi_qid", hi), ("b_base_pass_other_fail", b),
                        ("c_base_fail_other_pass", c), ("discordant", b + c), ("method", method), ("statistic", stat), ("p", p)]))
    df = pd.DataFrame(rows)
    df["p_holm_all"] = np.nan
    df["p_holm_family"] = np.nan
    for _, g in df.groupby(["label_set", "subset"]):
        df.loc[g.index, "p_holm_all"] = R.holm(g["p"].values)
    for _, g in df.groupby(["label_set", "subset", "comparison", "set"]):
        df.loc[g.index, "p_holm_family"] = R.holm(g["p"].values)
    return df


# ------------------------------------------------------------------------------------------------------------- C2
def c2(lab):
    qs = {q["qid"]: q for q in read_jsonl(QUESTIONS)}
    relb = lambda s: bool(s.kg or s.m2)  # noqa: E731

    def direction(ans_rel, lab_rel):
        if lab_rel and not ans_rel:
            return "absolute_for_relative"
        if ans_rel and not lab_rel:
            return "relative_for_absolute"
        return "both_relative" if ans_rel else "neither_relative"

    rows = []
    for r in read_jsonl(RD2 / "extract_rows.jsonl"):
        q = qs[r["qid"]]
        args = (r["answer"], q["target_sentence"], q["excerpt"], q.get("primary_target"))
        for L, o in (("v1", classify(*args)), ("v2", classify_v2(*args, frozen_class=r["auto_class"]))):
            assert o["auto_class"] == lab.at[r["instance_id"], "class_" + L]
            if o["auto_class"] not in UNIT_TYPE:
                continue
            p, m = find_spans(o["primary"])[0], find_spans(o["matched"])[0]
            a_sp, t_sp = find_spans(args[0]), find_spans(args[1])
            pt = find_spans(args[3] or "")
            sub = o["subtype"]
            rows.append({"instance_id": r["instance_id"], "label_set": L, "class": o["auto_class"], "subtype": sub,
                         "subtype4": sub if sub in ("unit_swap", "per_kg", "per_m2") else "rest", "condition": r["condition"],
                         "dir_A_primary_vs_matched": direction(relb(p), relb(m)),
                         "dir_B_primary_vs_primary_target": direction(relb(p), relb(pt[0])) if pt else "no_primary_target",
                         "dir_C_any_span": direction(any(relb(s) for s in a_sp), any(relb(s) for s in t_sp))})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------------------ tex
def tx(s):
    return str(s).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")


def pc(x, d=1):
    return "--" if x is None or (isinstance(x, float) and np.isnan(x)) else ("%.*f" % (d, 100 * x))


def ci(lo, hi):
    return "--" if np.isnan(lo) else "[%s, %s]" % (pc(lo), pc(hi))


def pfmt(p):
    if p is None or np.isnan(p):
        return "--"
    if p >= 1e-3:
        return "%.2g" % p
    m, e = ("%.1e" % p).split("e")
    return "$%s\\times10^{%d}$" % (m, int(e))


def rd2full_tex(rates):
    L = ["% generated by scripts/journal5/rd2_analysis_extra.py; PROVISIONAL automatic labels (v1 = pre-registered, v2 = amendment 1)",
         "\\begin{table*}[t]", "\\centering", "\\scriptsize",
         "\\caption{RD2: PASS rate on automatically detected unit/basis errors and on automatically correct answers (provisional "
         "automatic labels). Wilson 95\\% CI; drug-clustered bootstrap (5{,}000, pre-registered); question-clustered bootstrap "
         "(10{,}000). PF = parse failures (excluded from the denominator); PF=FAIL = PASS rate with parse failures counted as FAIL. "
         "Basis check: PASS = not flagged.}", "\\label{tab:rd2full}",
         "\\resizebox{\\textwidth}{!}{%", "\\begin{tabular}{llrrrrrrrrrr}", "\\toprule",
         " & & \\multicolumn{4}{c}{PASS on errors (\\%)} & \\multicolumn{4}{c}{PASS on correct (\\%)} & & \\\\",
         "\\cmidrule(lr){3-6}\\cmidrule(lr){7-10}",
         "Labels & System & $k/n$ (\\%) & Wilson & Drug & Question & $k/n$ (\\%) & Wilson & Drug & Question & PF (err/corr) & PF=FAIL err/corr \\\\",
         "\\midrule"]
    a = rates[rates["subset"] == "all"]
    for Ls in LSETS:
        g = a[a["label_set"] == Ls]
        for name in dict.fromkeys(g["system"]):
            e = g[(g["system"] == name) & (g["set"] == "error")].iloc[0]
            c = g[(g["system"] == name) & (g["set"] == "nonerror")].iloc[0]
            cells = []
            for r in (e, c):
                cells += ["%d/%d (%s)" % (r["k_pass"], r["n"], pc(r["pass_rate"])), ci(r["wilson_lo"], r["wilson_hi"]),
                          ci(r["drug_lo"], r["drug_hi"]), ci(r["qid_lo"], r["qid_hi"])]
            L.append("%s & %s & %s & %d/%d & %s/%s \\\\" % (Ls, tx(name), " & ".join(cells), e["parse_fail"], c["parse_fail"],
                                                          pc(e["pass_rate_pf_as_fail"]), pc(c["pass_rate_pf_as_fail"])))
        L.append("\\midrule" if Ls == "v1" else "\\bottomrule")
    L += ["\\end{tabular}}", "\\end{table*}"]
    return "\n".join(L) + "\n"


def rd2paired_tex(pm):
    L = ["% generated by scripts/journal5/rd2_analysis_extra.py; PROVISIONAL automatic labels",
         "\\begin{scriptsize}", "\\begin{longtable}{lllrrrrrrr}",
         "\\caption{RD2 paired comparisons (FT vs same-path base; UNF v1/v2 re-score vs raw) on the automatic error and correct "
         "sets. $b$ = base PASS \\& other FAIL, $c$ = base FAIL \\& other PASS; McNemar exact if $b+c<25$, else $\\chi^2$ with "
         "continuity correction; Holm over the 64 tests of each label set; $\\Delta$ = other $-$ base PASS rate (pp), "
         "question-clustered bootstrap 95\\% CI (10{,}000).}\\label{tab:rd2paired}\\\\",
         "\\toprule", "Labels & Base & Other & Set & $n$ & $b$/$c$ & $\\Delta$ pp & 95\\% CI & $p$ & $p_\\mathrm{Holm}$ \\\\",
         "\\midrule", "\\endfirsthead", "\\toprule",
         "Labels & Base & Other & Set & $n$ & $b$/$c$ & $\\Delta$ pp & 95\\% CI & $p$ & $p_\\mathrm{Holm}$ \\\\", "\\midrule",
         "\\endhead", "\\bottomrule", "\\endfoot"]
    a = pm[pm["subset"] == "all"]
    for Ls in LSETS:
        for _, r in a[a["label_set"] == Ls].iterrows():
            L.append("%s & %s & %s & %s & %d & %d/%d & %s & %s & %s & %s \\\\" % (
                Ls, tx(r["base"]), tx(r["other"]), "errors" if r["set"] == "error" else "correct", r["n_paired"],
                r["b_base_pass_other_fail"], r["c_base_fail_other_pass"], pc(r["delta_pass_rate"]),
                ci(r["delta_ci_lo_qid"], r["delta_ci_hi_qid"]), pfmt(r["p"]), pfmt(r["p_holm_all"])))
        if Ls == "v1":
            L.append("\\midrule")
    L += ["\\end{longtable}", "\\end{scriptsize}"]
    return "\n".join(L) + "\n"


def gen_table(lab):
    rows = []
    for (g, c), d in lab.groupby(["generator", "condition"]):
        rec = OrderedDict([("generator", g), ("condition", c), ("answers", len(d))])
        for Ls in LSETS:
            cl = d["class_" + Ls]
            nd, u, b, co = int((cl == "no_dose").sum()), int((cl == "unit_error").sum()), int((cl == "basis_error").sum()), int((cl == "correct").sum())
            rec.update([("no_dose_" + Ls, nd), ("unit_" + Ls, u), ("basis_" + Ls, b), ("correct_" + Ls, co),
                        ("unit_basis_rate_" + Ls, (u + b) / (len(d) - nd))])
        rows.append(rec)
    return pd.DataFrame(rows)


def rd2gen_tex(gt):
    L = ["% generated by scripts/journal5/rd2_analysis_extra.py; PROVISIONAL automatic labels",
         "\\begin{table}[t]", "\\centering", "\\scriptsize",
         "\\caption{RD2 answers per generator and condition: no-dose answers, automatic unit and basis errors, automatically "
         "correct answers and the unit/basis error rate among dose answers, under the pre-registered (v1) and amended (v2) "
         "automatic labels.}", "\\label{tab:rd2gen}", "\\begin{tabular}{llrrrrrrrrrrr}", "\\toprule",
         " & & & \\multicolumn{5}{c}{v1 (pre-registered)} & \\multicolumn{5}{c}{v2 (amendment 1)} \\\\",
         "\\cmidrule(lr){4-8}\\cmidrule(lr){9-13}",
         "Generator & Condition & Answers & No dose & Unit & Basis & Correct & Error \\% & No dose & Unit & Basis & Correct & Error \\% \\\\",
         "\\midrule"]
    for _, r in gt.iterrows():
        L.append("%s & %s & %d & %s \\\\" % (tx(r["generator"]), r["condition"], r["answers"], " & ".join(
            "%d & %d & %d & %d & %s" % (r["no_dose_" + Ls], r["unit_" + Ls], r["basis_" + Ls], r["correct_" + Ls],
                                        pc(r["unit_basis_rate_" + Ls])) for Ls in LSETS)))
    tot = gt.sum(numeric_only=True)
    L.append("\\midrule")
    L.append("All & & %d & %s \\\\" % (tot["answers"], " & ".join(
        "%d & %d & %d & %d & %s" % (tot["no_dose_" + Ls], tot["unit_" + Ls], tot["basis_" + Ls], tot["correct_" + Ls],
                                    pc((tot["unit_" + Ls] + tot["basis_" + Ls]) / (tot["answers"] - tot["no_dose_" + Ls]))) for Ls in LSETS)))
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------------------------ main
def git(*a):
    return subprocess.check_output(["git"] + list(a), cwd=ROOT, text=True).strip()


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    lab = load()
    sysl = R.systems(RD2_DIR)
    vmaps = {s[1]: s[2] for s in sysl}
    names = [s[1] for s in sysl]
    boot = Boot(lab)

    # ---- C3 full table (all systems, all answers) + C1 condition subsets (main systems + FT)
    table_names = [s[1] for s in sysl if s[0] in TABLE_FAMILIES]
    full = rate_rows(lab, boot, sysl, set(table_names), ("all",), drug=True)
    c1n = set(MAIN + FT)
    cond = rate_rows(lab, boot, sysl, c1n, ("closed", "grounded"))
    full.to_csv(os.path.join(OUT, "rd2_rates_all.csv"), index=False, float_format="%.6f")
    cond.to_csv(os.path.join(OUT, "c1_condition_rates.csv"), index=False, float_format="%.6f")

    # ---- paired: 64 comparisons on all answers; closed-only FT vs base
    allpairs = R.pairs(names)
    pm = paired_rows(lab, boot, vmaps, allpairs, ("all",))
    ftp = [p for p in allpairs if p[0] == "ft_vs_base"]
    pmc = paired_rows(lab, boot, vmaps, ftp, ("closed",))
    pm.to_csv(os.path.join(OUT, "rd2_paired_all.csv"), index=False, float_format="%.6g")
    pmc.to_csv(os.path.join(OUT, "c1_ft_mcnemar_closed.csv"), index=False, float_format="%.6g")
    assert (pm.groupby("label_set").size() == 64).all(), pm.groupby("label_set").size()

    # ---- C2
    sub = c2(lab)
    sub.to_csv(os.path.join(OUT, "c2_subtypes_per_item.csv"), index=False)
    st4 = sub.groupby(["label_set", "subtype4"]).size().unstack(0).fillna(0).astype(int)
    st4c = sub.groupby(["label_set", "class", "subtype4"]).size().unstack(0).fillna(0).astype(int)
    dirs = {d: sub.groupby(["label_set", d]).size().unstack(0).fillna(0).astype(int)
            for d in ("dir_A_primary_vs_matched", "dir_B_primary_vs_primary_target", "dir_C_any_span")}
    dirA_sub = sub.groupby(["label_set", "subtype4", "dir_A_primary_vs_matched"]).size().unstack(0).fillna(0).astype(int)

    # ---- C3 generator table + tex
    gt = gen_table(lab)
    gt.to_csv(os.path.join(OUT, "rd2_gen.csv"), index=False, float_format="%.6f")
    for fn, s in (("rd2full.tex", rd2full_tex(full)), ("rd2paired.tex", rd2paired_tex(pm)), ("rd2gen.tex", rd2gen_tex(gt))):
        with open(os.path.join(OUT, fn), "w") as fh:
            fh.write(s)

    # ---- C4 no-dose sensitivity
    nd = lab[lab["class_v1"] == "no_dose"]
    parse = nd[nd["class_v2"] != "no_dose"]
    ref_v2 = reference(lab, "v2")
    ref_c4 = lab["class_v2"].map(lambda c: "error" if c in UNIT_TYPE else "nonerror" if c == "correct" else "")
    entering = ref_c4[parse.index]
    c4 = OrderedDict([
        ("no_dose_v1", int(len(nd))), ("no_dose_scored_by_checkers", int(nd["scored"].sum())),
        ("parseable_under_v2", int(len(parse))), ("parseable_v2_classes", dict(Counter(parse["class_v2"]))),
        ("parseable_entering_error_set", int((entering == "error").sum())),
        ("parseable_entering_correct_set", int((entering == "nonerror").sum())),
        ("main_table_reference_sets_identical", bool(((ref_c4.where(lab["scored"], "")) == ref_v2).all())),
        ("note", "The 72 no-dose answers were never scored by any checker (scored set = 5,688 = 5,760 - 72), and the 4 "
                 "parseable ones fall in unverifiable (3) / time_ambiguous (1), which are in neither the error nor the correct "
                 "set; the main-table PASS rates with the parseable no-dose answers included under their v2 class are "
                 "therefore identical to the v2 rates (rd2_rates_all.csv, label_set v2). A sensitivity with human labels is "
                 "defined in prereg/rd2_amendment_1.md section 2.")])
    with open(os.path.join(OUT, "c4_nodose_sensitivity.json"), "w") as fh:
        json.dump(c4, fh, indent=1)
        fh.write("\n")

    # ---- C1 summary sentence
    def rng_(L, sub, names_):
        d = cond if sub != "all" else full
        g = d[(d["label_set"] == L) & (d["subset"] == sub) & (d["set"] == "error") & d["system"].isin(names_)]
        return g["pass_rate"].min(), g["pass_rate"].max(), g
    paper = list(R.PAPER)
    def corr_rng(L, sub):
        d = cond if sub != "all" else full
        g = d[(d["label_set"] == L) & (d["subset"] == sub) & (d["set"] == "nonerror") & d["system"].isin(paper)]
        return g["pass_rate"].min(), g["pass_rate"].max()

    s_lines = []
    for L in LSETS:
        lo, hi, g = rng_(L, "closed", paper)
        alo, ahi, _ = rng_(L, "all", paper)
        s_lines.append((L, lo, hi, alo, ahi, int(g["n"].max())))
    below7 = sorted(cond[(cond["label_set"] == "v1") & (cond["subset"] == "closed") & (cond["set"] == "error") &
                         cond["system"].isin(paper) & (cond["pass_rate"] < 0.07)]["system"])
    cc, ca = corr_rng("v1", "closed"), corr_rng("v1", "all")
    answer = ("Yes, roughly: within closed-book answers the seven paper checkers pass %s%% of automatic unit/basis errors under "
              "the pre-registered labels (n = %d; all answers %s%%) and %s%% under the v2 labels (n = %d) — only %s fall below 7%% — "
              "because %d of %d (v1) / %d of %d (v2) automatic errors are closed-book anyway; what changes in closed-book is PASS on "
              "correct answers, which drops to %s%% (all answers %s%%)." % (
                  "%s-%s" % (pc(s_lines[0][1]), pc(s_lines[0][2])), s_lines[0][5], "%s-%s" % (pc(s_lines[0][3]), pc(s_lines[0][4])),
                  "%s-%s" % (pc(s_lines[1][1]), pc(s_lines[1][2])), s_lines[1][5], " and ".join(below7) or "none",
                  s_lines[0][5], int((reference(lab, "v1") == "error").sum()), s_lines[1][5], int((reference(lab, "v2") == "error").sum()),
                  "%s-%s" % (pc(cc[0]), pc(cc[1])), "%s-%s" % (pc(ca[0]), pc(ca[1]))))

    # ---- markdown report
    def rate_cell(d, L, sub, name, st):
        r = d[(d["label_set"] == L) & (d["subset"] == sub) & (d["system"] == name) & (d["set"] == st)]
        if not len(r):
            return "–"
        r = r.iloc[0]
        return "%d/%d = %s %s" % (r["k_pass"], r["n"], pc(r["pass_rate"]), ci(r["qid_lo"], r["qid_hi"]))

    md = ["# RD2 extra analyses (amendment 1, Part C) — PROVISIONAL automatic labels", "",
          "Generated by `scripts/journal5/rd2_analysis_extra.py`. v1 = pre-registered automatic labels, v2 = amendment-1 labels "
          "(`results/journal5/rd2/amend1/labels_v2.jsonl`). Error = unit_error + basis_error; correct = correct. Question-"
          "clustered bootstrap %d resamples (seed %d), percentile 95%% CI. PARSE_FAIL excluded (counts in CSVs)." % (NB_QID, SEED),
          "", "## C1 Closed-book / grounded rates", "", answer, "",
          "| system | closed: PASS on errors v1 | v2 | closed: PASS on correct v1 | v2 | grounded: PASS on errors v1 | v2 | grounded: PASS on correct v1 | v2 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for name in MAIN + FT:
        if name not in c1n or name not in names:
            continue
        md.append("| %s | %s |" % (name, " | ".join(rate_cell(cond, L, sub, name, st) for sub in ("closed", "grounded")
                                                     for st in SETS for L in LSETS)))
    md += ["", "Closed-book-only FT vs base McNemar (all six FT models; MiniCheck-Flan-T5 r1 is the requested one):", "",
           "| labels | base | other | set | n | b / c | Δ pp [95% CI] | p | Holm (6×2 within labels) |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in pmc.iterrows():
        md.append("| %s | %s | %s | %s | %d | %d / %d | %s %s | %.3g | %.3g |" % (
            r["label_set"], r["base"], r["other"], r["set"], r["n_paired"], r["b_base_pass_other_fail"],
            r["c_base_fail_other_pass"], pc(r["delta_pass_rate"]), ci(r["delta_ci_lo_qid"], r["delta_ci_hi_qid"]), r["p"], r["p_holm_all"]))
    md += ["", "## C2 Error subtypes (automatic unit + basis errors)", "",
           "| subtype | v1 | v2 |", "|---|---|---|"] + ["| %s | %d | %d |" % (k, st4.at[k, "v1"], st4.at[k, "v2"]) for k in st4.index] + [
           "| **total** | %d | %d |" % (st4["v1"].sum(), st4["v2"].sum()), "", "By class:", "", "| class | subtype | v1 | v2 |", "|---|---|---|---|"] + [
           "| %s | %s | %d | %d |" % (k[0], k[1], st4c.at[k, "v1"], st4c.at[k, "v2"]) for k in st4c.index] + [
           "", "Direction of the basis mismatch. **Committed rule (A)**: compare the classifier's primary answer dose with the "
           "label dose it was matched to (`primary` vs `matched` in `rd_extract.classify`); 'absolute for relative' = the label dose "
           "is per kg or per m² and the answer dose is not; 'relative for absolute' = the reverse. Alternatives for "
           "reconciliation: (B) primary answer dose vs the question's primary target dose; (C) any answer dose vs any dose in the "
           "label target sentence.", "",
           "| rule | direction | v1 | v2 |", "|---|---|---|---|"]
    for dname, t in dirs.items():
        for k in t.index:
            md.append("| %s | %s | %d | %d |" % (dname, k, t.at[k, "v1"], t.at[k, "v2"]))
    md += ["", "Rule A by subtype:", "", "| subtype | direction | v1 | v2 |", "|---|---|---|---|"] + [
        "| %s | %s | %d | %d |" % (k[0], k[1], dirA_sub.at[k, "v1"], dirA_sub.at[k, "v2"]) for k in dirA_sub.index]
    A = dirs["dir_A_primary_vs_matched"]
    B = dirs["dir_B_primary_vs_primary_target"]
    C = dirs["dir_C_any_span"]
    recon = ("Reconciliation: rule A reproduces the audit's %d/%d exactly under v1; rule B gives %d/%d and rule C %d/%d, so "
             "the ad hoc 255/123 is not reproduced exactly by any committed rule (its first number equals rule B, its second is "
             "closest to rule C; the ad hoc rule was never committed, so it cannot be checked further). Under v2, rule A gives %d/%d: the %d fewer 'relative for absolute' "
             "items are exactly the m² superscript artefacts (answer per m², label per-m² unit unreadable). The paper should use "
             "rule A because it is the comparison that produced the error class itself, and should report the v2 figure "
             "alongside (and the adjudicated figure once available)." % (
                 A.at["absolute_for_relative", "v1"], A.at["relative_for_absolute", "v1"], B.at["absolute_for_relative", "v1"],
                 B.at["relative_for_absolute", "v1"], C.at["absolute_for_relative", "v1"], C.at["relative_for_absolute", "v1"],
                 A.at["absolute_for_relative", "v2"], A.at["relative_for_absolute", "v2"],
                 A.at["relative_for_absolute", "v1"] - A.at["relative_for_absolute", "v2"]))
    md += ["", recon, "", "## C3 Tables", "",
           "- `results/journal5/rd2/analysis/rd2full.tex` (CSV: `rd2_rates_all.csv`)",
           "- `results/journal5/rd2/analysis/rd2paired.tex` (CSV: `rd2_paired_all.csv`)",
           "- `results/journal5/rd2/analysis/rd2gen.tex` (CSV: `rd2_gen.csv`)", "",
           "## C4 No-dose sensitivity", "", c4["note"],
           " Parseable under v2: %d (%s); entering the error set: %d; entering the correct set: %d; checker verdicts available for "
           "no-dose answers: %d of %d." % (c4["parseable_under_v2"], ", ".join("%s %d" % kv for kv in sorted(c4["parseable_v2_classes"].items())),
                                           c4["parseable_entering_error_set"], c4["parseable_entering_correct_set"],
                                           c4["no_dose_scored_by_checkers"], c4["no_dose_v1"])]
    with open(os.path.join(OUT, "rd2_analysis_extra.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")

    # ---- Part D
    am_commit = git("log", "-1", "--format=%H", "--", "prereg/rd2_amendment_1.md")
    am_date = git("log", "-1", "--format=%cI", "--", "prereg/rd2_amendment_1.md")
    sheet = json.load(open(os.path.join(AM, "sheet_manifest.json")))
    relab = json.load(open(os.path.join(AM, "relabel_manifest.json")))
    bc = read_jsonl(os.path.join(RD2_DIR, "basis_check", "per_item.jsonl"))
    src = lambda f: "results/journal5/rd2/" + f  # noqa: E731
    S = "scripts/journal5/rd2_analysis_extra.py"

    def classes(L):
        t = lab.groupby(["class_" + L, "condition"]).size().unstack(1).fillna(0).astype(int)
        return {c: {"closed": int(t.at[c, "closed"]), "grounded": int(t.at[c, "grounded"]), "total": int(t.loc[c].sum())} for c in t.index}

    def rate_obj(d, L, sub, name, st):
        r = d[(d["label_set"] == L) & (d["subset"] == sub) & (d["system"] == name) & (d["set"] == st)]
        if not len(r):
            return None
        r = r.iloc[0]
        o = OrderedDict([("k", int(r["k_pass"])), ("n", int(r["n"])), ("rate", round(float(r["pass_rate"]), 6)),
                         ("qid_ci", [round(float(r["qid_lo"]), 6), round(float(r["qid_hi"]), 6)])])
        if "wilson_lo" in r and sub == "all":
            o["wilson_ci"] = [round(float(r["wilson_lo"]), 6), round(float(r["wilson_hi"]), 6)]
            o["drug_ci"] = [round(float(r["drug_lo"]), 6), round(float(r["drug_hi"]), 6)]
        o["parse_fail"] = int(r["parse_fail"])
        o["rate_pf_as_fail"] = round(float(r["pass_rate_pf_as_fail"]), 6)
        return o

    def basis_stats(L):
        ref = reference(lab, L)
        out = {}
        for v in ("full", "strict"):
            fl = {r["instance_id"] for r in bc if r["flag_" + v]}
            ab = sum(r["status_" + v] == "abstain" for r in bc)
            err, cor = set(ref.index[ref == "error"]), set(ref.index[ref == "nonerror"])
            out[v] = OrderedDict([("flagged", len(fl)), ("scored", len(bc)), ("flag_rate", round(len(fl) / len(bc), 6)),
                                  ("recall_on_errors", [len(fl & err), len(err)]),
                                  ("false_alarms_on_correct", [len(fl & cor), len(cor)]),
                                  ("ppv_vs_auto_errors", [len(fl & err), len(fl)]), ("abstentions", ab),
                                  ("status_no_dose", sum(r["status_" + v] == "no_dose" for r in bc))])
        return out

    def paired_obj(df):
        out = []
        for _, r in df.iterrows():
            out.append(OrderedDict([(k, (round(float(r[k]), 6) if isinstance(r[k], (float, np.floating)) else
                                         (int(r[k]) if isinstance(r[k], (int, np.integer)) else r[k]))) for k in df.columns]))
        return out

    D = OrderedDict()
    D["meta"] = OrderedDict([("generated", time.strftime("%Y-%m-%dT%H:%M:%S%z")), ("script", S),
                             ("status", "PROVISIONAL automatic labels; no human (pharmacist) label used"),
                             ("label_sets", {"v1": "pre-registered rd_extract.classify", "v2": "amendment 1 m2 pre-pass (labels_v2.jsonl)"}),
                             ("amendment", {"file": "prereg/rd2_amendment_1.md", "commit": am_commit, "date": am_date}),
                             ("n_boot_qid", NB_QID), ("n_boot_drug", NB_DRUG), ("seed", SEED)])
    D["totals"] = OrderedDict([("_source", "results/journal5/rd2/amend1/labels_v2.jsonl (scripts/journal5/rd2_relabel_v2.py); "
                                           "also amend1/relabel_diff.md"),
                               ("answers", len(lab)), ("scored_by_checkers", int(lab["scored"].sum())),
                               ("class_by_condition", {L: classes(L) for L in LSETS}),
                               ("unit_plus_basis", {L: int(lab["class_" + L].isin(UNIT_TYPE).sum()) for L in LSETS}),
                               ("changed_items_v1_to_v2", relab["changed_items"])])
    D["systems"] = OrderedDict([("_source", src("analysis/rd2_rates_all.csv") + " (" + S + ")"), ("rows", OrderedDict(
        (name, {L: {st: rate_obj(full, L, "all", name, st) for st in SETS} for L in LSETS}) for name in table_names))])
    D["closed_grounded"] = OrderedDict([("_source", src("analysis/c1_condition_rates.csv") + " (" + S + ")"), ("answer", answer),
                                        ("rows", OrderedDict((name, {L: {sub: {st: rate_obj(cond, L, sub, name, st) for st in SETS}
                                                                         for sub in ("closed", "grounded")} for L in LSETS})
                                                             for name in MAIN + FT if name in names)),
                                        ("ft_vs_base_closed_mcnemar", paired_obj(pmc))])
    D["paired_64"] = OrderedDict([("_source", src("analysis/rd2_paired_all.csv") + " (" + S + ")"), ("rows", paired_obj(pm))])
    D["basis_check"] = OrderedDict([("_source", src("basis_check/per_item.jsonl") + " (frozen basis check fdb95de); " + S),
                                    ("stats", {L: basis_stats(L) for L in LSETS})])
    D["subtypes"] = OrderedDict([("_source", src("analysis/c2_subtypes_per_item.csv") + " (" + S + ")"),
                                 ("subtype4", {L: {k: int(st4.at[k, L]) for k in st4.index} for L in LSETS}),
                                 ("direction_rule_A", {L: {k: int(A.at[k, L]) for k in A.index} for L in LSETS}),
                                 ("direction_rule_B", {L: {k: int(B.at[k, L]) for k in B.index} for L in LSETS}),
                                 ("direction_rule_C", {L: {k: int(C.at[k, L]) for k in C.index} for L in LSETS}),
                                 ("reconciliation", recon)])
    D["generator_condition"] = OrderedDict([("_source", src("analysis/rd2_gen.csv") + " (" + S + ")"),
                                            ("rows", json.loads(gt.to_json(orient="records")))])
    D["nodose"] = OrderedDict([("_source", src("analysis/c4_nodose_sensitivity.json") + " and amend1/nodose_rescan.md"),
                               ("rescan", relab["nodose"]), ("sensitivity", c4)])
    D["sheet"] = OrderedDict([("_source", "results/journal5/rd2/amend1/sheet_manifest.json, sheet_strata.md (scripts/journal5/rd2_sheet_v2.py)"),
                              ("rows", sheet["sheet_rows"]), ("v1_rows", sheet["v1_sheet_rows_reproduced"]),
                              ("added_vs_v1", sheet["rows_added_vs_v1"]), ("reconciliation", sheet["reconciliation"]),
                              ("population_by_stratum", sheet["population_by_stratum"]), ("sheet_by_stratum", sheet["sheet_by_stratum"]),
                              ("P1_rows", sheet["P1_rows"]), ("P1_by_group", sheet["P1_by_group"]), ("P1_by_stratum", sheet["P1_by_stratum"]),
                              ("overlap_rows", sheet["overlap_rows"]), ("sha256", sheet["sha256"])])
    with open(os.path.join(OUT, "paper_numbers_rd2.json"), "w") as fh:
        json.dump(D, fh, indent=1)
        fh.write("\n")

    P = ["# RD2 paper numbers (PROVISIONAL automatic labels; v1 = pre-registered, v2 = amendment 1)", "",
         "Generated %s by `%s`. Amendment: `prereg/rd2_amendment_1.md`, commit `%s` (%s). Machine-readable: "
         "`results/journal5/rd2/analysis/paper_numbers_rd2.json`. No pharmacist label has been used." % (
             D["meta"]["generated"], S, am_commit, am_date), "",
         "## Totals (source: amend1/labels_v2.jsonl, amend1/relabel_diff.md)", "",
         "| class | v1 closed | v1 grounded | v1 total | v2 closed | v2 grounded | v2 total |", "|---|---|---|---|---|---|---|"]
    cls = D["totals"]["class_by_condition"]
    for c in ("correct", "unit_error", "basis_error", "value_error", "match_other_context", "time_ambiguous", "unverifiable", "no_dose"):
        P.append("| %s | %s |" % (c, " | ".join("%d | %d | %d" % (cls[L][c]["closed"], cls[L][c]["grounded"], cls[L][c]["total"]) for L in LSETS)))
    P += ["| **total** | %s |" % " | ".join("%d | %d | %d" % (sum(v["closed"] for v in cls[L].values()), sum(v["grounded"] for v in cls[L].values()),
                                                             sum(v["total"] for v in cls[L].values())) for L in LSETS),
          "", "Unit + basis errors: v1 %d, v2 %d. Answers scored by checkers: %d of %d (the no-dose answers were not scored)." % (
              D["totals"]["unit_plus_basis"]["v1"], D["totals"]["unit_plus_basis"]["v2"], D["totals"]["scored_by_checkers"], len(lab)),
          "", "## Per-system PASS rates, all answers (source: analysis/rd2_rates_all.csv; Wilson / drug-cluster 5,000 / question-cluster 10,000)", "",
          "| system | labels | PASS on errors | Wilson | drug | question | PASS on correct | Wilson | drug | question | PF err/corr |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name in table_names:
        for L in LSETS:
            e, c = D["systems"]["rows"][name][L]["error"], D["systems"]["rows"][name][L]["nonerror"]
            P.append("| %s | %s | %s | %s/%s |" % (name, L, " | ".join("%d/%d = %s | %s | %s | %s" % (
                o["k"], o["n"], pc(o["rate"]), ci(*o["wilson_ci"]), ci(*o["drug_ci"]), ci(*o["qid_ci"])) for o in (e, c)),
                e["parse_fail"], c["parse_fail"]))
    P += ["", "## Closed-book / grounded (source: analysis/c1_condition_rates.csv, analysis/c1_ft_mcnemar_closed.csv)", "", answer,
          "", "See `analysis/rd2_analysis_extra.md` section C1 for every system.", "",
          "## Paired comparisons (source: analysis/rd2_paired_all.csv; 64 per label set, Holm within label set)", "",
          "| labels | base | other | set | n | b/c | Δ pp [CI] | p | p Holm |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in pm.iterrows():
        P.append("| %s | %s | %s | %s | %d | %d/%d | %s %s | %.3g | %.3g |" % (
            r["label_set"], r["base"], r["other"], r["set"], r["n_paired"], r["b_base_pass_other_fail"], r["c_base_fail_other_pass"],
            pc(r["delta_pass_rate"]), ci(r["delta_ci_lo_qid"], r["delta_ci_hi_qid"]), r["p"], r["p_holm_all"]))
    P += ["", "## Basis check (source: basis_check/per_item.jsonl)", "",
          "| variant | labels | flagged / scored | recall on auto errors | false alarms on auto correct | flagged that are auto errors | abstentions |",
          "|---|---|---|---|---|---|---|"]
    for v in ("full", "strict"):
        for L in LSETS:
            b = D["basis_check"]["stats"][L][v]
            P.append("| %s | %s | %d/%d = %s%% | %d/%d | %d/%d | %d/%d | %d |" % (
                v, L, b["flagged"], b["scored"], pc(b["flag_rate"]), *b["recall_on_errors"], *b["false_alarms_on_correct"],
                *b["ppv_vs_auto_errors"], b["abstentions"]))
    P += ["", "## Subtypes (source: analysis/c2_subtypes_per_item.csv)", "", "| subtype | v1 | v2 |", "|---|---|---|"] + [
        "| %s | %d | %d |" % (k, st4.at[k, "v1"], st4.at[k, "v2"]) for k in st4.index] + [
        "", "Direction, committed rule A: absolute for relative v1 %d / v2 %d; relative for absolute v1 %d / v2 %d." % (
            A.at["absolute_for_relative", "v1"], A.at["absolute_for_relative", "v2"], A.at["relative_for_absolute", "v1"],
            A.at["relative_for_absolute", "v2"]), "", recon, "",
        "## No-dose (source: amend1/nodose_rescan.md, analysis/c4_nodose_sensitivity.json)", "", c4["note"], "",
        "## Adjudication sheet (source: amend1/sheet_manifest.json, amend1/sheet_strata.md)", "",
        "Sheet v2 %d rows (v1 sheet %d + %d added: %s); P1 %d rows (%s); overlap %d rows." % (
            sheet["sheet_rows"], sheet["v1_sheet_rows_reproduced"], sheet["rows_added_vs_v1"],
            ", ".join("%s %d" % kv for kv in sheet["reconciliation"].items()), sheet["P1_rows"],
            ", ".join("%s %d" % kv for kv in sheet["P1_by_group"].items()), sheet["overlap_rows"]),
        "", "sha256: sheet v2 `%s`; key v2 `%s` (not committed)." % (sheet["sha256"]["sheet_v2"], sheet["sha256"]["key_v2"])]
    with open(os.path.join(OUT, "paper_numbers_rd2.md"), "w") as fh:
        fh.write("\n".join(P) + "\n")
    with open(os.path.join(OUT, "analysis_meta.json"), "w") as fh:
        json.dump({"script": S, "elapsed_s": round(time.time() - t0, 1), "n_boot_qid": NB_QID, "n_boot_drug": NB_DRUG, "seed": SEED,
                   "inputs_sha256": {f: R.sha256_file(os.path.join(RD2_DIR, f)) for f in
                                     ("real_dose/instances.jsonl", "amend1/labels_v2.jsonl", "basis_check/per_item.jsonl")}}, fh, indent=1)
        fh.write("\n")
    print(answer)
    print(recon)
    print("done in %.1fs -> %s" % (time.time() - t0, rel(OUT)))


if __name__ == "__main__":
    main()
