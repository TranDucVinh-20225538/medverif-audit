#!/usr/bin/env python3
"""(J4-TS) Threshold sensitivity of the audited checkers on the REAL drug-dose answers (RD set, 1451 answers vs FDA labels).

Reviewer question: "could tuning the checker threshold catch real dose/basis errors, and at what cost on correct answers?"
Post hoc, exploratory; no model calls, CPU only; reads committed score files, writes new files only.

Groups (same definitions as scripts/journal4/frontier_judges_rd.py / scripts/journal3/j3_report.py RD_GROUPS):
  negatives  auto-correct : auto_class == "correct"                         (n = 1062; labels automatic, PRESUMED correct)
  positives  true12       : qc/ai_precheck_real_dose_unit_errors.csv ai_label == "true_unit_error" (n = 12; AI-labelled)
             flagged47    : auto_class in {unit_error, basis_error}          (n = 47; automatic flags, incl. 12 AI-judged
                            parser artefacts on correct answers -> noisy positives, reported for context)
             value93      : auto_class == "value_error"                      (n = 93; automatic; context only)
Decision rule (paper / j3_common.verdict_map): PASS iff score > t, FAIL iff score <= t; default t = 0.5 for every
score-based checker (paper, Supplementary "Verifiers"; verified here to reproduce every stored verdict).
Score = higher means "more supported".  AUROC = P(score(correct) > score(error)) + 0.5 P(tie), i.e. the same orientation
as the card's AUC(conversion > 1000-fold swap): 0.5 = chance, 1 = every correct answer outranks every error.

Checkers
  paper (released, journal-2 RD scores): MiniCheck-RoBERTa, MiniCheck-DeBERTa, MiniCheck-Flan-T5, AlignScore-base,
        AlignScore-large  -- continuous.  RAGAS x Llama-3.3-70B and MedScore x Mistral-24B -- binary API judges, one
        operating point each (no threshold to tune).
  UNF v1 / v2 in front of the 5 paper checkers: rows in results/journal2/unf_heldout/rd_pack.jsonl use the re-score
        (rd_scores/<unf|unf_v2>/), all other rows keep the stored raw score (= paper / unf_heldout_report rule).
  FT (journal 3): MiniCheck-Flan-T5 and AlignScore-large, base / r0.5 / r1 / r2 (rd_raw); base and r1 also with UNF v2
        (rdunf_unf_v2 for pack rows, rd_raw otherwise; = j3_report.rdpair_metrics rule).
  local LLM judges (journal 3/4; extra): p_yes from verdict-token logprobs (missing -> 0/1 score, = j3 convention);
        default point = strict verdict, parse failures excluded.
Per checker x positive set: default-threshold counts; AUROC with 95% CIs (B = 10000, seed 20261001; drug-clustered =
primary, matching the paper's RD CIs; stratified case bootstrap = sensitivity); threshold needed to FAIL k of the
positives (k = 6, 9, 12 for true12; 24, 36, 47 for flagged47) and the resulting % of auto-correct answers FAILED
(drug-clustered CI, threshold re-derived in each resample with k scaled to the resampled positives); positives caught
at a fixed cost (5 / 10 / 20 % of correct answers failed).  Contrast: constructed-error AUCs already in the paper
(card claim side conversion vs 1000-fold swap, results/journal/threshold_robustness.json; held-out real dose strings
S vs U, results/journal2/unf_heldout/report.json and results/journal3/report.json ft_ho).

Outputs (results/journal4/threshold_sweep/): table.csv, cases.csv (12 errors), curves.csv (ROC corner points of every sweep), report.md, report.json,
fig_threshold_rd.{pdf,png}.   Python >= 3.8; numpy; matplotlib (figure only; --no-fig to skip).
Usage: python scripts/journal4/threshold_sweep_rd.py [--boot 10000] [--no-fig]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
from collections import OrderedDict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RD = ROOT / "results" / "journal2" / "real_dose"
RD_SCORES = RD / "scores"
UNF_RD = ROOT / "results" / "journal2" / "unf_heldout" / "rd_scores"
UNF_PACK = ROOT / "results" / "journal2" / "unf_heldout" / "rd_pack.jsonl"
FT_SCORES = ROOT / "results" / "journal3" / "ft" / "scores"
JUDGE_SCORES = ROOT / "results" / "journal3" / "judges" / "scores"
PRECHECK = ROOT / "qc" / "ai_precheck_real_dose_unit_errors.csv"
CARD_JSON = ROOT / "results" / "journal" / "threshold_robustness.json"
HO_JSON = ROOT / "results" / "journal2" / "unf_heldout" / "report.json"
J3_JSON = ROOT / "results" / "journal3" / "report.json"
OUT = ROOT / "results" / "journal4" / "threshold_sweep"
SEED = 20261001
DEFAULT_T = 0.5
TZ7 = dt.timezone(dt.timedelta(hours=7))

# key, display, stored RD score file, unf_heldout checker file stem, card json key, held-out report name
PAPER = [
    ("minicheck_roberta", "MiniCheck-RoBERTa", "t6_minicheck_roberta.jsonl", "t6a_minicheck_roberta", "t6a_minicheck_roberta", "MiniCheck-RoBERTa"),
    ("minicheck_deberta", "MiniCheck-DeBERTa", "t6_minicheck_deberta.jsonl", "t6a_minicheck_deberta", "t6a_minicheck_deberta", "MiniCheck-DeBERTa"),
    ("minicheck_flant5", "MiniCheck-Flan-T5", "v2a_minicheck.jsonl", "v2a_minicheck", "v2a_minicheck", "MiniCheck-Flan-T5-Large"),
    ("alignscore_base", "AlignScore-base", "t6_alignscore_base.jsonl", "t6a_alignscore_base", "t6a_alignscore_base", "AlignScore-base"),
    ("alignscore_large", "AlignScore-large", "v3_alignscore.jsonl", "v3_alignscore", "v3_alignscore", "AlignScore-large"),
]
BINARY = [("ragas_llama70b", "RAGAS x Llama-3.3-70B", "v4_ragas_nli.jsonl"),
          ("medscore_mistral24b", "MedScore x Mistral-24B", "v1_medscore.jsonl")]
FT_MODELS = [("minicheck_ft5", "MiniCheck-Flan-T5"), ("alignscore_large", "AlignScore-large")]
FT_TAGS = ["base", "r0.5", "r1", "r2"]
JUDGES = [("qwen25_0p5b", "Qwen2.5-0.5B"), ("qwen25_1p5b", "Qwen2.5-1.5B"), ("qwen25_3b", "Qwen2.5-3B"),
          ("qwen25_7b", "Qwen2.5-7B"), ("qwen25_14b", "Qwen2.5-14B"), ("llama31_8b", "Llama-3.1-8B"),
          ("medgemma_4b", "MedGemma-4B"), ("medgemma_27b", "MedGemma-27B-text"), ("baichuan_m2_32b", "Baichuan-M2-32B")]
KS = {"true12": [6, 9, 11, 12], "flagged47": [24, 36, 47], "value93": [47, 70, 93], "true12_samenum": [3, 6], "true12_diffnum": [3, 6]}
# (positives, negatives, families) ; first three = primary analyses, rest = sensitivity / descriptive
PAIRS = [("true12", "correct", None), ("flagged47", "correct", None), ("value93", "correct", None),
         ("true12", "correct_closed", ("paper", "paper_judge", "unf", "ft")),
         ("true12_samenum", "correct", ("paper", "paper_judge")), ("true12_diffnum", "correct", ("paper", "paper_judge"))]
PAIR_SALT = {("true12", "correct"): 1, ("flagged47", "correct"): 2, ("value93", "correct"): 3, ("true12", "correct_closed"): 4,
             ("true12_samenum", "correct"): 5, ("true12_diffnum", "correct"): 6}
FPRS = [0.05, 0.10, 0.20]


def read_jsonl(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def git_head():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        return None


# ---------------------------------------------------------------- loading
def load_groups():
    inst = read_jsonl(RD / "instances.jsonl")
    with PRECHECK.open(encoding="utf-8") as fh:
        pre = {r["instance_id"]: r["ai_label"] for r in csv.DictReader(l for l in fh if not l.startswith("#"))}
    cls = {r["instance_id"]: r["auto_class"] for r in inst}
    g = OrderedDict()
    g["correct"] = [r["instance_id"] for r in inst if r["auto_class"] == "correct"]
    g["true12"] = [r["instance_id"] for r in inst if pre.get(r["instance_id"]) == "true_unit_error"]
    g["flagged47"] = [r["instance_id"] for r in inst if r["auto_class"] in ("unit_error", "basis_error")]
    g["value93"] = [r["instance_id"] for r in inst if r["auto_class"] == "value_error"]
    # sensitivity: closed-book correct answers only (11 of the 12 confirmed errors are closed-book answers, whose wording
    # differs from the label; most correct answers are grounded, near-verbatim copies) and the two halves of true12
    g["correct_closed"] = [r["instance_id"] for r in inst if r["auto_class"] == "correct" and r["answer_condition"] == "closed"]
    g["true12_samenum"] = [i for i in g["true12"] if cls[i] == "unit_error"]      # label's number kept, unit/basis wrong
    g["true12_diffnum"] = [i for i in g["true12"] if cls[i] == "basis_error"]     # basis dropped AND number differs
    drug = {r["instance_id"]: r["drug"] for r in inst}
    assert (len(inst), len(g["correct"]), len(g["true12"]), len(g["flagged47"])) == (1451, 1062, 12, 47), \
        (len(inst), {k: len(v) for k, v in g.items()})
    return inst, g, drug


def stored_scores(path, key="score"):
    out, verd = {}, {}
    for r in read_jsonl(path):
        s = r.get("p_yes") if r.get("p_yes") is not None else r.get(key)
        if s is not None:
            out[r["instance_id"]] = float(s)
        verd[r["instance_id"]] = r.get("verdict")
    return out, verd


def merged(raw, variant_file, pack_ids):
    v, _ = stored_scores(variant_file)
    out = dict(raw)
    miss = [i for i in pack_ids if i not in v]
    assert not miss, "%s lacks %d pack rows" % (variant_file, len(miss))
    for i in pack_ids:
        out[i] = v[i]
    return out


def build_checkers():
    pack_ids = [r["instance_id"] for r in read_jsonl(UNF_PACK)]
    C = []  # dicts: key, name, family, scores, verdicts (for default point), kind
    for key, name, f, unf_stem, card_key, ho_name in PAPER:
        raw, verd = stored_scores(RD_SCORES / f)
        bad = sum(1 for i, s in raw.items() if ("PASS" if s > DEFAULT_T else "FAIL") != verd[i])
        assert bad == 0, "%s: default threshold does not reproduce %d stored verdicts" % (name, bad)
        C.append(dict(key=key, name=name, family="paper", text="raw", kind="continuous", scores=raw, base=key,
                      card_key=card_key, ho_name=ho_name, ho_pack="orig"))
        for var, lab in (("unf", "UNF v1"), ("unf_v2", "UNF v2")):
            C.append(dict(key="%s__%s" % (key, var), name="%s + %s" % (name, lab), family="unf", text=lab, kind="continuous",
                          scores=merged(raw, UNF_RD / var / (unf_stem + ".jsonl"), pack_ids), base=key, ho_name=ho_name, ho_pack=var))
    for key, name, f in BINARY:
        _, verd = stored_scores(RD_SCORES / f)
        C.append(dict(key=key, name=name, family="paper_judge", text="raw", kind="binary", verdicts=verd, base=key))
    for m, mname in FT_MODELS:
        for tag in FT_TAGS:
            raw, verd = stored_scores(FT_SCORES / ("%s_%s__rd_raw.jsonl" % (m, tag)))
            bad = sum(1 for i, s in raw.items() if ("PASS" if s > DEFAULT_T else "FAIL") != verd[i])
            assert bad == 0, (m, tag, bad)
            C.append(dict(key="ft_%s_%s" % (m, tag), name="%s %s (J3)" % (mname, tag), family="ft", text="raw",
                          kind="continuous", scores=raw, base=m, ft_name="%s_%s" % (m, tag)))
            if tag in ("base", "r1"):
                C.append(dict(key="ft_%s_%s__unf_v2" % (m, tag), name="%s %s (J3) + UNF v2" % (mname, tag), family="ft_unf",
                              text="UNF v2", kind="continuous", base=m, ft_name="%s_%s" % (m, tag),
                              scores=merged(raw, FT_SCORES / ("%s_%s__rdunf_unf_v2.jsonl" % (m, tag)), pack_ids)))
    for slug, name in JUDGES:
        f = JUDGE_SCORES / ("%s__rd.jsonl" % slug)
        if not f.is_file():
            continue
        sc, verd = stored_scores(f)
        C.append(dict(key="judge_%s" % slug, name="%s (local judge, p_yes)" % name, family="local_judge", text="raw",
                      kind="continuous_judge", scores=sc, verdicts=verd, base=slug))
    return C


# ---------------------------------------------------------------- metrics
def auc_matrix(sn, sp):
    """C[i, j] = 1 if score(correct j) > score(error i), 0.5 if tied."""
    return (sn[None, :] > sp[:, None]).astype(float) + 0.5 * (sn[None, :] == sp[:, None])


def weights_cluster(rng, B, drugs_p, drugs_n):
    ud = sorted(set(drugs_p) | set(drugs_n))
    idx = {d: k for k, d in enumerate(ud)}
    W = rng.multinomial(len(ud), [1.0 / len(ud)] * len(ud), size=B).astype(float)
    return W[:, [idx[d] for d in drugs_p]], W[:, [idx[d] for d in drugs_n]]


def weights_strat(rng, B, n_p, n_n):
    return (rng.multinomial(n_p, [1.0 / n_p] * n_p, size=B).astype(float),
            rng.multinomial(n_n, [1.0 / n_n] * n_n, size=B).astype(float))


def boot_auc(C, wp, wn):
    ok = wp.sum(1) > 0
    num = np.einsum("bi,ij,bj->b", wp[ok], C, wn[ok])
    return num / (wp[ok].sum(1) * wn[ok].sum(1)), int((~ok).sum())


def cost_at_k(sp, sn, k):
    """threshold = k-th smallest positive score; FAIL iff score <= t; returns (t, % correct failed, n correct failed)."""
    t = float(np.sort(sp)[k - 1])
    nf = int((sn <= t).sum())
    return t, 100.0 * nf / len(sn), nf


def boot_cost(sp, sn, wp, wn, frac):
    """drug-clustered CI of % correct failed when the threshold is set to FAIL >= frac of the (resampled) positives."""
    o = np.argsort(sp, kind="mergesort")
    sp_s, wp_s = sp[o], wp[:, o]
    D = (sn[:, None] <= sp_s[None, :]).astype(float)          # n_neg x n_pos
    cost = (wn @ D) / wn.sum(1, keepdims=True)                 # B x n_pos
    cw = np.cumsum(wp_s, 1)
    tot = cw[:, -1:]
    ok = tot[:, 0] > 0
    reach = cw[ok] >= frac * tot[ok] - 1e-9
    j = reach.argmax(1)
    return 100.0 * cost[ok][np.arange(ok.sum()), j]


def caught_at_fpr(sp, sn, fpr):
    """largest threshold whose correct-FAIL rate <= fpr; returns (#positives FAILED, actual % correct failed, t)."""
    cand = np.unique(np.concatenate([sn, sp, [-np.inf]]))
    best = (-np.inf, 0.0)
    for t in cand:
        f = (sn <= t).mean()
        if f <= fpr + 1e-12:
            best = (t, f)
    t, f = best
    return int((sp <= t).sum()), 100.0 * f, (None if not np.isfinite(t) else float(t))


def curve(sp, sn):
    """ROC corner points only: for every level of the positives' FAIL rate, the first and last threshold at that level
    (enough to redraw the step curve exactly; keeps curves.csv small)."""
    ts = np.unique(np.concatenate([sp, sn]))
    ts = np.concatenate([[-np.inf], ts])
    fp = (sn[None, :] <= ts[:, None]).mean(1)
    tp = (sp[None, :] <= ts[:, None]).mean(1)
    keep = np.zeros(len(ts), bool)
    keep[0] = keep[-1] = True
    chg = np.flatnonzero(np.diff(tp) != 0)
    keep[chg] = True
    keep[chg + 1] = True
    return ts[keep], fp[keep], tp[keep]


def pct(x, nd=1):
    return None if x is None else round(float(x), nd)


def analyse(C, g, drug, B):
    rows, curves = [], []
    for ci, c in enumerate(C):
        for pos, neg, fams in PAIRS:
            if fams is not None and c["family"] not in fams:
                continue
            neg_ids, pos_ids = g[neg], g[pos]
            r = OrderedDict(checker=c["name"], key=c["key"], family=c["family"], text=c["text"], kind=c["kind"],
                            positives=pos, negatives=neg)
            if c["kind"] == "binary" or c["kind"] == "continuous_judge":
                v = c["verdicts"]
                pn = [i for i in neg_ids if v.get(i) in ("PASS", "FAIL")]
                pp = [i for i in pos_ids if v.get(i) in ("PASS", "FAIL")]
                r.update(n_pos_scored=len(pp), n_neg_scored=len(pn),
                         default_caught=sum(v[i] == "FAIL" for i in pp), default_correct_passed=sum(v[i] == "PASS" for i in pn))
                r["default_recall_pct"] = pct(100.0 * r["default_caught"] / len(pp)) if pp else None
                r["default_correct_pass_pct"] = pct(100.0 * r["default_correct_passed"] / len(pn))
                r["default_correct_fail_pct"] = pct(100.0 - r["default_correct_pass_pct"])
                if c["kind"] == "binary":
                    rows.append(r)
                    continue
            s = c["scores"]
            pn = [i for i in neg_ids if i in s]
            pp = [i for i in pos_ids if i in s]
            sn = np.array([s[i] for i in pn])
            sp = np.array([s[i] for i in pp])
            if c["kind"] == "continuous":
                r.update(n_pos_scored=len(pp), n_neg_scored=len(pn), default_threshold=DEFAULT_T,
                         default_caught=int((sp <= DEFAULT_T).sum()), default_correct_passed=int((sn > DEFAULT_T).sum()))
                r["default_recall_pct"] = pct(100.0 * r["default_caught"] / len(pp))
                r["default_correct_pass_pct"] = pct(100.0 * r["default_correct_passed"] / len(pn))
                r["default_correct_fail_pct"] = pct(100.0 - r["default_correct_pass_pct"])
            else:
                r["n_pos_scored_pyes"], r["n_neg_scored_pyes"] = len(pp), len(pn)
            Cm = auc_matrix(sn, sp)
            r["auroc"] = round(float(Cm.mean()), 4)
            rng = np.random.default_rng(SEED + 1000 * ci + PAIR_SALT[(pos, neg)])
            wpc, wnc = weights_cluster(rng, B, [drug[i] for i in pp], [drug[i] for i in pn])
            a, dropped = boot_auc(Cm, wpc, wnc)
            r["auroc_ci_lo"], r["auroc_ci_hi"] = [round(float(x), 4) for x in np.percentile(a, [2.5, 97.5])]
            r["boot_dropped_no_pos"] = dropped
            wps, wns = weights_strat(rng, B, len(pp), len(pn))
            a2, _ = boot_auc(Cm, wps, wns)
            r["auroc_strat_ci_lo"], r["auroc_strat_ci_hi"] = [round(float(x), 4) for x in np.percentile(a2, [2.5, 97.5])]
            for k in KS[pos]:
                kk = min(k, len(pp))
                t, cf, nf = cost_at_k(sp, sn, kk)
                bc = boot_cost(sp, sn, wpc, wnc, kk / len(pp))
                r["k%d_threshold" % k] = round(t, 6)
                r["k%d_correct_fail_pct" % k] = pct(cf)
                r["k%d_correct_fail_n" % k] = nf
                r["k%d_correct_fail_ci_lo" % k], r["k%d_correct_fail_ci_hi" % k] = [pct(x) for x in np.percentile(bc, [2.5, 97.5])]
            for f in FPRS:
                n, af, t = caught_at_fpr(sp, sn, f)
                r["caught_at_fpr%02d" % int(f * 100)] = n
                r["fpr%02d_actual_pct" % int(f * 100)] = pct(af, 2)
            r["max_score_pos"] = round(float(sp.max()), 6)
            r["n_correct_score_le_maxpos"] = int((sn <= sp.max()).sum())
            rows.append(r)
            ts, fp, tp = curve(sp, sn)
            for t, x, y in zip(ts, fp, tp):
                curves.append((c["key"], pos, neg, "" if not np.isfinite(t) else "%.8g" % t, "%.6f" % x, "%.6f" % y))
    return rows, curves


def contrast():
    out = {}
    card = json.loads(CARD_JSON.read_text())["checkers"]
    ho = json.loads(HO_JSON.read_text())["checkers"]
    j3 = json.loads(J3_JSON.read_text())
    for key, name, f, unf_stem, card_key, ho_name in PAPER:
        out[key] = {"card_claim_auc_conv_vs_swap": card[card_key]["inversion_floor"]["claim"]["auc_conv_vs_swap"],
                    "card_evid_auc_conv_vs_swap": card[card_key]["inversion_floor"]["evid"]["auc_conv_vs_swap"],
                    "heldout_auc_S_gt_U": {p: ho[ho_name]["packs"][p]["auc_S_gt_U"] for p in ("orig", "unf", "unf_v2")}}
    for m, _ in FT_MODELS:
        for tag in FT_TAGS:
            n = "%s_%s" % (m, tag)
            d = j3.get("ft_ho", {}).get(n) or {}
            out["ft_" + n] = {"heldout_auc_S_gt_U": {v: (d.get(v) or {}).get("auc_S_gt_U") for v in ("raw", "unf", "unf_v2")}}
    return out


# ---------------------------------------------------------------- outputs
def write_csv(rows, path):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def fmt_ci(r, a="auroc"):
    if r.get(a) is None:
        return "--"
    return "%.2f [%.2f, %.2f]" % (r[a], r[a + "_ci_lo"], r[a + "_ci_hi"])


def fmt_cost(r, k):
    v = r.get("k%d_correct_fail_pct" % k)
    if v is None:
        return "--"
    return "%.1f [%.1f, %.1f]" % (v, r["k%d_correct_fail_ci_lo" % k], r["k%d_correct_fail_ci_hi" % k])


def per_case(inst, g, C):
    """one row per AI-confirmed error: drug, answer mode, mechanism, and for each paper checker its score and the share of
    auto-correct answers that a threshold just catching this error would also FAIL."""
    with PRECHECK.open(encoding="utf-8") as fh:
        pre = {r["instance_id"]: r for r in csv.DictReader(l for l in fh if not l.startswith("#"))}
    byid = {r["instance_id"]: r for r in inst}
    pc = [c for c in C if c["family"] == "paper"]
    out = []
    for i in g["true12"]:
        p, r = pre[i], byid[i]
        row = OrderedDict(check_id=p["check_id"], instance_id=i, drug=r["drug"], answer_condition=r["answer_condition"],
                          auto_class=r["auto_class"], label_dose=p["label_dose_auto"], answer_dose=p["answer_dose_auto"],
                          ai_mechanism=p["ai_mechanism"])
        for c in pc:
            sn = np.array([c["scores"][j] for j in g["correct"]])
            s = c["scores"][i]
            row["score_" + c["key"]] = round(s, 3)
            row["cost_" + c["key"]] = round(100.0 * float((sn <= s).mean()), 1)
        out.append(row)
    out.sort(key=lambda x: -np.mean([x["cost_" + c["key"]] for c in pc]))
    return out


def write_report(rows, con, meta, cases, path):
    R = {(r["key"], r["positives"]): r for r in rows if r["negatives"] == "correct"}
    RC = {r["key"]: r for r in rows if r["negatives"] == "correct_closed"}
    L = ["# Threshold sensitivity on real dose answers (RD, 1451 answers) -- J4-TS", "",
         "Generated by `scripts/journal4/threshold_sweep_rd.py` at %s (repo HEAD before this commit: `%s`). **Post hoc, exploratory.** "
         "No model calls: reads committed score files only." % (meta["generated_at"], meta["git_head"]), "",
         "**Labels.** Negatives = automatically correct answers (n = 1062, %d drugs; labels automatic, *presumed* correct, not human-checked). "
         "Positives = the 12 unit/basis errors confirmed by the **AI** pre-check (`true12`, %d drugs; AI-labelled, not human), and, for context, "
         "all 47 automatic unit-type flags (`flagged47`; 12 of them are parser artefacts on correct answers per the same pre-check, "
         "so they are noisy positives) and 93 automatic value errors. With 12 positives one error = 8.3 recall points; every number "
         "here is provisional." % (meta["drugs"]["correct"], meta["drugs"]["true12"]), "",
         "**Rule.** FAIL iff score <= t (PASS iff score > t); default t = 0.5 for every score-based checker (reproduces all stored "
         "verdicts). AUROC = P(score(correct) > score(error)) + 0.5 P(tie); 0.5 = chance; same orientation as the card AUC "
         "(conversion > 1000-fold swap). CIs: 95%% percentile, B = %d, seed %d, drug-clustered (primary, as for all RD CIs in the "
         "paper; stratified case bootstrap in `table.csv`). Cost CIs re-derive the threshold in each resample (k scaled to the "
         "resampled positives); for k = 12/12 the threshold is the *maximum* error score, an extreme order statistic for which "
         "bootstrap CIs are unreliable (the point estimate sits near the upper limit because resamples often drop the hardest "
         "case) -- read the per-case table instead." % (meta["boot"], SEED), "",
         "**Did the paper already have this?** No. The paper sweeps thresholds (400 quantiles, best min(QI, US), cross-fitted Youden, "
         "inversion floor, AUC conversion-vs-swap) only on the constructed card (Table 2, Supplementary 'Operating points'), and reports "
         "AUC on constructed swaps of held-out real dose strings (Table 3B). On real answers (Table 4, Supplementary slips table, "
         "Table S7) it reports default-threshold verdicts only. No threshold sweep, ROC or AUROC on real RD errors exists in "
         "`main.tex` (v3), the briefs, or any repo report/script (searched `scripts/journal{2,3,4}`, `notes/`, `results/`).", ""]
    L += ["## 1. Paper checkers vs the 12 AI-confirmed errors (negatives: 1062 auto-correct answers)", "",
          "| checker | AUROC [95% CI] | default t=0.5: caught /12, % correct failed | % correct failed to catch 6/12 | 9/12 [CI] | 11/12 | 12/12 (t) | caught /12 at 5 / 10 / 20 % correct failed | AUROC, closed-book correct only (n=" + str(meta["n"]["correct_closed"]) + ") | card AUC conv>swap (claim) | held-out constructed AUC raw -> UNF v2 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, name, *_ in PAPER:
        r, c, rc = R[(key, "true12")], con[key], RC[key]
        L.append("| %s | %s | %d, %.1f | %.1f | %s | %.1f | %.1f (%.3f) | %d / %d / %d | %s | %.2f | %.2f -> %.2f |" % (
            name, fmt_ci(r), r["default_caught"], r["default_correct_fail_pct"], r["k6_correct_fail_pct"], fmt_cost(r, 9),
            r["k11_correct_fail_pct"], r["k12_correct_fail_pct"], r["k12_threshold"],
            r["caught_at_fpr05"], r["caught_at_fpr10"], r["caught_at_fpr20"], fmt_ci(rc),
            c["card_claim_auc_conv_vs_swap"], c["heldout_auc_S_gt_U"]["orig"], c["heldout_auc_S_gt_U"]["unf_v2"]))
    for key, name, _ in BINARY:
        r, rc = R[(key, "true12")], RC[key]
        L.append("| %s (binary) | -- | %d/%d, %.1f | -- | -- | -- | -- | -- | closed-book: %d/%d, %.1f | -- | -- |" % (
            name, r["default_caught"], r["n_pos_scored"], r["default_correct_fail_pct"], rc["default_caught"], rc["n_pos_scored"],
            rc["default_correct_fail_pct"]))
    L += ["", "'% correct failed to catch k/12' = share of the 1062 auto-correct answers FAILED by the threshold t = score of the "
          "k-th lowest-scoring confirmed error (false alarms). At the default the checkers already FAIL 9-11 of 12, so 6/12 and 9/12 "
          "are reached at or below the default; the question is the cost of the last 1-3 errors.", ""]
    # same vs different numeral
    L += ["## 2. Which errors are hard? (descriptive; n = 6 + 6, AI-labelled)", "",
          "`true12` splits into 6 automatic `unit_error` rows (the answer keeps the label's number but changes or drops the unit/basis, "
          "e.g. 0.7 mg vs 0.7 mg/kg) and 6 `basis_error` rows (basis dropped *and* the number differs, e.g. 500 mg vs 10 mg/kg).", "",
          "| checker | AUROC same-number (6) | default caught /6 | AUROC different-number (6) | default caught /6 |", "|---|---|---|---|---|"]
    for key, name, *_ in PAPER:
        a, b = R[(key, "true12_samenum")], R[(key, "true12_diffnum")]
        L.append("| %s | %s | %d | %s | %d |" % (name, fmt_ci(a), a["default_caught"], fmt_ci(b), b["default_caught"]))
    for key, name, _ in BINARY:
        a, b = R[(key, "true12_samenum")], R[(key, "true12_diffnum")]
        L.append("| %s (binary) | -- | %d | -- | %d |" % (name, a["default_caught"], b["default_caught"]))
    pk = [p[0] for p in PAPER]
    L += ["", "Per case (sorted by mean cost). Score = checker score; cost = % of auto-correct answers that a threshold just "
          "catching this error would also FAIL.", "",
          "| case | drug | mode | auto class | label dose | answer dose | AI mechanism | " + " | ".join("%s score (cost %%)" % p[1] for p in PAPER) + " |",
          "|" + "---|" * (7 + len(PAPER))]
    for x in cases:
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            x["check_id"], x["drug"], x["answer_condition"], x["auto_class"], x["label_dose"], x["answer_dose"], x["ai_mechanism"],
            " | ".join("%.2f (%.1f)" % (x["score_" + k], x["cost_" + k]) for k in pk)))
    # fixes
    L += ["", "## 3. Fixes (UNF in front of the paper checkers; journal-3 fine-tunes) vs true12", "",
          "| checker | AUROC [CI] | default: caught /12, % correct failed | % correct failed @9/12 [CI] | @11/12 | @12/12 | AUROC closed-book only | held-out constructed AUC S>U |",
          "|---|---|---|---|---|---|---|---|"]
    for c in [x for x in rows if x["positives"] == "true12" and x["negatives"] == "correct" and x["family"] in ("unf", "ft", "ft_unf")]:
        if c["family"] == "unf":
            base, var = c["key"].split("__")
            ho = "%.2f" % con[base]["heldout_auc_S_gt_U"][var]
        else:
            n = c["key"].split("__")[0][3:]
            v = con.get("ft_" + n, {}).get("heldout_auc_S_gt_U", {}).get("unf_v2" if c["family"] == "ft_unf" else "raw")
            ho = "%.2f" % v if v is not None else "--"
        L.append("| %s | %s | %d, %.1f | %s | %.1f | %.1f | %s | %s |" % (
            c["checker"], fmt_ci(c), c["default_caught"], c["default_correct_fail_pct"], fmt_cost(c, 9), c["k11_correct_fail_pct"],
            c["k12_correct_fail_pct"], fmt_ci(RC[c["key"]]) if c["key"] in RC else "--", ho))
    L += ["", "## 4. All 47 automatic unit-type flags and 93 automatic value errors (context; noisy positives)", "",
          "| checker | AUROC flagged47 [CI] | default: caught /47, % correct failed | % correct failed @24/47 | @36/47 [CI] | @47/47 | AUROC value93 [CI] |",
          "|---|---|---|---|---|---|---|"]
    for c in [x for x in rows if x["positives"] == "flagged47" and x["family"] in ("paper", "paper_judge", "unf", "ft", "ft_unf")]:
        v = R.get((c["key"], "value93"), {})
        if c["kind"] == "binary":
            L.append("| %s (binary) | -- | %d/%d, %.1f | -- | -- | -- | -- |" % (c["checker"], c["default_caught"], c["n_pos_scored"], c["default_correct_fail_pct"]))
            continue
        L.append("| %s | %s | %d, %.1f | %.1f | %s | %.1f | %s |" % (c["checker"], fmt_ci(c), c["default_caught"], c["default_correct_fail_pct"],
                                                                 c["k24_correct_fail_pct"], fmt_cost(c, 36), c["k47_correct_fail_pct"], fmt_ci(v)))
    L += ["", "Catching all 47 flags costs most correct answers, as expected: 12 of the 47 are parser artefacts on correct answers.", "",
          "## 5. Local LLM judges (extra; p_yes from verdict-token logprobs, missing -> 0/1, = journal-3 convention)", "",
          "Default = strict verdict, parse failures excluded (as in Table S7). AUROC uses every answer with a score.", "",
          "| judge | default: caught / scored true12, % correct failed (scored) | AUROC true12 [CI] | % correct failed @9/12 | @12/12 | AUROC flagged47 [CI] |",
          "|---|---|---|---|---|---|"]
    for c in [x for x in rows if x["positives"] == "true12" and x["family"] == "local_judge"]:
        f = R[(c["key"], "flagged47")]
        L.append("| %s | %d/%d, %.1f | %s | %.1f | %.1f | %s |" % (c["checker"].replace(" (local judge, p_yes)", ""), c["default_caught"], c["n_pos_scored"],
                                                          c["default_correct_fail_pct"], fmt_ci(c), c["k9_correct_fail_pct"], c["k12_correct_fail_pct"], fmt_ci(f)))
    L += ["", "## 6. Reading", ""] + meta["reading"] + ["",
          "Files: `table.csv` (one row per checker x positive set x negative set; all columns incl. stratified CIs, thresholds, "
          "caught-at-fixed-cost), `cases.csv` (per-case table), `curves.csv` (ROC corner points of each sweep: threshold, fraction of "
          "correct FAILED, fraction of positives FAILED), `report.json`, `fig_threshold_rd.{pdf,png}`.", ""]
    path.write_text("\n".join(L), encoding="utf-8")


