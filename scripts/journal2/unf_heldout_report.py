#!/usr/bin/env python3
"""(UNF-HO-4) Report for the HELD-OUT UNF evaluation (CPU, no models, no API).

(a) normalizer level (always): parse accuracy of UNF v1 (src/unit_norm_fix.py, pre-specified) and of the FROZEN
    post-hoc v2 (src/unit_norm_fix_v2.py; sha256 checked against results/journal2/unf_v2_freeze.json) on
      * REAL dose strings as written (primary): LLM-answer mentions (rd_answer + rd_answer_free) and label mentions
        (the RD excerpt mention supporting each answer, and the openFDA label mentions), in their real context;
      * all 300 test claims (S + U, incl. the constructed swaps/conversions), and the end-to-end pair outcome;
    drug-clustered bootstrap CIs, paired v2-v1 delta, a surface-feature breakdown and the list of failures.
(b) checker level (when scores exist): 5 small checkers x packs orig / unf (v1) / unf_v2 (v2)
      held-out: QI = PASS on S, US = FAIL on U (anchor-conditional and unconditional), inversion = share of bases whose
                S score <= U score, AUC(S > U); paired deltas vs raw text;
      RD pairs : QI = PASS on auto-`correct` answers, US = FAIL on auto unit-type errors (and on the AI-pre-check
                 `true_unit_error` subset), FAIL on value errors; rows unchanged by the normalizer keep the stored
                 verdict, changed rows use the same-run re-score (orig re-scored = before).
Outputs: notes/unf_heldout.md, results/journal2/unf_heldout/report.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from unf_adv_report import boot_rate, f, fd, paired_delta  # noqa: E402

DATA = ROOT / "data/journal2/unf_heldout.jsonl"
RDPACK = ROOT / "results/journal2/unf_heldout/rd_pack.jsonl"
SCORES = ROOT / "results/journal2/unf_heldout/scores"
RDSCORES = ROOT / "results/journal2/unf_heldout/rd_scores"
RD = ROOT / "results/journal2/real_dose"
PRECHECK = ROOT / "qc/ai_precheck_real_dose_unit_errors.csv"
OUTJ = ROOT / "results/journal2/unf_heldout/report.json"
NOTE = ROOT / "notes/unf_heldout.md"
FREEZE = ROOT / "results/journal2/unf_v2_freeze.json"
CHECKERS = [("t6a_minicheck_roberta", "MiniCheck-RoBERTa", "t6_minicheck_roberta.jsonl"),
            ("t6a_minicheck_deberta", "MiniCheck-DeBERTa", "t6_minicheck_deberta.jsonl"),
            ("t6a_alignscore_base", "AlignScore-base", "t6_alignscore_base.jsonl"),
            ("v2a_minicheck", "MiniCheck-Flan-T5-Large", "v2a_minicheck.jsonl"),
            ("v3_alignscore", "AlignScore-large", "v3_alignscore.jsonl")]
PACKS = [("orig", "raw text"), ("unf", "UNF v1"), ("unf_v2", "UNF v2 (frozen post-hoc)")]


def read_jsonl(p: Path) -> list:
    out = []
    if Path(p).is_file():
        for l in Path(p).open(encoding="utf-8"):
            if l.strip():
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    return out


def scores(p: Path) -> dict:
    return {r["instance_id"]: r for r in read_jsonl(p) if r.get("verdict") in ("PASS", "FAIL")}


def verdicts_stored(p: Path) -> dict:
    out = {}
    for r in read_jsonl(p):
        v = r.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[r["instance_id"]] = v
        elif r.get("score") is not None:
            out[r["instance_id"]] = "PASS" if float(r["score"]) > 0.5 else "FAIL"
    return out


# ------------------------------------------------------------------ surface features of real strings (own rules)
FEATURES = [
    ("lost superscript 'm 2'", r"m 2"),
    ("no space number-unit ('8mEq', '500-750mg')", r"\d(?:mg|mcg|mEq|mL|g)\b"),
    ("range, unit on both ends", r"\d\s*[a-zµμ]+\S*\s+(?:to|-)\s+\d[\d.,]*\s*[a-zµμ]"),
    ("hyphen range ('2-5 mcg')", r"\d-\d"),
    ("'to' range", r"\d\s+to\s+\d"),
    ("spelled unit / denominator ('micrograms per kilogram')", r"milligram|microgram|gram|kilogram|per (?:kg|minute|day|m2)"),
    ("spelled time denominator ('/minute', '/hour', '/24 hr', '/daily dose')", r"/(?:minute|hour|24 hr|daily)"),
    ("'million units'", r"million"),
    ("units (singular 'unit' / units)", r"\bunits?\b"),
    ("thousands comma", r"\d,\d{3}"),
    ("mEq", r"mEq"),
    ("concentration (/mL)", r"/\s*mL"),
    ("per-kg/m2/time basis (abbreviated)", r"/(?:kg|m²|m2|day|min|h)\b"),
    ("mcg/µg", r"mcg|µg"),
    ("plain number + unit", r"."),
]


def feature(m: str) -> str:
    for name, rx in FEATURES:
        if re.search(rx, m):
            return name
    return "other"


def why_type(w: str) -> str:
    return w.split(" (")[0].split(" from ")[0].replace("wrong key", "wrong basis/kind").split(" mass")[0] if w else ""


def real_units(rows: list) -> list:
    """(group, row, ok_key_prefix, mention, why_key) for every real string as written."""
    out = []
    for r in rows:
        if r["source"] in ("rd_answer", "rd_answer_free") and r["family"] in ("S", "parse_only"):
            out.append(("LLM answer", r, "", r["mention"]))
        if r["source"] == "rd_answer" and r["family"] == "S":
            out.append(("RD label excerpt", r, "ev_", r["evidence_span"]))
        if r["source"] == "label" and r["family"] == "anchor":
            out.append(("openFDA label", r, "", r["mention"]))
    return out


def residual(r: dict) -> bool:
    """U claim still contains a correct copy of the same dose elsewhere (raw-text check, whitespace-insensitive):
    the swap replaced one occurrence, but the answer/label window repeats the dose.  Such U claims are still
    UNSUPPORTED (they contain a false dose statement), but containment-based pair scoring cannot detect them."""
    rest = re.sub(r"\s+", "", r["claim"][:r["surface_start"]] + " | " + r["claim"][r["surface_end"]:]).lower()
    return any(re.sub(r"\s+", "", x).lower() in rest for x in (r.get("mention") or "", r.get("evidence_span") or "") if x)


def auc(pos: list, neg: list):
    if not pos or not neg:
        return None
    p, n = np.array(pos, float), np.array(neg, float)
    gt = (p[:, None] > n[None, :]).sum() + 0.5 * (p[:, None] == n[None, :]).sum()
    return float(gt / (len(p) * len(n)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--scores", default=str(SCORES))
    ap.add_argument("--rd-scores", default=str(RDSCORES))
    ap.add_argument("--out-json", default=str(OUTJ))
    ap.add_argument("--out-md", default=str(NOTE))
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args()
    sha = hashlib.sha256((ROOT / "src/unit_norm_fix_v2.py").read_bytes()).hexdigest()
    frz = json.loads(FREEZE.read_text())
    rows = read_jsonl(Path(args.data))
    if not rows:
        raise SystemExit("no held-out data (run scripts/journal2/unf_heldout_build.py)")
    B = args.boot
    res = {"generated_by": "scripts/journal2/unf_heldout_report.py", "v2_sha256": sha, "v2_frozen_sha256": frz["sha256"],
           "v2_matches_freeze": sha == frz["sha256"], "freeze_record": frz, "n_rows": len(rows),
           "rows_by_family": dict(Counter(r["family"] for r in rows)),
           "rows_by_source_family": {s: dict(Counter(r["family"] for r in rows if r["source"] == s)) for s in sorted({r["source"] for r in rows})},
           "n_drugs": len({r["drug"] for r in rows}),
           "U_residual": dict(Counter(r["source"] for r in rows if r["family"] == "U" and residual(r))), "normalizer": {}, "checkers": {}, "rd": {}}
    # ---------------- (a) normalizer level
    RU = real_units(rows)
    test = [r for r in rows if r["family"] in ("S", "U")]
    for v in ("v1", "v2"):
        ok = lambda r, k: bool(r[v + "_" + k + "parse_ok"])  # noqa: E731
        d = {"real_all": boot_rate([(r["drug"], int(ok(r, k))) for _, r, k, _ in RU], None, B),
             "real_by_group": {g: boot_rate([(r["drug"], int(ok(r, k))) for gg, r, k, _ in RU if gg == g], None, B)
                               for g in ("LLM answer", "RD label excerpt", "openFDA label")},
             "test_claims": boot_rate([(r["drug"], int(r[v + "_parse_ok"])) for r in test], None, B),
             "test_by_label": {l: boot_rate([(r["drug"], int(r[v + "_parse_ok"])) for r in test if r["label"] == l], None, B)
                               for l in ("SUPPORTED", "UNSUPPORTED")},
             "test_by_source": {s: boot_rate([(r["drug"], int(r[v + "_parse_ok"])) for r in test if r["source"] == s], None, B)
                                for s in ("rd_answer", "label")},
             "pair_outcome": boot_rate([(r["drug"], int(r[v + "_pair_ok"])) for r in test], None, B),
             "pair_U_clean": boot_rate([(r["drug"], int(r[v + "_pair_ok"])) for r in test if r["label"] == "UNSUPPORTED" and not residual(r)], None, B),
             "pair_U_residual": boot_rate([(r["drug"], int(r[v + "_pair_ok"])) for r in test if r["label"] == "UNSUPPORTED" and residual(r)], None, B),
             "pair_by_label": {l: boot_rate([(r["drug"], int(r[v + "_pair_ok"])) for r in test if r["label"] == l], None, B)
                               for l in ("SUPPORTED", "UNSUPPORTED")},
             "anchors_parse_ok": "%d/%d" % (sum(int(r[v + "_parse_ok"]) for r in rows if r["family"] == "anchor"),
                                            sum(1 for r in rows if r["family"] == "anchor"))}
        d["real_failures"] = [{"group": g, "id": r["instance_id"], "drug": r["drug"], "mention": m, "gold": r[k + "gold_str"] if k else r["gold_str"],
                               "why": r[v + "_" + k + "parse_why"], "feature": feature(m)} for g, r, k, m in RU if not ok(r, k)]
        d["test_failures"] = [{"id": r["instance_id"], "label": r["label"], "source": r["source"], "variant": r["variant"],
                               "why": r[v + "_parse_why"]} for r in test if not r[v + "_parse_ok"]]
        res["normalizer"][v] = d
    # paired delta v2 - v1 on real strings and on test claims (drug-clustered)
    for name, units in (("real_all", [(r["drug"], int(r["v1_" + k + "parse_ok"]), int(r["v2_" + k + "parse_ok"])) for _, r, k, _ in RU]),
                        ("test_claims", [(r["drug"], int(r["v1_parse_ok"]), int(r["v2_parse_ok"])) for r in test])):
        a, b = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
        for dname, x1, x2 in units:
            a[dname][0] += x1; a[dname][1] += 1; b[dname][0] += x2; b[dname][1] += 1  # noqa: E702
        res["normalizer"]["delta_v2_minus_v1_" + name] = paired_delta(dict(a), dict(b), min(B, 5000))
        res["normalizer"]["discordant_" + name] = {"v1_only_ok": sum(1 for _, x1, x2 in units if x1 and not x2),
                                                   "v2_only_ok": sum(1 for _, x1, x2 in units if x2 and not x1)}
    res["normalizer"]["v2_regressions_vs_v1"] = [
        {"group": g, "id": r["instance_id"], "drug": r["drug"], "mention": m, "v2_why": r["v2_" + k + "parse_why"]}
        for g, r, k, m in RU if r["v1_" + k + "parse_ok"] and not r["v2_" + k + "parse_ok"]] + [
        {"group": "test claim " + r["label"], "id": r["instance_id"], "drug": r["drug"], "mention": r["variant"], "v2_why": r["v2_parse_why"]}
        for r in test if r["v1_parse_ok"] and not r["v2_parse_ok"]]
    feats = Counter(feature(m) for _, _, _, m in RU)
    res["normalizer"]["real_by_feature"] = {fe: {"n": n, "v1_ok": sum(1 for _, r, k, m in RU if feature(m) == fe and r["v1_" + k + "parse_ok"]),
                                                 "v2_ok": sum(1 for _, r, k, m in RU if feature(m) == fe and r["v2_" + k + "parse_ok"])}
                                            for fe, n in feats.most_common()}
    res["normalizer"]["real_failure_types"] = {v: dict(Counter(why_type(x["why"]) for x in res["normalizer"][v]["real_failures"]))
                                               for v in ("v1", "v2")}
    # ---------------- (b1) checker level, held-out pairs
    anchors = {}
    for r in rows:
        if r["family"] == "anchor":
            anchors[r["cid"]] = r
    S_ = {r["cid"]: r for r in rows if r["family"] == "S"}
    U_ = {r["cid"]: r for r in rows if r["family"] == "U"}
    sroot = Path(args.scores)
    for ck, name, _ in CHECKERS:
        sc = {p: scores(sroot / p / (ck + ".jsonl")) for p, _ in PACKS}
        if not sc["orig"]:
            res["checkers"][name] = {"status": "not scored yet"}
            continue
        out = {"coverage": {p: "%d/%d" % (sum(1 for r in rows if r["instance_id"] in sc[p]), sum(1 for r in rows if r["family"] != "parse_only"))
                            for p, _ in PACKS}, "packs": {}, "deltas": {}}
        per = {}
        okb0 = {c for c, a in anchors.items() if sc["orig"].get(a["instance_id"], {}).get("verdict") == "PASS"}
        for p, _ in PACKS:
            if not sc[p]:
                continue
            okb = {c for c, a in anchors.items() if sc[p].get(a["instance_id"], {}).get("verdict") == "PASS"}
            m = {"anchor_pass": "%d/%d" % (len(okb), len(anchors))}
            for metric, fam, want in (("QI", S_, "PASS"), ("US", U_, "FAIL")):
                sel = [r for r in fam.values() if r["instance_id"] in sc[p]]
                val = lambda r: int(sc[p][r["instance_id"]]["verdict"] == want)  # noqa: E731
                m[metric] = boot_rate([(r["drug"], val(r)) for r in sel if r["cid"] in okb], None, B)
                m[metric + "_uncond"] = boot_rate([(r["drug"], val(r)) for r in sel], None, B)
                if metric == "US":
                    m["US_clean"] = boot_rate([(r["drug"], val(r)) for r in sel if r["cid"] in okb and not residual(r)], None, B)
                    m["US_residual"] = boot_rate([(r["drug"], val(r)) for r in sel if r["cid"] in okb and residual(r)], None, B)
                for src in ("rd_answer", "label"):
                    m["%s_%s" % (metric, src)] = boot_rate([(r["drug"], val(r)) for r in sel if r["cid"] in okb and r["source"] == src], None, B)
                cnt = defaultdict(lambda: [0, 0])
                for r in sel:
                    if r["cid"] in okb0:
                        cnt[r["drug"]][0] += val(r)
                        cnt[r["drug"]][1] += 1
                per[(p, metric)] = dict(cnt)
            both = [c for c in S_ if S_[c]["instance_id"] in sc[p] and U_[c]["instance_id"] in sc[p]]
            inv = [(S_[c]["drug"], int(float(sc[p][S_[c]["instance_id"]]["score"]) <= float(sc[p][U_[c]["instance_id"]]["score"]))) for c in both]
            m["inversion"] = boot_rate(inv, None, B)
            m["auc_S_gt_U"] = auc([float(sc[p][S_[c]["instance_id"]]["score"]) for c in both],
                                  [float(sc[p][U_[c]["instance_id"]]["score"]) for c in both])
            out["packs"][p] = m
        for p in ("unf", "unf_v2"):
            for metric in ("QI", "US"):
                if (p, metric) in per:
                    out["deltas"]["%s_%s" % (metric, p)] = paired_delta(per[("orig", metric)], per[(p, metric)], min(B, 2000))
        res["checkers"][name] = out
    # ---------------- (b2) checker level, RD pairs
    pack = {r["instance_id"]: r for r in read_jsonl(RDPACK)}
    inst = read_jsonl(RD / "instances.jsonl")
    pre = {}
    if PRECHECK.is_file():
        with PRECHECK.open(encoding="utf-8") as fh:
            pre = {r["instance_id"]: r["ai_label"] for r in csv.DictReader(l for l in fh if not l.startswith("#"))}
    groups = {"QI_correct": lambda r: r["auto_class"] == "correct",
              "US_unit_type_auto": lambda r: r["auto_class"] in ("unit_error", "basis_error"),
              "US_unit_type_precheck_true": lambda r: pre.get(r["instance_id"]) == "true_unit_error",
              "US_same_numeral_auto": lambda r: r["auto_class"] == "unit_error",
              "US_value_auto": lambda r: r["auto_class"] == "value_error"}
    rroot = Path(args.rd_scores)
    res["rd"]["pack_rows"] = len(pack)
    res["rd"]["pack_changed"] = {"v1": sum(1 for r in pack.values() if r["v1_changed"]), "v2": sum(1 for r in pack.values() if r["v2_changed"])}
    res["rd"]["group_sizes"] = {g: sum(1 for r in inst if fn(r)) for g, fn in groups.items()}
    res["rd"]["group_sizes_changed"] = {v: {g: sum(1 for r in inst if fn(r) and pack.get(r["instance_id"], {}).get(v + "_changed")) for g, fn in groups.items()}
                                       for v in ("v1", "v2")}
    res["rd"]["checkers"] = {}
    for ck, name, stored_f in CHECKERS:
        st = verdicts_stored(RD / "scores" / stored_f)
        sc = {p: scores(rroot / p / (ck + ".jsonl")) for p, _ in PACKS}
        need = [i for i in pack]
        cov = {p: sum(1 for i in need if i in sc[p]) for p, _ in PACKS}
        if cov["orig"] < len(need):
            res["rd"]["checkers"][name] = {"status": "not fully scored (%s of %d)" % (cov, len(need))}
            continue
        d = {"coverage": cov, "env_agreement_orig_rescored_vs_stored": [sum(1 for i in need if sc["orig"][i]["verdict"] == st.get(i)),
                                                                        sum(1 for i in need if st.get(i) in ("PASS", "FAIL"))], "packs": {}}
        for p, _ in PACKS:
            if cov[p] < len(need):
                continue
            col = {}
            for r in inst:
                i = r["instance_id"]
                v = sc[p][i]["verdict"] if i in pack else st.get(i)
                if v in ("PASS", "FAIL"):
                    col[i] = v
            d["packs"][p] = {}
            for g, fn in groups.items():
                want = "PASS" if g.startswith("QI") else "FAIL"
                d["packs"][p][g] = boot_rate([(r["drug"], int(col[r["instance_id"]] == want)) for r in inst if fn(r) and r["instance_id"] in col], None, B)
        res["rd"]["checkers"][name] = d
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n")
    write_md(res, Path(args.out_md))
    print(json.dumps({"wrote": [args.out_json, args.out_md], "v2_matches_freeze": res["v2_matches_freeze"],
                      "v1_real": res["normalizer"]["v1"]["real_all"]["rate"], "v2_real": res["normalizer"]["v2"]["real_all"]["rate"],
                      "v1_test": res["normalizer"]["v1"]["test_claims"]["rate"], "v2_test": res["normalizer"]["v2"]["test_claims"]["rate"],
                      "checkers": {k: ("scored" if "packs" in v else v["status"]) for k, v in res["checkers"].items()},
                      "rd": {k: ("scored" if "packs" in v else v["status"]) for k, v in res["rd"]["checkers"].items()}}))


def write_md(res: dict, path: Path) -> None:
    N = res["normalizer"]
    n1, n2 = N["v1"], N["v2"]
    fam = res["rows_by_family"]
    L = ["# Held-out evaluation of the unit normalizers (UNF v1 vs frozen v2) on REAL dose strings", "",
         "Generated by `scripts/journal2/unf_heldout_report.py`. Data: `data/journal2/unf_heldout.jsonl` (built by "
         "`scripts/journal2/unf_heldout_build.py`, manual gold in `scripts/journal2/unf_heldout_gold.py`).", "",
         "**Freeze.** `src/unit_norm_fix_v2.py` was frozen in commit `81d078b` (`results/journal2/unf_v2_freeze.json`, "
         "sha256 `%s…`, %s) before any held-out data existed; the gold table was committed (`19cc00b`) before the "
         "normalizers' outputs were inspected. Current v2 sha256 matches the freeze: **%s**. v2 was developed on the "
         "synthetic adversarial set (`data/journal2/unf_adversarial.jsonl`); this set is its first held-out test." % (
             res["v2_frozen_sha256"][:16], res["freeze_record"]["frozen_at"], "yes" if res["v2_matches_freeze"] else "NO -- v2 CHANGED"), "",
         "**Gold labels are AI-adjudicated** (Grok Bot agent, from the raw text, without running either normalizer) and "
         "need a human spot check before publication.", "",
         "## Composition", "",
         "- %d rows over %d drugs (none of the drugs used as bases in the adversarial set): %d S (should PASS), %d U (should "
         "FAIL), %d anchors, %d parse-only real strings." % (res["n_rows"], res["n_drugs"], fam.get("S", 0), fam.get("U", 0),
                                                             fam.get("anchor", 0), fam.get("parse_only", 0)),
         "- Sources: `rd_answer` = dose mention as written in a real-dose LLM answer (gpt-4o-mini / gemma-3-27b) paired with "
         "that question's FDA-label excerpt (S = the real answer as written; U = same answer, mention unit swapped; anchor = "
         "answer with the label's own surface); `label` = dose mention as written in openFDA label text (evidence = real "
         "label sentence; S = sentence with a correct conversion/respelling; U = label numeral with a swapped unit; anchor = "
         "sentence verbatim); `rd_answer_free` = random closed-book answer mentions (parse-only). By source/family: %s." % (
             "; ".join("%s %s" % (s, d) for s, d in res["rows_by_source_family"].items())), "",
         "## (a) Normalizer level", "",
         "Correct = exactly one dose span over the mention with the gold kind/basis/value (same rule as the adversarial "
         "report). Drug-clustered 95% CIs.", "",
         "| set | UNF v1 | UNF v2 (frozen) |", "|---|---|---|",
         "| **real strings as written (all)** | %s | %s |" % (f(n1["real_all"]), f(n2["real_all"]))]
    for g in ("LLM answer", "RD label excerpt", "openFDA label"):
        L.append("| real: %s | %s | %s |" % (g, f(n1["real_by_group"][g]), f(n2["real_by_group"][g])))
    L += ["| all 300 test claims (S + U) | %s | %s |" % (f(n1["test_claims"]), f(n2["test_claims"])),
          "| test claims SUPPORTED | %s | %s |" % (f(n1["test_by_label"]["SUPPORTED"]), f(n2["test_by_label"]["SUPPORTED"])),
          "| test claims UNSUPPORTED | %s | %s |" % (f(n1["test_by_label"]["UNSUPPORTED"]), f(n2["test_by_label"]["UNSUPPORTED"])),
          "| end-to-end pair outcome (S + U) | %s | %s |" % (f(n1["pair_outcome"]), f(n2["pair_outcome"])),
          "| pair outcome, U without residual correct copy | %s | %s |" % (f(n1["pair_U_clean"]), f(n2["pair_U_clean"])),
          "| pair outcome, U with residual correct copy | %s | %s |" % (f(n1["pair_U_residual"]), f(n2["pair_U_residual"])),
          "| anchors parsed | %s | %s |" % (n1["anchors_parse_ok"], n2["anchors_parse_ok"]), "",
          "Pair outcome = the adversarial-set rule: S passes if the normalized claim contains the normalized evidence span; "
          "U passes if the swap was parsed correctly and the normalized claim does NOT contain it. %s U claims (by source) "
          "keep another correct copy of the same dose elsewhere in the answer/label window (the swap replaced one "
          "occurrence); they remain UNSUPPORTED (they contain a false dose) but the containment rule cannot pass them, so "
          "the clean-U row is the meaningful one." % res["U_residual"], "",
          "Paired v2 − v1 (points, drug-clustered bootstrap): real strings %s (discordant: v2-only correct %d, v1-only correct %d); "
          "test claims %s (v2-only %d, v1-only %d)." % (
              fd({"delta": N["delta_v2_minus_v1_real_all"]["delta"], "ci": N["delta_v2_minus_v1_real_all"]["ci"]}),
              N["discordant_real_all"]["v2_only_ok"], N["discordant_real_all"]["v1_only_ok"],
              fd(N["delta_v2_minus_v1_test_claims"]), N["discordant_test_claims"]["v2_only_ok"], N["discordant_test_claims"]["v1_only_ok"]), "",
          "### Real strings by surface feature (first matching feature)", "", "| feature | n | v1 correct | v2 correct |", "|---|---|---|---|"]
    for fe, d in N["real_by_feature"].items():
        L.append("| %s | %d | %d | %d |" % (fe, d["n"], d["v1_ok"], d["v2_ok"]))
    L += ["", "Failure types (real strings): v1 %s; v2 %s. Note: grounded answers often copy the excerpt surface, so the same "
          "string can appear once as an LLM-answer mention and once as the RD-excerpt mention (dependence handled by "
          "drug clustering)." % (N["real_failure_types"]["v1"], N["real_failure_types"]["v2"]), "",
          "**v2 regressions vs v1 (v1 correct, frozen v2 wrong) -- reported, NOT fixed (v2 is frozen):** " +
          ("; ".join("[%s] %s `%s`: %s" % (x["group"], x["drug"], x["mention"], x["v2_why"]) for x in N["v2_regressions_vs_v1"]) or "none"), ""]
    for v, d in (("v1", n1), ("v2 (frozen)", n2)):
        L += ["### %s failures on real strings (%d)" % (v, len(d["real_failures"])), ""]
        for x in d["real_failures"]:
            L.append("- [%s] %s `%s` (gold %s): %s" % (x["group"], x["drug"], x["mention"], x["gold"], x["why"]))
        L.append("")
    L += ["### Test-claim failures (constructed S/U variants; v1 %d, v2 %d)" % (len(n1["test_failures"]), len(n2["test_failures"])), ""]
    for v, d in (("v1", n1), ("v2", n2)):
        for x in d["test_failures"]:
            L.append("- %s %s [%s] %s: %s" % (v, x["label"][0], x["source"], x["variant"], x["why"]))
    L += ["", "## (b) Checker level", ""]
    sc = {k: v for k, v in res["checkers"].items() if "packs" in v}
    if not sc:
        L += ["Held-out pairs not scored yet: run `sbatch jobs/journal2/jr2_UNFHO.sbatch` on the HPC (the last array task "
              "reruns this script).", ""]
    else:
        L += ["### Held-out pairs", "", "QI = PASS on S; US = FAIL on U; anchor-conditional (anchor PASSes in the same pack). "
              "Inversion = share of bases whose S score ≤ U score (threshold-free; lower is better). Δ = pack − raw text, "
              "paired drug-clustered bootstrap on bases whose anchor PASSes on raw text.", "",
              "| checker | metric | raw text | UNF v1 | Δ v1 | UNF v2 | Δ v2 |", "|---|---|---|---|---|---|---|"]
        for name, d in sc.items():
            P = d["packs"]
            for metric in ("QI", "US"):
                L.append("| %s | %s | %s | %s | %s | %s | %s |" % (name, metric, f(P.get("orig", {}).get(metric)), f(P.get("unf", {}).get(metric)),
                                                                fd(d["deltas"].get(metric + "_unf", {"delta": None})), f(P.get("unf_v2", {}).get(metric)),
                                                                fd(d["deltas"].get(metric + "_unf_v2", {"delta": None}))))
            L.append("| %s | US (U w/o residual copy) | %s | %s | | %s | |" % (name, *[f(P.get(p, {}).get("US_clean")) for p in ("orig", "unf", "unf_v2")]))
            L.append("| %s | inversion | %s | %s | | %s | |" % (name, f(P.get("orig", {}).get("inversion")), f(P.get("unf", {}).get("inversion")),
                                                              f(P.get("unf_v2", {}).get("inversion"))))
            L.append("| %s | AUC(S>U) | %s | %s | | %s | |" % (name, *["%.3f" % P[p]["auc_S_gt_U"] if P.get(p, {}).get("auc_S_gt_U") is not None else "NA"
                                                                     for p in ("orig", "unf", "unf_v2")]))
        L += ["", "By source (anchor-conditional): " + "; ".join("%s %s" % (n, {p: {m: "%s" % (f(d["packs"][p].get(m)))
                                                                                     for m in ("QI_rd_answer", "QI_label", "US_rd_answer", "US_label")}
                                                                                for p in d["packs"]}) for n, d in sc.items()), ""]
    rd = res["rd"]
    L += ["### Real-dose (RD) pairs", "",
          "RD rows changed by the normalizer: v1 %d, v2 %d (of 1451). Group sizes (all / changed by v1 / by v2): %s." % (
              rd["pack_changed"]["v1"], rd["pack_changed"]["v2"],
              "; ".join("%s %d/%d/%d" % (g, n, rd["group_sizes_changed"]["v1"][g], rd["group_sizes_changed"]["v2"][g]) for g, n in rd["group_sizes"].items())), ""]
    rs = {k: v for k, v in rd["checkers"].items() if "packs" in v}
    if not rs:
        L += ["Not scored yet (" + "; ".join("%s: %s" % (k, v.get("status")) for k, v in rd["checkers"].items()) + ").", ""]
    else:
        L += ["QI = PASS on auto-`correct` answers; US = FAIL on errors (auto unit-type; AI-pre-check `true_unit_error` subset; "
              "auto same-numeral; auto value). Unchanged rows keep the stored verdict; changed rows use the same-run re-score.", "",
              "| checker | group | raw text | UNF v1 | UNF v2 |", "|---|---|---|---|---|"]
        for name, d in rs.items():
            for g in ("QI_correct", "US_unit_type_auto", "US_unit_type_precheck_true", "US_same_numeral_auto", "US_value_auto"):
                L.append("| %s | %s | %s | %s | %s |" % (name, g, *[f(d["packs"].get(p, {}).get(g)) for p in ("orig", "unf", "unf_v2")]))
        L += ["", "Env agreement (re-scored raw text vs stored paper verdicts, changed rows): " +
              "; ".join("%s %d/%d" % (n, *d["env_agreement_orig_rescored_vs_stored"]) for n, d in rs.items()), ""]
    L += ["## Caveats", "",
          "- Gold canonical quantities and the S/NOT-supported decisions for answers are AI-adjudicated (no human yet); "
          "a human should spot-check at least the failures listed above and a random 10-20% of the rest.",
          "- Real-world frequency: `rd_answer` mentions are stratified by surface feature (rare forms over-represented); "
          "`rd_answer_free` (30 random closed-book mentions) is the unweighted realism check. Grounded answers often copy the "
          "label verbatim, so many S pairs are surface-identical (no normalization needed).",
          "- The label cache was itself selected with v1 (`rd_fetch_labels.py` keeps labels with >=1 v1-parseable dose); "
          "candidate mentions were found with this script's own pattern, which can miss forms both normalizers also miss "
          "(e.g. number words), so absolute accuracy is an upper bound for unusual spellings.",
          "- Gold follows stated conventions (frequency words are not part of a mention; a range with the unit on both ends "
          "is one mention; table-header units are not part of a contiguous mention).",
          "- v2 is post-hoc (developed on the adversarial set) but frozen before this set: these held-out numbers are the "
          "defensible v2 numbers; adversarial-set v2 numbers remain optimistic.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
