#!/usr/bin/env python3
"""(J3-FINAL) Journal chain 3 report (CPU, numpy; no models).  Writes notes/journal3_report.md + results/journal3/report.json.

(1) FT-on-RD   chain-1 fine-tuned checkers (+ same-path bases) on the 1451 real-dose answers: PASS on auto-correct; FAIL on
               any auto error / unit-type (unit+basis) / same-numeral (unit) / value; FAIL on the AI-precheck confirmed
               subset (qc/ai_precheck_real_dose_unit_errors.csv, ai_label == true_unit_error; read-only); slip-past per
               1000 answers (impact_estimate.py definition: #(error answers PASS) / #(answers scored) x 1000), drug-
               clustered bootstrap.  Paper checkers / judges from results/journal2/real_dose/scores as references.
(2) FT x UNF   held-out UNF set (unf_heldout_report.py metrics: QI = S PASS, US = U FAIL, anchor-conditional per pack;
               US_clean = U without residual correct copy; inversion = share of pairs with score(S) <= score(U); AUC
               S > U) and RD pairs (rows the normalizer changes re-scored; unchanged rows keep the model's raw RD verdict),
               raw vs UNF v1 vs frozen UNF v2; 2x2 {base, FT} x {raw, UNF}.  Paper-env base + UNF references are read
               from results/journal2/unf_heldout/report.json.
(3) Judges     small local LLM judges (RAGAS-NLI prompt): paper card cells (C0-conditional), inversion floor / AUC on
               p_yes, journal RAG cells, RD groups + slips; reference rows = existing Llama results (T19 local HF, API
               8B/70B, MedScore).
Everything missing is reported as 'not scored yet' (the report runs on any partial state).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from j3_common import (FT_SCORES, J3, JUDGE_SCORES, MARKERS, NOTES, PACK_FILES, RAG_CELLS, ROOT, card_metrics,  # noqa: E402
                       fmt_rate, inversion_floor, qboot, rag_cell, read_jsonl, residual, v2_freeze_ok, verdict_map)
from j3_models import FT, JUDGES, ft_name  # noqa: E402

PRECHECK = ROOT / "qc/ai_precheck_real_dose_unit_errors.csv"
RD_SCORES = ROOT / "results/journal2/real_dose/scores"
RAG_SCORES = ROOT / "results/journal/rag/scores"
UNFHO_REPORT = ROOT / "results/journal2/unf_heldout/report.json"
RAW = ROOT / "results/raw"
SEED = 20261001
RD_GROUPS = [("correct PASS", lambda r, pre: r["auto_class"] == "correct", "PASS"),
             ("any err FAIL", lambda r, pre: r["auto_class"] in ("unit_error", "basis_error", "value_error"), "FAIL"),
             ("unit-type FAIL", lambda r, pre: r["auto_class"] in ("unit_error", "basis_error"), "FAIL"),
             ("same-numeral FAIL", lambda r, pre: r["auto_class"] == "unit_error", "FAIL"),
             ("value FAIL", lambda r, pre: r["auto_class"] == "value_error", "FAIL"),
             ("precheck-true FAIL", lambda r, pre: pre.get(r["instance_id"]) == "true_unit_error", "FAIL")]
SLIPS = [("any", lambda r, pre: r["auto_class"] in ("unit_error", "basis_error", "value_error")),
         ("unit-type", lambda r, pre: r["auto_class"] in ("unit_error", "basis_error")),
         ("value", lambda r, pre: r["auto_class"] == "value_error"),
         ("precheck-true", lambda r, pre: pre.get(r["instance_id"]) == "true_unit_error")]
# reference (existing) judge results; card = main + T7 + T17 score files merged
REF_CARD = [("Llama-3.2-1B local HF (T19)", [RAW / "t19/llama32_1b_instruct.jsonl"]),
            ("Llama-3.2-3B local HF (T19)", [RAW / "t19/llama32_3b_instruct.jsonl"]),
            ("Llama-3.1-8B local HF (T19)", [RAW / "t19/llama31_8b_instruct.jsonl"]),
            ("Llama-3.1-8B API (v6)", [RAW / "t6b/full/v6_ragas_llama31_8b.jsonl", RAW / "t7/v6_ragas_llama31_8b.jsonl", RAW / "t17/v6_ragas_llama31_8b.jsonl"]),
            ("Llama-3.3-70B API (v4, paper)", [RAW / "v4_ragas_nli.llama.jsonl", RAW / "t7/v4_ragas_nli.llama.jsonl", RAW / "t17/v4_ragas_nli.llama.jsonl"]),
            ("Mistral-Small-24B MedScore (paper)", [RAW / "v1_medscore.jsonl", RAW / "t7/v1_medscore.jsonl", RAW / "t17/v1_medscore.jsonl"])]
REF_RAG = [("Llama-3.3-70B API (v4)", RAG_SCORES / "v4_ragas_nli.jsonl"), ("Mistral-Small-24B MedScore", RAG_SCORES / "v1_medscore.jsonl"),
           ("MiniCheck-Flan-T5-Large (paper env)", RAG_SCORES / "v2a_minicheck.jsonl"), ("AlignScore-large (paper env)", RAG_SCORES / "v3_alignscore.jsonl")]
REF_RD = [("MiniCheck-RoBERTa (paper)", "t6_minicheck_roberta.jsonl"), ("MiniCheck-DeBERTa (paper)", "t6_minicheck_deberta.jsonl"),
          ("AlignScore-base (paper)", "t6_alignscore_base.jsonl"), ("MiniCheck-Flan-T5-Large (paper)", "v2a_minicheck.jsonl"),
          ("AlignScore-large (paper)", "v3_alignscore.jsonl"), ("Llama-3.3-70B RAGAS (paper)", "v4_ragas_nli.jsonl"),
          ("Mistral-Small-24B MedScore (paper)", "v1_medscore.jsonl")]
PAPER_BASE = {"minicheck_ft5": "MiniCheck-Flan-T5-Large", "alignscore_large": "AlignScore-large"}


# ---------------------------------------------------------------- helpers
def merged_verdicts(paths) -> dict:
    out = {}
    for p in paths:
        out.update(verdict_map(p))
    return out


def merged_scores(paths) -> dict:
    out = {}
    for p in paths:
        for r in read_jsonl(p):
            s = r.get("p_yes") if r.get("p_yes") is not None else r.get("score")
            if s is not None:
                out[r["instance_id"]] = float(s)
    return out


class CB:
    """Drug-clustered bootstrap of k/n ratios (impact_estimate.Boot semantics, multinomial cluster weights)."""

    def __init__(self, clusters, n_boot):
        self.ids = sorted(set(clusters))
        idx = {c: i for i, c in enumerate(self.ids)}
        self.rc = np.array([idx[c] for c in clusters])
        m = len(self.ids)
        self.W = np.random.default_rng(SEED).multinomial(m, np.full(m, 1.0 / m), size=n_boot).astype(float)

    def ratio(self, num, den, scale):
        pn = np.bincount(self.rc, weights=np.asarray(num, float), minlength=len(self.ids))
        pd = np.bincount(self.rc, weights=np.asarray(den, float), minlength=len(self.ids))
        k, n = pn.sum(), pd.sum()
        kb, nb = self.W @ pn, self.W @ pd
        rb = (kb[nb > 0] / nb[nb > 0]) * scale
        return {"k": int(round(k)), "n": int(round(n)), "rate": (scale * k / n) if n else None,
                "ci": [float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))] if n and len(rb) else [None, None]}


def fr(s, nd=1, n=True):
    if not s or s.get("rate") is None:
        return "NA"
    lo, hi = s["ci"]
    core = ("%.*f [%.*f, %.*f]" % (nd, s["rate"], nd, lo, nd, hi)) if lo is not None else "%.*f" % (nd, s["rate"])
    return core + (" (n=%d)" % s["n"] if n else "")


def pairs_rate(pairs, n_boot):
    """pairs: [(cluster, 0/1)] -> rate in % with drug-cluster CI."""
    if not pairs:
        return {"k": 0, "n": 0, "rate": None, "ci": [None, None]}
    cb = CB([c for c, _ in pairs], n_boot)
    return cb.ratio([x for _, x in pairs], [1] * len(pairs), 100.0)


def auc(pos, neg):
    if not pos or not neg:
        return None
    p, n = np.array(pos, float), np.array(neg, float)
    return float(((p[:, None] > n[None, :]).sum() + 0.5 * (p[:, None] == n[None, :]).sum()) / (len(p) * len(n)))


def load_precheck() -> dict:
    if not PRECHECK.is_file():
        return {}
    with PRECHECK.open(encoding="utf-8") as fh:
        return {r["instance_id"]: r["ai_label"] for r in csv.DictReader(l for l in fh if not l.startswith("#"))}


# ---------------------------------------------------------------- (1) RD block
def rd_block(inst, vd, pre, cb):
    vv = [vd.get(r["instance_id"]) for r in inst]
    scored = np.array([v in ("PASS", "FAIL") for v in vv], float)
    passed = np.array([v == "PASS" for v in vv], float)
    out = {"scored": int(scored.sum()), "of": len(inst), "parse_fail": sum(1 for v in vv if v == "PARSE_FAIL"), "groups": {}, "slips": {}}
    for g, fn, want in RD_GROUPS:
        m = np.array([fn(r, pre) for r in inst], float)
        hit = passed if want == "PASS" else (scored - passed)
        out["groups"][g] = cb.ratio(m * hit, m * scored, 100.0)
    for g, fn in SLIPS:
        m = np.array([fn(r, pre) for r in inst], float)
        out["slips"][g] = cb.ratio(m * passed, scored, 1000.0)
    return out


def rd_rows_md(name, b):
    if b is None:
        return "| %s | not scored yet |" % name
    return "| %s | %d/%d | %s | %s | %s | %s |" % (
        name, b["scored"], b["of"], " | ".join(fr(b["groups"][g], n=False) for g, _, _ in RD_GROUPS),
        fr(b["slips"]["any"], n=False), fr(b["slips"]["unit-type"], n=False), fr(b["slips"]["precheck-true"], n=False))


RD_HDR = ["| checker | scored | " + " | ".join(g for g, _, _ in RD_GROUPS) + " | slips/1000 any | slips/1000 unit-type | slips/1000 precheck-true |",
          "|" + "---|" * (2 + len(RD_GROUPS) + 3)]


# ---------------------------------------------------------------- (2) held-out + RD pairs
def ho_metrics(rows, sc, n_boot):
    """sc: id -> (verdict, score)."""
    A = {r["cid"]: r for r in rows if r["family"] == "anchor"}
    S = {r["cid"]: r for r in rows if r["family"] == "S"}
    U = {r["cid"]: r for r in rows if r["family"] == "U"}
    okb = {c for c, a in A.items() if sc.get(a["instance_id"], (None,))[0] == "PASS"}
    m = {"anchor_pass": "%d/%d" % (len(okb), len(A)), "coverage": sum(1 for r in rows if r["instance_id"] in sc)}
    val = lambda r, want: int(sc[r["instance_id"]][0] == want)  # noqa: E731
    s_sel = [r for r in S.values() if r["instance_id"] in sc and sc[r["instance_id"]][0] in ("PASS", "FAIL")]
    u_sel = [r for r in U.values() if r["instance_id"] in sc and sc[r["instance_id"]][0] in ("PASS", "FAIL")]
    m["QI"] = pairs_rate([(r["drug"], val(r, "PASS")) for r in s_sel if r["cid"] in okb], n_boot)
    m["US"] = pairs_rate([(r["drug"], val(r, "FAIL")) for r in u_sel if r["cid"] in okb], n_boot)
    m["US_clean"] = pairs_rate([(r["drug"], val(r, "FAIL")) for r in u_sel if r["cid"] in okb and not residual(r)], n_boot)
    m["QI_uncond"] = pairs_rate([(r["drug"], val(r, "PASS")) for r in s_sel], n_boot)
    m["US_clean_uncond"] = pairs_rate([(r["drug"], val(r, "FAIL")) for r in u_sel if not residual(r)], n_boot)
    both = [c for c in S if c in U and S[c]["instance_id"] in sc and U[c]["instance_id"] in sc
            and sc[S[c]["instance_id"]][1] is not None and sc[U[c]["instance_id"]][1] is not None]
    m["inversion"] = pairs_rate([(S[c]["drug"], int(sc[S[c]["instance_id"]][1] <= sc[U[c]["instance_id"]][1])) for c in both], n_boot)
    m["auc_S_gt_U"] = auc([sc[S[c]["instance_id"]][1] for c in both], [sc[U[c]["instance_id"]][1] for c in both])
    return m


def sc_map(path):
    out = {}
    for r in read_jsonl(path):
        v = r.get("verdict")
        if v not in ("PASS", "FAIL", "PARSE_FAIL") and r.get("score") is not None:
            v = "PASS" if float(r["score"]) > 0.5 else "FAIL"
        out[r["instance_id"]] = (v, float(r["score"]) if r.get("score") is not None else None)
    return out


def rdpair_metrics(inst, pack, raw_v, unf_v, pre, n_boot):
    """unchanged rows keep raw RD verdict; rows in the UNF pack use the variant re-score."""
    col = {}
    for r in inst:
        i = r["instance_id"]
        v = unf_v.get(i) if i in pack else raw_v.get(i)
        if v in ("PASS", "FAIL"):
            col[i] = v
    out = {"coverage": len(col)}
    for g, fn, want in RD_GROUPS:
        if g == "any err FAIL":
            continue
        out[g] = pairs_rate([(r["drug"], int(col[r["instance_id"]] == want)) for r in inst if fn(r, pre) and r["instance_id"] in col], n_boot)
    return out


# ---------------------------------------------------------------- (3) judges
def judge_card(card, vd, scores):
    m = card_metrics(card, vd)
    m["inversion"] = inversion_floor(card, scores) if scores else None
    return m


def card_row_md(name, m):
    if m is None:
        return "| %s | not scored yet |" % name
    c = lambda k: fmt_rate(m[k]).split(" (n=")[0]  # noqa: E731
    inv = m.get("inversion") or {}
    ic = inv.get("claim") or {}
    return "| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        name, m["n_scored"], c("c0_pass_rate"), c("qi_all"), c("ns"), c("us_claim_up"), c("us_evid_up"), c("us_claim_down"), c("us_evid_down"),
        "%.1f" % (100 * ic["floor"]) if ic.get("floor") is not None else "NA",
        "%.3f" % ic["auc_conv_vs_swap"] if ic.get("auc_conv_vs_swap") is not None else "NA", m["n_parse_fail"])


CARD_HDR = ["| judge | n | C0 PASS | QI (conv PASS\\|C0) | NS (evid ×2/×10 FAIL\\|C0) | US claim↑ | US evid↑ | US claim↓ | US evid↓ | "
            "inversion floor % (conv ≤ ×1000 claim swap; p_yes, else 0/1) | AUC conv>swap | parse fails |", "|" + "---|" * 12]


def rag_block(inst, vd):
    return {lab: qboot(rag_cell(inst, vd, cond, want, conditional)) for lab, cond, want, conditional in RAG_CELLS}


def rag_row_md(name, b):
    if b is None:
        return "| %s | not scored yet |" % name
    return "| %s | %s |" % (name, " | ".join(fmt_rate(b[lab]) for lab, _, _, _ in RAG_CELLS))


def blind_gone(m, rag):
    """'unit-blindness disappears' criterion: C0 >= 80, QI >= 80, US claim up/down >= 80 on the card, and RAG unit-up /
    unit-down FAIL|C0 >= 80 (point estimates)."""
    if m is None:
        return None
    ks = [m[k]["rate"] for k in ("c0_pass_rate", "qi_all", "us_claim_up", "us_claim_down")]
    if rag:
        ks += [rag["unit-up FAIL|C0"]["rate"], rag["unit-down FAIL|C0"]["rate"]]
    return all(x is not None and x >= 0.8 for x in ks)


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ft-scores", default=str(FT_SCORES))
    ap.add_argument("--judge-scores", default=str(JUDGE_SCORES))
    ap.add_argument("--out-json", default=str(J3 / "report.json"))
    ap.add_argument("--out-md", default=str(NOTES / "journal3_report.md"))
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args()
    fts, jds, B = Path(args.ft_scores), Path(args.judge_scores), args.boot
    ok, cur, frz = v2_freeze_ok()
    inst = read_jsonl(PACK_FILES["rd"])
    pre = load_precheck()
    cb = CB([r["drug"] for r in inst], B)
    res = {"generated_by": "scripts/journal3/j3_report.py",
           "generated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M UTC+7"),
           "v2_sha256": cur, "v2_matches_freeze": ok, "n_rd": len(inst), "precheck_true": sum(1 for v in pre.values() if v == "true_unit_error"),
           "markers": sorted(p.stem for p in MARKERS.glob("*.done")) if MARKERS.is_dir() else [], "ft_rd": {}, "ref_rd": {}, "judge_rd": {},
           "ft_ho": {}, "ft_rdpairs": {}, "paper_unf": {}, "judge_card": {}, "ref_card": {}, "judge_rag": {}, "ref_rag": {}, "judges": {}}
    # (1)
    for model, tag in FT:
        n = ft_name(model, tag)
        vd = verdict_map(fts / ("%s__rd_raw.jsonl" % n))
        res["ft_rd"][n] = rd_block(inst, vd, pre, cb) if len(vd) >= len(inst) else ({"status": "partial %d/%d" % (len(vd), len(inst))} if vd else None)
    for name, f in REF_RD:
        vd = verdict_map(RD_SCORES / f)
        res["ref_rd"][name] = rd_block(inst, vd, pre, cb) if vd else None
    # (2)
    ho_rows = [r for r in read_jsonl(PACK_FILES["ho"]) if r.get("family") in ("S", "U", "anchor")]
    pack = {r["instance_id"]: r for r in read_jsonl(PACK_FILES["rdunf"])}
    for model, tag in FT:
        n = ft_name(model, tag)
        d, e = {}, {}
        raw_rd = verdict_map(fts / ("%s__rd_raw.jsonl" % n))
        for var in ("raw", "unf", "unf_v2"):
            sc = sc_map(fts / ("%s__ho_%s.jsonl" % (n, var)))
            d[var] = ho_metrics(ho_rows, sc, B) if len(sc) >= len(ho_rows) else None
            uv = verdict_map(fts / ("%s__rdunf_%s.jsonl" % (n, var)))
            e[var] = rdpair_metrics(inst, pack, raw_rd, uv, pre, B) if (len(raw_rd) >= len(inst) and len(uv) >= len(pack)) else None
        res["ft_ho"][n], res["ft_rdpairs"][n] = d, e
    if UNFHO_REPORT.is_file():
        rep = json.loads(UNFHO_REPORT.read_text())
        for key, nm in PAPER_BASE.items():
            res["paper_unf"][key] = {"ho": {p: rep["checkers"].get(nm, {}).get("packs", {}).get(p) for p in ("orig", "unf", "unf_v2")},
                                     "rd": {p: rep["rd"]["checkers"].get(nm, {}).get("packs", {}).get(p) for p in ("orig", "unf", "unf_v2")}}
    # (3)
    card = read_jsonl(PACK_FILES["card"])
    rag = read_jsonl(PACK_FILES["rag"])
    for slug, hf_id, pb, gb, fam, gated in JUDGES:
        mk = MARKERS / ("J3_JG_%s.done" % slug)
        info = json.loads(mk.read_text()) if mk.is_file() else {}
        f = {p: jds / ("%s__%s.jsonl" % (slug, p)) for p in ("card", "rag", "rd")}
        vd = {p: verdict_map(f[p]) for p in f}
        rows0 = read_jsonl(f["card"]) or read_jsonl(f["rag"]) or read_jsonl(f["rd"])
        res["judges"][slug] = {"hf_id": hf_id, "params_b": pb, "status": ("skipped: " + str(info["skipped"])) if info.get("skipped") else
                               ("done" if info else ("partial" if any(vd.values()) else "not run")),
                               "revision": (rows0[0].get("hf_revision") if rows0 else None) or info.get("revision"),
                               "backend": (rows0[0].get("backend") + " " + str(rows0[0].get("backend_version"))) if rows0 else None,
                               "rows": {p: len(v) for p, v in vd.items()},
                               "p_yes_missing": {p: sum(1 for r in read_jsonl(f[p]) if r.get("p_yes") is None) for p in f}}
        res["judge_card"][slug] = judge_card(card, vd["card"], merged_scores([f["card"]])) if len(vd["card"]) >= len(card) else None
        res["judge_rag"][slug] = rag_block(rag, vd["rag"]) if len(vd["rag"]) >= len(rag) else None
        res["judge_rd"][slug] = rd_block(inst, vd["rd"], pre, cb) if len(vd["rd"]) >= len(inst) else None
        res["judges"][slug]["unit_blindness_gone"] = blind_gone(res["judge_card"][slug], res["judge_rag"][slug])
    for name, paths in REF_CARD:
        vd = merged_verdicts(paths)
        res["ref_card"][name] = judge_card(card, vd, merged_scores(paths)) if vd else None
    for name, p in REF_RAG:
        vd = verdict_map(p)
        res["ref_rag"][name] = rag_block(rag, vd) if vd else None
    # agreement: new Llama-3.1-8B (vLLM) vs T19 local HF / API on the card
    new8 = verdict_map(jds / "llama31_8b__card.jsonl")
    if new8:
        res["llama8b_agreement"] = {}
        for name, paths in REF_CARD[2:4]:
            ref = merged_verdicts(paths)
            common = [i for i in new8 if i in ref and new8[i] in ("PASS", "FAIL") and ref[i] in ("PASS", "FAIL")]
            res["llama8b_agreement"][name] = {"n": len(common), "agree": sum(1 for i in common if new8[i] == ref[i])}
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n")
    write_md(res, Path(args.out_md))
    print(json.dumps({"wrote": [args.out_json, args.out_md], "ft_rd": {k: ("ok" if v and "groups" in v else v) for k, v in res["ft_rd"].items()},
                      "judges": {k: v["status"] for k, v in res["judges"].items()}}, default=str))


def write_md(res, path):
    L = ["# Journal chain 3 — FT on real doses, FT × UNF, small local LLM judges", "",
         "Generated %s by `scripts/journal3/j3_report.py` (chain 3, `jobs/run_journal_chain3.sh`). UNF v2 sha256 %s… (%s freeze). "
         "Bootstrap: drug clusters (RD, held-out), base clusters (card), question clusters (RAG); 95%% percentile CIs. "
         "RD labels are AUTOMATIC (rd_extract.py); precheck-true = AI pre-check `true_unit_error` (n=%d, AI-made, not human). "
         "Held-out UNF gold is AI-built." % (res["generated_at"], res["v2_sha256"][:12], "matches" if res["v2_matches_freeze"] else "DOES NOT MATCH",
                                               res["precheck_true"]), ""]
    L += ["## 1. Fine-tuned checkers on the 1451 real-dose answers", "",
          "Group cells = % of the group with the wanted verdict (PASS on correct, FAIL on errors). Slips/1000 = error answers "
          "that PASS per 1000 scored answers (impact_estimate.py definition). FT rows and `*_base` rows use the same inference path "
          "(vllm env); `(paper)` rows are the stored RD scores.", ""] + RD_HDR
    for n, b in res["ft_rd"].items():
        L.append(rd_rows_md(n, b) if (b is None or "groups" in b) else "| %s | %s |" % (n, b["status"]))
    for n, b in res["ref_rd"].items():
        L.append(rd_rows_md(n, b))
    for n, b in res["judge_rd"].items():
        if b:
            L.append(rd_rows_md("judge " + n, b))
    L += ["", "## 2. FT × UNF", "", "### 2x2 {base, FT r1} × {raw, UNF v1, UNF v2}", "",
          "Held-out: QI = S PASS, US clean = U (no residual copy) FAIL, both anchor-conditional; inversion = % pairs with score(S) ≤ "
          "score(U); AUC(S>U). RD pairs: rows the normalizer changes are re-scored, the rest keep the raw verdict.", "",
          "| checker | text | HO QI | HO US clean | HO inversion | HO AUC | RD correct PASS | RD unit-type FAIL | RD same-numeral FAIL | RD precheck-true FAIL | RD value FAIL |",
          "|" + "---|" * 11]
    vlab = {"raw": "raw", "unf": "UNF v1", "unf_v2": "UNF v2"}
    for model in ("minicheck_ft5", "alignscore_large"):
        pu = res["paper_unf"].get(model)
        if pu:
            for p, lab in (("orig", "raw"), ("unf", "UNF v1"), ("unf_v2", "UNF v2")):
                h, r = pu["ho"].get(p) or {}, pu["rd"].get(p) or {}
                L.append("| %s base (paper env, unf_heldout) | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    model, lab, fr(h.get("QI"), n=False), fr(h.get("US_clean"), n=False), fr(h.get("inversion"), n=False),
                    "%.3f" % h["auc_S_gt_U"] if h.get("auc_S_gt_U") is not None else "NA",
                    *[fr(r.get(k), n=False) for k in ("QI_correct", "US_unit_type_auto", "US_same_numeral_auto", "US_unit_type_precheck_true", "US_value_auto")]))
        for tag in ("base", "r1"):
            n = ft_name(model, tag)
            for var in ("raw", "unf", "unf_v2"):
                h, r = (res["ft_ho"].get(n) or {}).get(var), (res["ft_rdpairs"].get(n) or {}).get(var)
                if h is None and r is None:
                    L.append("| %s | %s | not scored yet |" % (n, vlab[var]))
                    continue
                h, r = h or {}, r or {}
                L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    n, vlab[var], fr(h.get("QI"), n=False), fr(h.get("US_clean"), n=False), fr(h.get("inversion"), n=False),
                    "%.3f" % h["auc_S_gt_U"] if h.get("auc_S_gt_U") is not None else "NA",
                    *[fr(r.get(k), n=False) for k in ("correct PASS", "unit-type FAIL", "same-numeral FAIL", "precheck-true FAIL", "value FAIL")]))
    L += ["", "### All FT runs, held-out (raw / UNF v1 / UNF v2)", "", "| checker | QI raw | QI v1 | QI v2 | US clean raw | US clean v1 | US clean v2 | inversion raw | inversion v2 | AUC raw | AUC v2 |",
          "|" + "---|" * 11]
    for n, d in res["ft_ho"].items():
        if not any(d.values()):
            L.append("| %s | not scored yet |" % n)
            continue
        g = lambda v, k: fr((d.get(v) or {}).get(k), n=False)  # noqa: E731
        a = lambda v: "%.3f" % d[v]["auc_S_gt_U"] if d.get(v) and d[v].get("auc_S_gt_U") is not None else "NA"  # noqa: E731
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (n, g("raw", "QI"), g("unf", "QI"), g("unf_v2", "QI"), g("raw", "US_clean"),
                                                                             g("unf", "US_clean"), g("unf_v2", "US_clean"), g("raw", "inversion"),
                                                                             g("unf_v2", "inversion"), a("raw"), a("unf_v2")))
    L += ["", "## 3. Small local LLM judges (RAGAS-NLI prompt, vLLM, temperature 0)", "", "### Models", "",
          "| slug | HF id | params (B) | status | revision | backend | rows card/rag/rd | p_yes missing card/rag/rd | unit-blindness gone? |", "|" + "---|" * 9]
    for s, j in res["judges"].items():
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (s, j["hf_id"], j["params_b"], j["status"], (j["revision"] or "")[:10], j["backend"] or "",
                                                                    "/".join(str(j["rows"][p]) for p in ("card", "rag", "rd")),
                                                                    "/".join(str(j["p_yes_missing"][p]) for p in ("card", "rag", "rd")),
                                                                    {True: "yes", False: "no", None: "NA"}[j["unit_blindness_gone"]]))
    L += ["", "Criterion: C0, QI, US claim↑ and US claim↓ ≥ 80% on the card and RAG unit-up / unit-down FAIL|C0 ≥ 80% (point estimates).", "",
          "### Main DOSE card (paper cells, C0-conditional; same frozen cohort as the paper table)", ""] + CARD_HDR
    for s, m in sorted(res["judge_card"].items(), key=lambda kv: res["judges"][kv[0]]["params_b"]):
        L.append(card_row_md("%s (%sB)" % (s, res["judges"][s]["params_b"]), m))
    for n, m in res["ref_card"].items():
        L.append(card_row_md("ref: " + n, m))
    if res.get("llama8b_agreement"):
        L += ["", "Llama-3.1-8B vLLM (chain 3) verdict agreement on the card: " + "; ".join(
            "%s %d/%d" % (k, v["agree"], v["n"]) for k, v in res["llama8b_agreement"].items())]
    L += ["", "### Journal RAG pack (question-clustered)", "", "| judge | " + " | ".join(lab.replace("|", "\\|") for lab, _, _, _ in RAG_CELLS) + " |", "|" + "---|" * (1 + len(RAG_CELLS))]
    for s, b in sorted(res["judge_rag"].items(), key=lambda kv: res["judges"][kv[0]]["params_b"]):
        L.append(rag_row_md(s, b))
    for n, b in res["ref_rag"].items():
        L.append(rag_row_md("ref: " + n, b))
    L += ["", "RD results for the judges are in section 1 (rows `judge <slug>`).", "",
          "Caveats: T19 local Llama rows used HF transformers (not vLLM); API rows are provider-served; MedGemma is a multimodal "
          "Gemma-3 checkpoint used text-only; p_yes is read from the verdict-digit top-20 logprobs (missing -> 0/1 score)."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
