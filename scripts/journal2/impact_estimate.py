#!/usr/bin/env python3
"""(IMPACT) Real-world impact estimate from the real-dose (RD) outputs (CPU, stdlib + numpy, no models, no API).

Question: per 1000 LLM dose answers, how many contain a dose error, and how many of those erroneous answers a
grounding checker lets through (verdict PASS at the paper's operating point, same as rd_report.py: stored
`verdict`, else score > 0.5) -- overall, by answer mode (grounded / closed-book) and by generator
(gpt-4o-mini / gemma-3-27b), broken down by automatic error type:
  any       = unit_error + basis_error + value_error (rd_extract.py primary error set)
  unit_type = unit_error + basis_error
  same_num  = unit_error (same numeral, other unit / basis)
  value     = value_error
Denominator = every answer that states a dose (results/journal2/real_dose/instances.jsonl; 5 no-dose answers
excluded).  time_ambiguous / unverifiable / match_other_context answers stay in the denominator as non-errors
(so the error rate is a lower bound); the `adjudicable` sensitivity drops time_ambiguous + unverifiable.

Slip-past per 1000 for a checker = #(error answers with PASS) / #(answers with a PASS/FAIL verdict) x 1000,
i.e. computed on the rows that checker scored (PARSE_FAIL and missing rows excluded and counted).  For a
checker with incomplete coverage (Llama-70B RAGAS: 1388/1451, all 63 missing rows are gemma-3-27b closed-book)
a post-stratified estimate (generator x mode cells reweighted to the full cell sizes) is reported as well.
Judges are picked up automatically when their score file appears (MedScore v1_medscore.jsonl, HPC job 62101).

UNF deployment (checker + unit normalization, src/unit_norm_fix.py, evidence mode): UNF is applied to every RD
(claim, evidence) pair here (cheap, deterministic).  Rows whose text UNF leaves unchanged keep their stored
verdict (identical input), so the slips among them are a hard floor.  Rows UNF changes need re-scoring with the
small checkers (HPC: jobs/journal2/jr2_UNFADV.sbatch -> scripts/journal2/unf_adv_score.py --set rd_unf);
until those scores exist the post-UNF number is reported as PENDING with [floor, ceiling] bounds.

Labels are AUTOMATIC (rule-based, rd_extract.py) pending human verification in qc/real_dose_errors_check.csv;
when human labels are present the human-confirmed variant is added.  A `suspected label-parsing artifact`
sensitivity drops unit/basis flags where the answer carries a /kg or /m2 denominator that the label sentence
does contain in raw text but the parser missed (e.g. "mg/m 2" from a lost superscript, "(mcg/kg)" table header).

CIs: percentile bootstrap resampling DRUGS as clusters (questions are nested in drugs; 10,000 resamples);
question-cluster CIs are also stored in the JSON.

Outputs: results/journal2/impact/impact.json, results/journal2/impact/rd_unf_pack.jsonl (rows UNF changes,
original + normalized text, for HPC re-scoring), notes/impact_estimate.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT / "src", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from unit_norm_fix import apply_unf_pair  # noqa: E402

RD = ROOT / "results/journal2/real_dose"
OUT = ROOT / "results/journal2/impact"
NOTE = ROOT / "notes/impact_estimate.md"
QC = ROOT / "qc/real_dose_errors_check.csv"
PACK = OUT / "rd_unf_pack.jsonl"
UNF_SCORES = OUT / "rd_unf_scores"
SEED = 20261001
# (score file, display name, small-checker id used for the UNF re-score or None)
CHECKERS = [("t6_minicheck_roberta.jsonl", "MiniCheck-RoBERTa", "t6a_minicheck_roberta"),
            ("t6_minicheck_deberta.jsonl", "MiniCheck-DeBERTa", "t6a_minicheck_deberta"),
            ("t6_alignscore_base.jsonl", "AlignScore-base", "t6a_alignscore_base"),
            ("v2a_minicheck.jsonl", "MiniCheck-Flan-T5-Large", "v2a_minicheck"),
            ("v3_alignscore.jsonl", "AlignScore-large", "v3_alignscore"),
            ("v4_ragas_nli.jsonl", "Llama-3.3-70B (RAGAS NLI)", None),
            ("v1_medscore.jsonl", "Mistral-Small-24B (MedScore)", None)]
ETYPES = {"any": {"unit_error", "basis_error", "value_error"}, "unit_type": {"unit_error", "basis_error"},
          "same_num": {"unit_error"}, "value": {"value_error"}}
ETYPE_LABEL = {"any": "any error", "unit_type": "unit-type", "same_num": "same numeral, other unit", "value": "value"}
GEN_LABEL = {"gpt4o_mini": "gpt-4o-mini", "gemma3_27b": "gemma-3-27b"}
STRATA = {"overall": lambda r: True, "grounded": lambda r: r["answer_condition"] == "grounded",
          "closed": lambda r: r["answer_condition"] == "closed", "gpt4o_mini": lambda r: r["generator"] == "gpt4o_mini",
          "gemma3_27b": lambda r: r["generator"] == "gemma3_27b"}
for _g in ("gpt4o_mini", "gemma3_27b"):
    for _m in ("grounded", "closed"):
        STRATA["%s|%s" % (_g, _m)] = (lambda g, m: (lambda r: r["generator"] == g and r["answer_condition"] == m))(_g, _m)
CELLS = [k for k in STRATA if "|" in k]


def read_jsonl(p: Path) -> list:
    if not Path(p).is_file():
        return []
    return [json.loads(l) for l in Path(p).open(encoding="utf-8") if l.strip()]


def verdicts(path: Path) -> dict:
    """Same rule as rd_report.verdicts (last row per id wins)."""
    out = {}
    for r in read_jsonl(path):
        v = r.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[r["instance_id"]] = v
        elif r.get("score") is not None:
            out[r["instance_id"]] = "PASS" if float(r["score"]) > 0.5 else "FAIL"
    return out


_M2_RAW = re.compile(r"/\s*m\s*2|/\s*m²|/\s*m\^2|per\s+square\s+met", re.I)
_KG_RAW = re.compile(r"\bkg\b|kilogram", re.I)


def artifact_suspect(x: dict) -> bool:
    """Unit/basis flag where the ANSWER has a /kg or /m2 denominator that the parsed label dose lacks although
    the raw label sentence contains it (lost superscript 'mg/m 2', '(mcg/kg)' table header, 'mcg of X per kg')."""
    if x["auto_class"] not in ("unit_error", "basis_error"):
        return False
    a, t, ts = x.get("primary") or "", x.get("matched") or "", x.get("target_sentence") or ""
    a_m2, t_m2 = bool(_M2_RAW.search(a)), bool(_M2_RAW.search(t))
    a_kg, t_kg = bool(_KG_RAW.search(a)), bool(_KG_RAW.search(t))
    return (a_m2 and not t_m2 and bool(_M2_RAW.search(ts))) or (a_kg and not t_kg and bool(_KG_RAW.search(ts)))


def human_labels() -> dict:
    out = {}
    if not QC.is_file():
        return out
    with QC.open(encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            lab = (r.get("human_answer_dose_is_error (Y/N/unclear)") or "").strip().upper()
            if lab:
                out[r["instance_id"]] = {"is_error": lab[:1],
                                         "type": (r.get("human_error_type (unit/basis/value/context/none)") or "").strip().lower()}
    return out


class Boot:
    """Cluster bootstrap on additive count features: feature matrix F (clusters x features), weights W (B x clusters)."""

    def __init__(self, clusters: list, n_boot: int, seed: int = SEED):
        self.ids = sorted(set(clusters))
        self.idx = {c: i for i, c in enumerate(self.ids)}
        self.row_c = np.array([self.idx[c] for c in clusters])
        m = len(self.ids)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(m, np.full(m, 1.0 / m), size=n_boot).astype(np.float64)  # B x m
        self.cache = {}

    def sums(self, mask: np.ndarray) -> tuple:
        """mask: per-row 0/1 (or counts). Returns (point_sum, boot_sums[B])."""
        key = mask.tobytes()
        if key not in self.cache:
            per_c = np.bincount(self.row_c, weights=mask.astype(np.float64), minlength=len(self.ids))
            self.cache[key] = (float(per_c.sum()), self.W @ per_c)
        return self.cache[key]


def ratio(bt: Boot, num: np.ndarray, den: np.ndarray, scale: float = 1000.0) -> dict:
    k, kb = bt.sums(num)
    n, nb = bt.sums(den)
    with np.errstate(divide="ignore", invalid="ignore"):
        rb = np.where(nb > 0, kb / nb, np.nan) * scale
    rb = rb[~np.isnan(rb)]
    ci = [float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))] if len(rb) and n else [None, None]
    return {"k": int(round(k)), "n": int(round(n)), "per": (scale * k / n) if n else None, "ci": ci}


def poststrat(bt: Boot, num: np.ndarray, den: np.ndarray, cells: dict, scale: float = 1000.0) -> dict:
    """sum_c rate_c * N_c / N over generator x mode cells (cells: name -> row mask over ALL answers, so N_c is the
    full cell size even where the checker has missing rows)."""
    pt_num, pt_den, b_num, b_den = 0.0, 0.0, 0.0, 0.0
    for cm in cells.values():
        k, kb = bt.sums(num * cm)
        n, nb = bt.sums(den * cm)
        Nc, Ncb = bt.sums(cm)
        pt_num += (k / n if n else 0.0) * Nc
        pt_den += Nc
        with np.errstate(divide="ignore", invalid="ignore"):
            b_num = b_num + np.where(nb > 0, kb / nb, 0.0) * Ncb
        b_den = b_den + Ncb
    rb = scale * b_num / b_den
    return {"per": scale * pt_num / pt_den, "ci": [float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))]}


def build_unf_pack(inst: list) -> dict:
    """Apply UNF to every RD pair; write the changed rows (both texts) for HPC re-scoring. Returns id -> changed."""
    changed, pack = {}, []
    for r in inst:
        c2, e2, info = apply_unf_pair(r["claim"], r["evidence"])
        ch = c2 != r["claim"] or e2 != r["evidence"]
        changed[r["instance_id"]] = ch
        if ch:
            pack.append({"instance_id": r["instance_id"], "base_id": r["drug"], "auto_class": r["auto_class"],
                         "claim_orig": r["claim"], "evidence_orig": r["evidence"], "claim_unf": c2, "evidence_unf": e2,
                         "unf_claim_changed": c2 != r["claim"], "unf_evidence_changed": e2 != r["evidence"],
                         "unf_edits": info["edits"], "valid": True})
    OUT.mkdir(parents=True, exist_ok=True)
    with PACK.open("w", encoding="utf-8") as fh:
        for r in pack:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return changed


def fmt(s: dict, nd: int = 1) -> str:
    if s.get("per") is None:
        return "NA"
    lo, hi = s["ci"]
    return ("%.*f [%.*f, %.*f]" % (nd, s["per"], nd, lo, nd, hi)) if lo is not None else "%.*f" % (nd, s["per"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--out-md", default=str(NOTE))
    ap.add_argument("--out-json", default=str(OUT / "impact.json"))
    ap.add_argument("--unf-scores", default=str(UNF_SCORES), help="RD-UNF re-scores root (override for smoke tests)")
    ap.add_argument("--precheck", default=None, help="AI pre-check CSV (e.g. qc/ai_precheck_real_dose_unit_errors.csv): "
                    "sensitivity analysis counting only ai_label == true_unit_error as unit-type errors; writes "
                    "impact_precheck.json + notes/real_dose_ai_precheck.md unless --out-* given. Default behaviour unchanged.")
    args = ap.parse_args()
    if args.precheck:
        run_precheck(args)
        return
    unf_scores = Path(args.unf_scores)
    inst = read_jsonl(RD / "instances.jsonl")
    ext = {r["instance_id"]: r for r in read_jsonl(RD / "extract_rows.jsonl")}
    if not inst:
        raise SystemExit("no RD instances")
    n_nodose = sum(1 for r in ext.values() if r["auto_class"] == "no_dose")
    N = len(inst)
    cls = np.array([r["auto_class"] for r in inst])
    smask = {s: np.array([1.0 if f(r) else 0.0 for r in inst]) for s, f in STRATA.items()}
    emask = {e: np.isin(cls, list(v)).astype(float) for e, v in ETYPES.items()}
    adjud = (~np.isin(cls, ["time_ambiguous", "unverifiable"])).astype(float)
    suspect = np.array([1.0 if artifact_suspect(ext.get(r["instance_id"], r)) else 0.0 for r in inst])
    hl = human_labels()
    if hl:
        hy = np.array([1.0 if hl.get(r["instance_id"], {}).get("is_error") == "Y" else 0.0 for r in inst])
        ht = [hl.get(r["instance_id"], {}).get("type", "") for r in inst]
        emask["human_any"] = hy
        emask["human_unit_type"] = hy * np.array([1.0 if t in ("unit", "basis") else 0.0 for t in ht])
        emask["human_value"] = hy * np.array([1.0 if t == "value" else 0.0 for t in ht])
    clusters = {"drug": [r["drug"] for r in inst], "question": [r["qid"] for r in inst]}
    boots = {k: Boot(v, args.boot) for k, v in clusters.items()}
    bt = boots["drug"]
    ones = np.ones(N)
    res = {"generated_by": "scripts/journal2/impact_estimate.py", "labels": "AUTOMATIC (rd_extract.py) pending human "
           "verification in qc/real_dose_errors_check.csv", "human_labelled_rows": len(hl), "n_dose_answers": N,
           "n_no_dose_answers_excluded": n_nodose, "n_drugs": len(set(clusters["drug"])), "n_questions": len(set(clusters["question"])),
           "bootstrap": {"resamples": args.boot, "cluster": "drug (primary); question in *_qcluster", "seed": SEED},
           "operating_point": "stored verdict, else score > 0.5 (as rd_report.py)", "class_counts": dict(Counter(cls.tolist())),
           "artifact_suspect_ids": [r["instance_id"] for r, s in zip(inst, suspect) if s],
           "prevalence": {}, "checkers": {}, "unf": {}}
    # --- prevalence per 1000 dose answers
    for s, sm in smask.items():
        d = res["prevalence"].setdefault(s, {"n_answers": int(sm.sum())})
        for e, em in emask.items():
            d[e] = ratio(bt, em * sm, sm)
            d[e + "_qcluster"] = ratio(boots["question"], em * sm, sm)
            d[e + "_adjudicable"] = ratio(bt, em * sm * adjud, sm * adjud)
        d["any_excl_artifact_suspect"] = ratio(bt, emask["any"] * (1 - suspect) * sm, sm)
        d["unit_type_excl_artifact_suspect"] = ratio(bt, emask["unit_type"] * (1 - suspect) * sm, sm)
    # --- UNF: which rows change
    changed = build_unf_pack(inst)
    chg = np.array([1.0 if changed[r["instance_id"]] else 0.0 for r in inst])
    res["unf"]["pack"] = str(PACK.relative_to(ROOT))
    res["unf"]["rows_changed"] = int(chg.sum())
    res["unf"]["changed_by_class"] = dict(Counter(c for c, x in zip(cls.tolist(), chg) if x))
    # --- checkers
    for fname, name, ck in CHECKERS:
        p = RD / "scores" / fname
        if not p.is_file():
            res["checkers"][name] = {"status": "missing (%s not present yet)" % fname}
            continue
        vd = verdicts(p)
        vv = [vd.get(r["instance_id"]) for r in inst]
        scored = np.array([1.0 if v in ("PASS", "FAIL") else 0.0 for v in vv])
        passed = np.array([1.0 if v == "PASS" else 0.0 for v in vv])
        cov = {"scored": int(scored.sum()), "of": N, "parse_fail": sum(1 for v in vv if v == "PARSE_FAIL"),
               "missing": sum(1 for v in vv if v is None),
               "missing_by_cell": dict(Counter("%s|%s" % (r["generator"], r["answer_condition"]) for r, v in zip(inst, vv) if v not in ("PASS", "FAIL")))}
        d = {"coverage": cov, "strata": {}}
        for s, sm in smask.items():
            ds = d["strata"].setdefault(s, {"n_scored": int((sm * scored).sum())})
            for e, em in emask.items():
                ds["slip_" + e] = ratio(bt, em * passed * sm, scored * sm)
                ds["miss_rate_" + e] = ratio(bt, em * passed * sm, em * scored * sm, scale=100.0)
            ds["slip_any_qcluster"] = ratio(boots["question"], emask["any"] * passed * sm, scored * sm)
            ds["slip_any_excl_artifact_suspect"] = ratio(bt, emask["any"] * (1 - suspect) * passed * sm, scored * sm)
            ds["slip_unit_type_excl_artifact_suspect"] = ratio(bt, emask["unit_type"] * (1 - suspect) * passed * sm, scored * sm)
            ds["correct_pass_pct"] = ratio(bt, (cls == "correct") * passed * sm, (cls == "correct") * scored * sm, scale=100.0)
        if cov["scored"] < N:
            cells = {c: smask[c] for c in CELLS}
            d["poststratified_overall"] = {e: poststrat(bt, emask[e] * passed, scored, cells) for e in ("any", "unit_type", "same_num", "value")}
        # --- UNF deployment (small checkers only)
        if ck:
            u = {"floor_unchanged_rows": {}, "ceiling": {}}
            for e in ("any", "unit_type", "same_num", "value"):
                u["floor_unchanged_rows"][e] = ratio(bt, emask[e] * passed * (1 - chg), scored)
                u["ceiling"][e] = ratio(bt, emask[e] * np.maximum(passed, chg) * scored, scored)
                u.setdefault("errors_changed_by_unf", {})[e] = int((emask[e] * chg).sum())
            after_vd = verdicts(unf_scores / "unf" / (ck + ".jsonl"))
            orig_vd = verdicts(unf_scores / "orig" / (ck + ".jsonl"))
            need = [r["instance_id"] for r, c in zip(inst, chg) if c]
            have = [i for i in need if after_vd.get(i) in ("PASS", "FAIL")]
            u["rescored_changed_rows"] = [len(have), len(need)]
            if need and len(have) == len(need):
                pa = np.array([(1.0 if after_vd[r["instance_id"]] == "PASS" else 0.0) if c else p_
                               for r, c, p_ in zip(inst, chg, passed)])
                for s, sm in smask.items():
                    for e in ("any", "unit_type", "same_num", "value"):
                        u.setdefault("after", {}).setdefault(s, {})[e] = ratio(bt, emask[e] * pa * sm, scored * sm)
                        u.setdefault("before", {}).setdefault(s, {})[e] = d["strata"][s]["slip_" + e]
                    u.setdefault("after", {}).setdefault(s, {})["correct_pass_pct"] = ratio(
                        bt, (cls == "correct") * pa * sm, (cls == "correct") * scored * sm, scale=100.0)
                agree = [orig_vd.get(i) == vd.get(i) for i in need if orig_vd.get(i) in ("PASS", "FAIL")]
                u["env_agreement_rescored_orig_vs_stored"] = [sum(agree), len(agree)]
                u["status"] = "done"
            else:
                u["status"] = "PENDING (HPC re-score of UNF-changed rows: %d/%d)" % (len(have), len(need))
            d["unf"] = u
        res["checkers"][name] = d
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(res, indent=1, default=str) + "\n")
    write_md(res, Path(args.out_md))
    print(json.dumps({"wrote": [args.out_json, args.out_md], "N": N,
                      "checkers": {k: v.get("status", "ok") for k, v in res["checkers"].items()}}))


def write_md(res: dict, path: Path) -> None:
    P = res["prevalence"]
    L = ["# Real-world impact estimate: dose errors per 1000 LLM answers", "",
         "Generated by `scripts/journal2/impact_estimate.py` from the real-dose outputs (`results/journal2/real_dose/`); "
         "JSON: `results/journal2/impact/impact.json`. **Error labels are automatic (rule-based, `rd_extract.py`) and "
         "pending human verification in `qc/real_dose_errors_check.csv` (%d rows labelled so far).**" % res["human_labelled_rows"], "",
         "Denominator: %d answers that state a dose (%d no-dose answers excluded; %d drugs, %d questions, 2 generators x "
         "grounded/closed-book). Checker = PASS at the paper's operating point (as `rd_report.py`). Slips = erroneous "
         "answers the checker PASSes, per 1000 dose answers scored by that checker. 95%% CIs: drug-clustered bootstrap "
         "(%d resamples)." % (res["n_dose_answers"], res["n_no_dose_answers_excluded"], res["n_drugs"], res["n_questions"],
                              res["bootstrap"]["resamples"]), "",
         "## Dose errors per 1000 dose answers", "",
         "| stratum | n | any error | unit-type | same numeral, other unit | value |", "|---|---|---|---|---|---|"]
    names = {"overall": "all answers", "grounded": "grounded", "closed": "closed-book", "gpt4o_mini": "gpt-4o-mini",
             "gemma3_27b": "gemma-3-27b"}
    for s in names:
        d = P[s]
        L.append("| %s | %d | %s | %s | %s | %s |" % (names[s], d["n_answers"], fmt(d["any"]), fmt(d["unit_type"]),
                                                        fmt(d["same_num"]), fmt(d["value"])))
    L += ["", "Sensitivities (all answers): adjudicable denominator (drop time_ambiguous + unverifiable) any error %s; "
          "excluding %d suspected label-parsing artifacts (answer has /kg or /m2 that the parser missed in the label, "
          "e.g. `mg/m 2`): any error %s, unit-type %s." % (fmt(P["overall"]["any_adjudicable"]), len(res["artifact_suspect_ids"]),
                                                         fmt(P["overall"]["any_excl_artifact_suspect"]),
                                                         fmt(P["overall"]["unit_type_excl_artifact_suspect"])), ""]
    L += ["## Erroneous answers that slip past each checker (per 1000 dose answers)", "",
          "| checker | coverage | any error | unit-type | same numeral, other unit | value | any, excl. suspected artifacts | miss rate (any) | grounded: any | closed-book: any | gpt-4o-mini: any | gemma-3-27b: any |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, d in res["checkers"].items():
        if "strata" not in d:
            L.append("| %s | %s | | | | | | | | | | |" % (name, d["status"]))
            continue
        o = d["strata"]
        mr = o["overall"]["miss_rate_any"]
        L.append("| %s | %d/%d | %s | %s | %s | %s | %s | %s%% | %s | %s | %s | %s |" % (
            name, d["coverage"]["scored"], d["coverage"]["of"], fmt(o["overall"]["slip_any"]), fmt(o["overall"]["slip_unit_type"]),
            fmt(o["overall"]["slip_same_num"]), fmt(o["overall"]["slip_value"]), fmt(o["overall"]["slip_any_excl_artifact_suspect"]), fmt(mr), fmt(o["grounded"]["slip_any"]),
            fmt(o["closed"]["slip_any"]), fmt(o["gpt4o_mini"]["slip_any"]), fmt(o["gemma3_27b"]["slip_any"])))
    ps = [(n, d) for n, d in res["checkers"].items() if d.get("poststratified_overall")]
    if ps:
        L += [""] + ["%s: coverage %d/%d (missing rows by cell: %s); post-stratified overall slips per 1000: any %s, unit-type %s." % (
            n, d["coverage"]["scored"], d["coverage"]["of"], d["coverage"]["missing_by_cell"], fmt(d["poststratified_overall"]["any"]),
            fmt(d["poststratified_overall"]["unit_type"])) for n, d in ps]
    L += ["", "Per-stratum slips by error type (grounded / closed-book, per 1000 answers in that stratum) are in the JSON "
          "(`checkers.<name>.strata`), with miss rates (share of errors PASSed) and question-clustered CIs.", "",
          "## Checker + unit normalization (UNF) deployment", "",
          "UNF (`src/unit_norm_fix.py`) changes the text of %d/%d RD pairs (by class: %s). Unchanged pairs keep their verdict, "
          "so their slips are a floor; changed pairs are re-scored on HPC (`jobs/journal2/jr2_UNFADV.sbatch`, "
          "pack `results/journal2/impact/rd_unf_pack.jsonl`)." % (res["unf"]["rows_changed"], res["n_dose_answers"],
                                                                 res["unf"]["changed_by_class"]), "",
          "| checker | before: any | after UNF: any | before: unit-type | after UNF: unit-type | status |", "|---|---|---|---|---|---|"]
    for name, d in res["checkers"].items():
        u = d.get("unf")
        if not u:
            continue
        o = d["strata"]["overall"]
        if u["status"] == "done":
            a = u["after"]["overall"]
            L.append("| %s | %s | %s | %s | %s | done |" % (name, fmt(o["slip_any"]), fmt(a["any"]), fmt(o["slip_unit_type"]), fmt(a["unit_type"])))
        else:
            L.append("| %s | %s | pending; bounds [%.1f, %.1f] | %s | pending; bounds [%.1f, %.1f] | %s |" % (
                name, fmt(o["slip_any"]), u["floor_unchanged_rows"]["any"]["per"], u["ceiling"]["any"]["per"], fmt(o["slip_unit_type"]),
                u["floor_unchanged_rows"]["unit_type"]["per"], u["ceiling"]["unit_type"]["per"], u["status"]))
    L += ["", "Bounds: floor = slips among pairs UNF leaves unchanged (verdict cannot change); ceiling = every UNF-changed error PASSes."]
    dn = [(n, d["unf"]) for n, d in res["checkers"].items() if d.get("unf", {}).get("status") == "done"]
    if dn:
        L.append("After UNF, correct answers PASSed (false-alarm side): " + "; ".join(
            "%s %s%%" % (n, fmt(u["after"]["overall"]["correct_pass_pct"])) for n, u in dn) + ". Same-env agreement of the HPC "
            "re-scored original text with the stored RD verdicts: " + "; ".join(
            "%s %d/%d" % (n, *u["env_agreement_rescored_orig_vs_stored"]) for n, u in dn) + ".")
    L.append("")
    # paper-ready sentences
    o, g, c = P["overall"], P["grounded"], P["closed"]
    sm = [(n, d) for n, d in res["checkers"].items() if "strata" in d and d["coverage"]["scored"] == d["coverage"]["of"]]
    rng = lambda key: (min(d["strata"]["overall"][key]["per"] for _, d in sm), max(d["strata"]["overall"][key]["per"] for _, d in sm))  # noqa: E731
    L += ["## Paper-ready sentences (automatic labels; update after human verification)", ""]
    if sm:
        a_lo, a_hi = rng("slip_any")
        u_lo, u_hi = rng("slip_unit_type")
        L.append("- Of every 1000 dose answers produced by gpt-4o-mini and gemma-3-27b, %.0f (95%% CI %.0f-%.0f) contained an "
                 "automatically flagged dose error: %.0f (%.0f-%.0f) when answering closed-book versus %.0f (%.0f-%.0f) when grounded "
                 "in the FDA label excerpt." % (o["any"]["per"], o["any"]["ci"][0], o["any"]["ci"][1], c["any"]["per"], c["any"]["ci"][0],
                                                c["any"]["ci"][1], g["any"]["per"], g["any"]["ci"][0], g["any"]["ci"][1]))
        mu = [d["strata"]["overall"]["miss_rate_unit_type"]["per"] for _, d in sm]
        mv = [d["strata"]["overall"]["miss_rate_value"]["per"] for _, d in sm]
        L.append("- At the paper's operating points, the %d fully scored checkers let %.1f-%.1f of these erroneous answers per 1000 "
                 "through, %.1f-%.1f of them unit-type errors (wrong unit or dosing basis): unit-type errors are %.0f%% of flagged "
                 "errors, but each checker passed %.0f-%.0f%% of them versus %.0f-%.0f%% of value errors." % (
                     len(sm), a_lo, a_hi, u_lo, u_hi, 100 * o["unit_type"]["k"] / max(1, o["any"]["k"]), min(mu), max(mu), min(mv), max(mv)))
        L.append("- %d of the %d unit-type flags are suspected label-parsing artifacts (e.g. `mg/m 2` from a lost superscript); "
                 "excluding them, unit-type errors fall to %.1f per 1000 answers and total slips to %.1f-%.1f per 1000, so the "
                 "unit-type figures (especially grounded) are upper bounds until `qc/real_dose_errors_check.csv` is adjudicated." % (
                     len(res["artifact_suspect_ids"]), o["unit_type"]["k"], o["unit_type_excl_artifact_suspect"]["per"],
                     *rng("slip_any_excl_artifact_suspect")))
    L += ["", "## Caveats", "",
          "- Automatic labels compare the answer's first dose with one label sentence; `match_other_context`, `time_ambiguous` and "
          "`unverifiable` answers count as non-errors in the main denominator (error rate is a lower bound for those, an upper bound "
          "for artifact-prone unit flags). Closed-book 'errors' may be legitimate doses from another label/regimen.",
          "- Missing judges are skipped and picked up automatically on rerun (MedScore RD scores: HPC job 62101). Judges with "
          "incomplete coverage (RAGAS Llama-3.3-70B: see coverage column and missing-by-cell line) use their scored rows only; "
          "the post-stratified overall reweights generator x mode cells to full size.",
          "- Per-1000 figures are specific to this question set (FDA-label [DOSE] cloze questions over 197 drugs), not a general "
          "clinical error rate.", ""]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------
# --precheck: sensitivity analysis on an AI-assisted pre-check of the unit-type flags (NOT human verification)
PRECHECK_MD = ROOT / "notes/real_dose_ai_precheck.md"
PRECHECK_JSON = OUT / "impact_precheck.json"
AI_LABELS = ["true_unit_error", "parser_artifact_answer_correct", "different_indication_or_population",
             "value_error_misclassified", "ambiguous"]
PC_STRATA = ["overall", "grounded", "closed", "gpt4o_mini", "gemma3_27b"]


def read_precheck(path: Path) -> dict:
    with Path(path).open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(l for l in fh if not l.startswith("#")))
    return {r["instance_id"]: r for r in rows}


def run_precheck(args) -> None:
    pc_path = Path(args.precheck)
    pc = read_precheck(pc_path)
    out_md = Path(args.out_md) if args.out_md != str(NOTE) else PRECHECK_MD
    out_json = Path(args.out_json) if args.out_json != str(OUT / "impact.json") else PRECHECK_JSON
    inst = read_jsonl(RD / "instances.jsonl")
    N = len(inst)
    cls = np.array([r["auto_class"] for r in inst])
    ai = np.array([pc.get(r["instance_id"], {}).get("ai_label", "") for r in inst])
    unit_auto = np.isin(cls, ["unit_error", "basis_error"])
    not_checked = [r["instance_id"] for r, u in zip(inst, unit_auto) if u and r["instance_id"] not in pc]
    if not_checked:
        raise SystemExit("pre-check CSV lacks %d auto unit-type rows, e.g. %s" % (len(not_checked), not_checked[:3]))
    f = lambda m: np.asarray(m, dtype=float)  # noqa: E731
    true_u = unit_auto & (ai == "true_unit_error")
    masks = {
        "unit_type_auto": f(unit_auto), "same_num_auto": f(cls == "unit_error"),
        "unit_type_true": f(true_u), "same_num_true": f(true_u & (cls == "unit_error")),
        "unit_type_true_or_ambiguous": f(unit_auto & np.isin(ai, ["true_unit_error", "ambiguous"])),
        "value_auto": f(cls == "value_error"),
        "value_precheck": f((cls == "value_error") | (unit_auto & (ai == "value_error_misclassified"))),
        "any_auto": f(np.isin(cls, ["unit_error", "basis_error", "value_error"])),
        "any_precheck": f((cls == "value_error") | (unit_auto & np.isin(ai, ["true_unit_error", "value_error_misclassified"]))),
        "artifact": f(unit_auto & (ai == "parser_artifact_answer_correct")),
        "diff_pop": f(unit_auto & (ai == "different_indication_or_population")),
        "same_num_artifact": f((cls == "unit_error") & (ai == "parser_artifact_answer_correct")),
    }
    smask = {s: np.array([1.0 if STRATA[s](r) else 0.0 for r in inst]) for s in PC_STRATA}
    bt = Boot([r["drug"] for r in inst], args.boot)
    res = {"generated_by": "scripts/journal2/impact_estimate.py --precheck %s" % pc_path.relative_to(ROOT) if pc_path.is_absolute()
           and ROOT in pc_path.parents else "scripts/journal2/impact_estimate.py --precheck %s" % pc_path,
           "provenance": "AI-assisted pre-check by Grok Bot (LLM), not human verification; to be confirmed by a human annotator",
           "n_dose_answers": N, "bootstrap": {"resamples": args.boot, "cluster": "drug", "seed": SEED},
           "ai_label_counts": {}, "ai_label_by_auto_class": {}, "ai_label_by_mode": {}, "prevalence": {}, "checkers": {}}
    for lab in AI_LABELS:
        res["ai_label_counts"][lab] = int((unit_auto & (ai == lab)).sum())
        for c in ("unit_error", "basis_error"):
            res["ai_label_by_auto_class"].setdefault(c, {})[lab] = int(((cls == c) & (ai == lab)).sum())
        for m in ("grounded", "closed"):
            res["ai_label_by_mode"].setdefault(m, {})[lab] = int((unit_auto & (ai == lab) & (smask[m] > 0)).sum())
    conf = [pc[i].get("ai_confidence", "") for i in pc]
    res["ai_confidence_counts"] = dict(Counter(conf))
    for s, sm in smask.items():
        res["prevalence"][s] = {"n_answers": int(sm.sum()), **{k: ratio(bt, m * sm, sm) for k, m in masks.items()}}
    for fname, name, _ in CHECKERS:
        p = RD / "scores" / fname
        if not p.is_file():
            res["checkers"][name] = {"status": "missing"}
            continue
        vd = verdicts(p)
        vv = [vd.get(r["instance_id"]) for r in inst]
        scored = f([v in ("PASS", "FAIL") for v in vv])
        passed = f([v == "PASS" for v in vv])
        d = {"scored": int(scored.sum()), "strata": {}}
        for s, sm in smask.items():
            ds = d["strata"].setdefault(s, {})
            for k, m in masks.items():
                ds["pass_pct_" + k] = ratio(bt, m * passed * sm, m * scored * sm, scale=100.0)
                ds["slip_" + k] = ratio(bt, m * passed * sm, scored * sm)
        res["checkers"][name] = d
    res["review_first"] = [{"check_id": r.get("check_id"), "instance_id": i, "ai_label": r["ai_label"],
                            "ai_confidence": r["ai_confidence"], "ai_rationale": r["ai_rationale"]}
                           for i, r in pc.items() if r["ai_confidence"] == "low" or r["ai_label"] == "ambiguous"
                           or (r["ai_label"] == "true_unit_error" and r["ai_confidence"] != "high")]
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(res, indent=1, default=str) + "\n")
    write_precheck_md(res, pc, out_md, out_json)
    print(json.dumps({"wrote": [str(out_json), str(out_md)], "ai_label_counts": res["ai_label_counts"]}))


SHORTNAME = {"MiniCheck-RoBERTa": "MC-RoBERTa", "MiniCheck-DeBERTa": "MC-DeBERTa", "AlignScore-base": "AS-base",
             "MiniCheck-Flan-T5-Large": "MC-Flan-T5", "AlignScore-large": "AS-large",
             "Llama-3.3-70B (RAGAS NLI)": "Llama-70B RAGAS", "Mistral-Small-24B (MedScore)": "MedScore (Mistral-24B)"}
LLM_JUDGES = ["Llama-3.3-70B (RAGAS NLI)", "Mistral-Small-24B (MedScore)"]


def _kn(s: dict) -> str:
    if not s["n"]:
        return "NA (n=0)"
    lo, hi = s["ci"]
    ci = " [%.0f, %.0f]" % (lo, hi) if lo is not None else ""
    return "%d/%d = %.0f%%%s" % (s["k"], s["n"], s["per"], ci)


def write_precheck_md(res: dict, pc: dict, path: Path, jpath: Path) -> None:
    C = res["checkers"]
    names = [n for n in C if "strata" in C[n]]
    L = ["# Real-dose unit-type errors: AI-assisted pre-check (sensitivity analysis)", "",
         "> **AI-assisted pre-check by Grok Bot (LLM), not human verification; to be confirmed by a human annotator.** "
         "The labels in `qc/ai_precheck_real_dose_unit_errors.csv` were assigned by an LLM agent reading each row's "
         "cloze question, FDA-label excerpt/target sentence, the generator's answer and the auto-extracted quantities "
         "(no API calls; adjudication table in `scripts/journal2/rd_ai_precheck_build.py`). `qc/real_dose_errors_check.csv` "
         "(the human sheet) is untouched. Treat everything below as a provisional sensitivity analysis.", "",
         "Generated by `python3 scripts/journal2/impact_estimate.py --precheck qc/ai_precheck_real_dose_unit_errors.csv` "
         "(JSON: `%s`). Default `impact_estimate.py` output is unchanged. PASS = stored verdict at the paper's operating "
         "point (as `rd_report.py`); 95%% CIs = drug-clustered bootstrap (%d resamples; very wide/degenerate for small n)." % (
             jpath.relative_to(ROOT) if ROOT in jpath.parents else jpath, res["bootstrap"]["resamples"]), "",
         "## 1. Pre-check labels for the %d auto-labelled unit-type errors" % sum(res["ai_label_counts"].values()), "",
         "| ai_label | all unit-type | same numeral, other unit (auto `unit_error`) | other basis (auto `basis_error`) | grounded | closed-book |",
         "|---|---|---|---|---|---|"]
    for lab in AI_LABELS:
        L.append("| `%s` | %d | %d | %d | %d | %d |" % (lab, res["ai_label_counts"][lab], res["ai_label_by_auto_class"]["unit_error"][lab],
                                                    res["ai_label_by_auto_class"]["basis_error"][lab], res["ai_label_by_mode"]["grounded"][lab],
                                                    res["ai_label_by_mode"]["closed"][lab]))
    L.append("| **total** | %d | %d | %d | %d | %d |" % (sum(res["ai_label_counts"].values()), sum(res["ai_label_by_auto_class"]["unit_error"].values()),
                                                         sum(res["ai_label_by_auto_class"]["basis_error"].values()),
                                                         sum(res["ai_label_by_mode"]["grounded"].values()), sum(res["ai_label_by_mode"]["closed"].values())))
    L += ["", "Confidence: %s. Mechanisms (ai_mechanism column): %s." % (
        ", ".join("%s %d" % (k, v) for k, v in sorted(res["ai_confidence_counts"].items())),
        ", ".join("%s %d" % (k, v) for k, v in Counter((r["ai_label"][:4] + ":" + r["ai_mechanism"]) for r in pc.values()).most_common())), ""]
    L += ["## 2. Checker PASS rate on unit-type errors: auto labels vs pre-check-confirmed (`true_unit_error`) only", "",
          "PASS % among the errors (= miss rate; lower is better). `auto` = all auto-labelled rows (as in `notes/real_dose_errors.md`); "
          "`true` = only rows the pre-check labels `true_unit_error`; `artifact` = rows labelled `parser_artifact_answer_correct` "
          "(answers that are actually correct, so PASS is the right verdict); `diff-pop` = `different_indication_or_population` (legit dose for another population; not counted as errors).", "",
          "| checker | unit-type auto | unit-type **true** | same-numeral auto | same-numeral **true** | same-numeral artifact (correct answers) | unit-type true or ambiguous | unit-type diff-pop |",
          "|---|---|---|---|---|---|---|---|"]
    for n in names:
        o = C[n]["strata"]["overall"]
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (SHORTNAME[n], _kn(o["pass_pct_unit_type_auto"]), _kn(o["pass_pct_unit_type_true"]),
                                                       _kn(o["pass_pct_same_num_auto"]), _kn(o["pass_pct_same_num_true"]),
                                                       _kn(o["pass_pct_same_num_artifact"]), _kn(o["pass_pct_unit_type_true_or_ambiguous"]),
                                                       _kn(o["pass_pct_diff_pop"])))
    L += ["", "### By answer mode (pre-check-confirmed true unit errors only)", "",
          "| checker | unit-type true: grounded | unit-type true: closed-book | same-numeral true: grounded | same-numeral true: closed-book |",
          "|---|---|---|---|---|"]
    for n in names:
        g, c = C[n]["strata"]["grounded"], C[n]["strata"]["closed"]
        L.append("| %s | %s | %s | %s | %s |" % (SHORTNAME[n], _kn(g["pass_pct_unit_type_true"]), _kn(c["pass_pct_unit_type_true"]),
                                               _kn(g["pass_pct_same_num_true"]), _kn(c["pass_pct_same_num_true"])))
    L += ["", "### Value errors after re-assigning `value_error_misclassified` (value errors themselves NOT pre-checked)", "",
          "| checker | value auto | value + misclassified |", "|---|---|---|"]
    for n in names:
        o = C[n]["strata"]["overall"]
        L.append("| %s | %s | %s |" % (SHORTNAME[n], _kn(o["pass_pct_value_auto"]), _kn(o["pass_pct_value_precheck"])))
    P = res["prevalence"]
    L += ["", "## 3. Impact per 1000 dose answers (pre-check sensitivity)", "",
          "Prevalence per 1000 dose answers (n=%d): unit-type auto %s -> true %s; same-numeral auto %s -> true %s; any error auto %s -> "
          "pre-check %s (value errors kept as auto-labelled)." % (
              P["overall"]["n_answers"], fmt(P["overall"]["unit_type_auto"]), fmt(P["overall"]["unit_type_true"]), fmt(P["overall"]["same_num_auto"]),
              fmt(P["overall"]["same_num_true"]), fmt(P["overall"]["any_auto"]), fmt(P["overall"]["any_precheck"])), "",
          "Slips = erroneous answers PASSed, per 1000 dose answers scored by that checker.", "",
          "| checker | unit-type slips auto | unit-type slips true | same-numeral slips auto | same-numeral slips true | any-error slips auto | any-error slips pre-check | closed-book: unit-type true | grounded: unit-type true |",
          "|---|---|---|---|---|---|---|---|---|"]
    for n in names:
        o, g, c = (C[n]["strata"][s] for s in ("overall", "grounded", "closed"))
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            SHORTNAME[n], fmt(o["slip_unit_type_auto"]), fmt(o["slip_unit_type_true"]), fmt(o["slip_same_num_auto"]), fmt(o["slip_same_num_true"]),
            fmt(o["slip_any_auto"]), fmt(o["slip_any_precheck"]), fmt(c["slip_unit_type_true"]), fmt(g["slip_unit_type_true"])))
    # verdict (data-driven numbers)
    o = {n: C[n]["strata"]["overall"] for n in names}
    small = [n for n in names if n not in LLM_JUDGES]
    js = [n for n in LLM_JUDGES if n in o]
    def rng_(key, ns):
        v = [o[n][key]["per"] for n in ns if o[n][key]["n"]]
        return (min(v), max(v)) if v else (float("nan"), float("nan"))
    sn_true_n = o[names[0]]["pass_pct_same_num_true"]["n"]
    ut_true_n = o[names[0]]["pass_pct_unit_type_true"]["n"]
    L += ["", "## 4. Verdict", ""]
    L.append("- **The 'LLM judges pass same-numeral unit errors 53-60%%' figure is mostly a parser artifact.** Of the %d auto "
             "same-numeral (`unit_error`) flags, the pre-check finds %d where the answer is actually correct (lost `m 2` superscript, "
             "`(mcg/kg)` table header, 'mcg of ivermectin per kg') and only %d genuine unit errors. On the artifacts every checker "
             "PASSes most rows (correctly), which inflated the auto 'miss rate' of the judges to %.0f-%.0f%%." % (
                 res["ai_label_by_auto_class"]["unit_error"] and sum(res["ai_label_by_auto_class"]["unit_error"].values()),
                 res["ai_label_by_auto_class"]["unit_error"]["parser_artifact_answer_correct"], sn_true_n, *rng_("pass_pct_same_num_auto", js)))
    L.append("- On the %d pre-check-confirmed same-numeral errors, the LLM judges PASS %s (%s) and %s (%s); the small checkers PASS "
             "%.0f-%.0f%% (%s). On all %d confirmed unit-type errors: judges %s, small checkers %s." % (
                 sn_true_n, _kn(o[js[0]]["pass_pct_same_num_true"]), SHORTNAME[js[0]], _kn(o[js[1]]["pass_pct_same_num_true"]), SHORTNAME[js[1]],
                 *rng_("pass_pct_same_num_true", small), ", ".join("%s %d/%d" % (SHORTNAME[n], o[n]["pass_pct_same_num_true"]["k"],
                                                                                  o[n]["pass_pct_same_num_true"]["n"]) for n in small),
                 ut_true_n, ", ".join("%s %d/%d" % (SHORTNAME[n], o[n]["pass_pct_unit_type_true"]["k"], o[n]["pass_pct_unit_type_true"]["n"]) for n in js),
                 ", ".join("%s %d/%d" % (SHORTNAME[n], o[n]["pass_pct_unit_type_true"]["k"], o[n]["pass_pct_unit_type_true"]["n"]) for n in small)))
    L.append("- So, under this pre-check, the LLM judges do **not** pass genuine same-numeral unit errors at high rates; they "
             "catch them about as well as the best small checkers (MiniCheck-DeBERTa, MiniCheck-Flan-T5), while "
             "RoBERTa / AlignScore-base / AlignScore-large still PASS about half. With n=%d (same numeral) and n=%d (unit-type), "
             "and only one confirmed grounded error (losartan, which MedScore PASSes and RAGAS FAILs), differences between "
             "checkers are not statistically resolvable (see CIs); the claim in the paper should be reworded to 'auto-labelled' "
             "or dropped until human verification." % (sn_true_n, ut_true_n))
    L.append("- The remaining auto unit-type flags are mostly **closed-book answers giving a legitimate dose for another "
             "population/indication** (%d; typically the adult dose when the hidden cloze slot is pediatric mg/kg), "
             "%d value errors whose unit parse was wrong, and %d ambiguous rows. Checkers mostly FAIL the diff-pop rows "
             "(the evidence names a different population/regimen; see the diff-pop column)." % (
                 res["ai_label_counts"]["different_indication_or_population"], res["ai_label_counts"]["value_error_misclassified"],
                 res["ai_label_counts"]["ambiguous"]))
    L += ["", "## 5. Rows the human annotator should check first", "",
          "Low-confidence labels, `ambiguous` labels, and medium-confidence `true_unit_error` labels (these drive the re-computed table).", "",
          "| check_id | instance_id | ai_label | conf | rationale |", "|---|---|---|---|---|"]
    for r in res["review_first"]:
        L.append("| %s | %s | %s | %s | %s |" % (r["check_id"], r["instance_id"], r["ai_label"], r["ai_confidence"], r["ai_rationale"].replace("|", "/")))
    L += ["", "## Caveats", "",
          "- The pre-checker is an LLM; its pharmacology can be wrong (e.g. where it relied on prescribing-information knowledge "
          "beyond the shown excerpt, such as adult acetaminophen or JRA meloxicam doses). Human labels in "
          "`qc/real_dose_errors_check.csv` supersede it.",
          "- Only the 47 auto unit-type rows were pre-checked; the 93 auto value errors were not (their PASS rates above are auto-labelled).",
          "- `different_indication_or_population` answers are not counted as errors here; a stricter reading (the answer does not "
          "fit the question's population) would count them, which mostly adds closed-book rows that all checkers FAIL.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