def make_fig(rows, curves, con, path_stem):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    R = {(r["key"], r["positives"]): r for r in rows if r["negatives"] == "correct"}
    RC = {r["key"]: r for r in rows if r["negatives"] == "correct_closed"}
    cv = {}
    for key, pos, neg, t, x, y in curves:
        if neg == "correct":
            cv.setdefault((key, pos), []).append((float(x), float(y)))
    cols = {"minicheck_roberta": "#1f77b4", "minicheck_deberta": "#ff7f0e", "minicheck_flant5": "#2ca02c",
            "alignscore_base": "#d62728", "alignscore_large": "#9467bd"}
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.6), gridspec_kw={"width_ratios": [1, 1, 1.05]})
    for pi, (pos, npos, title) in enumerate([("true12", 12, "(a) 12 AI-confirmed unit/basis errors"),
                                             ("flagged47", 47, "(b) 47 automatic unit-type flags (noisy)")]):
        a = ax[pi]
        if pos == "true12":
            for k in (9, 11, 12):
                a.axhline(100.0 * k / 12, color="0.88", lw=0.7, zorder=0)
        for key, name, *_ in PAPER:
            pts = sorted(cv[(key, pos)])
            r = R[(key, pos)]
            a.step([100 * p[0] for p in pts], [100 * p[1] for p in pts], where="post", color=cols[key], lw=1.4,
                   label="%s (AUROC %.2f)" % (name, r["auroc"]))
            a.plot(r["default_correct_fail_pct"], 100.0 * r["default_caught"] / npos, "o", color=cols[key], ms=7, mec="k", mew=0.6)
        for (key, name, _), mk in zip(BINARY, ("s", "D")):
            r = R[(key, pos)]
            a.plot(r["default_correct_fail_pct"], 100.0 * r["default_caught"] / r["n_pos_scored"], mk, color="0.35", ms=7, mec="k",
                   mew=0.6, label="%s (binary)" % name.replace(" x ", " × "))
        a.plot([0, 100], [0, 100], ":", color="0.6", lw=0.8)
        a.set_xlim(0, 100)
        a.set_ylim(0, 103)
        a.set_xlabel("% of automatically correct answers FAILED (n = 1062)")
        a.set_ylabel("%% of errors FAILED (n = %d)" % npos)
        a.set_title(title, fontsize=10)
        a.legend(fontsize=6.5, loc="lower right")
    a = ax[2]
    keys = [p[0] for p in PAPER]
    y = np.arange(len(keys))[::-1].astype(float)
    a.axvline(0.5, color="0.6", ls=":", lw=0.8)
    a.plot([con[k]["card_claim_auc_conv_vs_swap"] for k in keys], y + 0.3, "v", color="0.45", ms=6,
           label="constructed: card, conversion vs 1000× swap")
    a.plot([con[k]["heldout_auc_S_gt_U"]["orig"] for k in keys], y + 0.15, "^", color="#8c564b", ms=6,
           label="constructed: held-out strings, correct vs swap")
    a.plot([con[k]["heldout_auc_S_gt_U"]["unf_v2"] for k in keys], y, "^", color="#e377c2", ms=6, mfc="none",
           label="constructed: same, after UNF v2")
    for rr, off, mk, mfc, lab in (([R[(k, "true12")] for k in keys], -0.15, "o", "k", "real: correct vs 12 confirmed errors"),
                                  ([RC[k] for k in keys], -0.3, "o", "w", "real: closed-book correct only")):
        a.errorbar([r["auroc"] for r in rr], y + off, xerr=[[r["auroc"] - r["auroc_ci_lo"] for r in rr], [r["auroc_ci_hi"] - r["auroc"] for r in rr]],
                   fmt=mk, color="k", mfc=mfc, ms=5, capsize=2, lw=0.9, label=lab + " (95% CI)")
    a.set_yticks(y)
    a.set_yticklabels([p[1] for p in PAPER], fontsize=8)
    a.set_xlim(0, 1)
    a.set_xlabel("AUC = P(score of correct item > score of error)")
    a.set_title("(c) Ranking: constructed vs real errors", fontsize=10)
    a.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.45, -0.17), ncol=1)
    fig.tight_layout()
    fig.savefig(str(path_stem) + ".pdf", bbox_inches="tight")
    fig.savefig(str(path_stem) + ".png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def rng_str(vals, nd=1):
    return ("%%.%df-%%.%df" % (nd, nd)) % (min(vals), max(vals))


def reading(rows):
    R = {(r["key"], r["positives"]): r for r in rows if r["negatives"] == "correct"}
    RC = {r["key"]: r for r in rows if r["negatives"] == "correct_closed"}
    P = [R[(k[0], "true12")] for k in PAPER]
    PC = [RC[k[0]] for k in PAPER]
    S = [R[(k[0], "true12_samenum")] for k in PAPER]
    D = [R[(k[0], "true12_diffnum")] for k in PAPER]
    return [
        "- Paper checkers vs true12: AUROC %s (drug-clustered CIs %.2f-%.2f overall); closed-book correct answers only: %s." % (
            rng_str([r["auroc"] for r in P], 2), min(r["auroc_ci_lo"] for r in P), max(r["auroc_ci_hi"] for r in P), rng_str([r["auroc"] for r in PC], 2)),
        "- At t = 0.5 they already FAIL %d-%d of 12 while failing %s%% of auto-correct answers. Catching 9/12 costs %s%%, 11/12 %s%%, "
        "12/12 %s%% of correct answers failed. At a 5%% / 10%% false-alarm budget they catch %d-%d / %d-%d of 12." % (
            min(r["default_caught"] for r in P), max(r["default_caught"] for r in P), rng_str([r["default_correct_fail_pct"] for r in P]),
            rng_str([r["k9_correct_fail_pct"] for r in P]), rng_str([r["k11_correct_fail_pct"] for r in P]),
            rng_str([r["k12_correct_fail_pct"] for r in P]), min(r["caught_at_fpr05"] for r in P), max(r["caught_at_fpr05"] for r in P),
            min(r["caught_at_fpr10"] for r in P), max(r["caught_at_fpr10"] for r in P)),
        "- The expensive errors are the ones that keep the label's number (same-number AUROC %s vs different-number %s; n = 6 each), "
        "i.e. the numeral-bound pattern of the card." % (rng_str([r["auroc"] for r in S], 2), rng_str([r["auroc"] for r in D], 2)),
        "- Constructed contrast: on the card the same checkers rank a correct conversion above a 1000-fold swap with AUC 0.09-0.38 "
        "(inverted); on held-out real dose strings constructed swaps reach 0.22-0.44 raw and 0.91-0.97 after UNF v2. Real errors "
        "are thus ranked *better* than constructed ones by the raw checkers, mostly because real errors usually also change the "
        "number and correct answers mostly copy the label's dose; the ranking does not translate into a usable operating point."]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--no-fig", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    inst, g, drug = load_groups()
    C = build_checkers()
    rows, curves = analyse(C, g, drug, args.boot)
    con = contrast()
    cases = per_case(inst, g, C)
    meta = {"generated_at": dt.datetime.now(TZ7).strftime("%Y-%m-%d %H:%M %z"), "git_head": git_head(), "boot": args.boot,
            "seed": SEED, "default_threshold": DEFAULT_T, "n": {k: len(v) for k, v in g.items()},
            "drugs": {k: len({drug[i] for i in v}) for k, v in g.items()}}
    meta["reading"] = reading(rows)
    write_csv(rows, OUT / "table.csv")
    write_csv(cases, OUT / "cases.csv")
    with (OUT / "curves.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "positives", "negatives", "threshold_fail_if_score_le", "frac_correct_failed", "frac_positives_failed"])
        w.writerows(curves)
    (OUT / "report.json").write_text(json.dumps({"meta": meta, "rows": rows, "cases": cases, "contrast": con}, indent=1) + "\n",
                                     encoding="utf-8")
    write_report(rows, con, meta, cases, OUT / "report.md")
    if not args.no_fig:
        make_fig(rows, curves, con, OUT / "fig_threshold_rd")
    print(json.dumps({"wrote": str(OUT), "n": meta["n"], "reading": meta["reading"]}, indent=1))


if __name__ == "__main__":
    main()
