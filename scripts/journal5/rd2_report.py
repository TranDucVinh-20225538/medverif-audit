#!/usr/bin/env python3
"""(RD2-7) Pre-registered RD2 analyses (prereg/rd2_prereg.md, section 6).  CPU, stdlib, deterministic.

Reference standard: pharmacist adjudication (results/journal5/rd2/qc/rd2_adjudication_sheet.csv filled in, passed with
--adjudicated; joined to rd2_adjudication_key.csv).  Without it, every number is printed as PROVISIONAL (auto labels:
error = rd_extract unit_error+basis_error, non-error = auto correct) and must not be reported as a result.

  P1  each of the 7 paper checkers: PASS rate on natural unit/basis errors (Wilson 95% CI; drug-cluster bootstrap 95% CI
      secondary); PARSE_FAIL excluded from the denominator and counted (sensitivity: PARSE_FAIL = FAIL).
  P2  frozen basis check (fdb95de, full = primary, strict = secondary): recall on adjudicated unit/basis errors found
      INDEPENDENTLY of the rule (sources A auto-extractor or C random control) = primary; recall on all adjudicated
      errors = secondary; PPV of flags; false-alarm rate = flags adjudicated not-a-unit/basis-error / estimated
      non-error answers (adjudicated-negative rate in the random controls extrapolated to the unselected rest).
  P3  transfer: (a) chain-1 fine-tuned MiniCheck-Flan-T5 (r1 primary; r0.5/r2/base and AlignScore-large FT secondary):
      FAIL rate on errors and PASS rate on non-errors vs the same-path base; (b) UNF v1 / frozen UNF v2 applied before the
      5 small checkers and the FT models: PASS rate on errors / non-errors raw vs UNF (unchanged rows keep raw verdicts).
  S   secondary: P1 for the chain-3 local LLM judges; error rates by generator / condition / dosing stratum.
Output: results/journal5/rd2/report.json + report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import RD2, RD2_DIR, ROOT, log, read_jsonl  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "journal3"))
from j3_common import verdict_map  # noqa: E402

PAPER = OrderedDict([("MiniCheck-RoBERTa", "t6_minicheck_roberta"), ("MiniCheck-DeBERTa", "t6_minicheck_deberta"),
                     ("AlignScore-base", "t6_alignscore_base"), ("MiniCheck-Flan-T5-Large", "v2a_minicheck"),
                     ("AlignScore-large", "v3_alignscore"), ("Llama-3.3-70B RAGAS", "v4_ragas_nli"),
                     ("MedScore (Mistral-Small-24B)", "v1_medscore")])
SMALL = list(PAPER.values())[:5]
ERR_TYPES = ("unit", "basis")


def wilson(k, n, z=1.959964):
    if not n:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [round(100 * max(0.0, c - h), 1), round(100 * min(1.0, c + h), 1)]


def cluster_ci(pairs, n_boot=5000, seed=20261002):
    """pairs: [(cluster, hit 0/1)] -> percentile 95% CI of the pooled rate over resampled clusters (%)."""
    by = defaultdict(lambda: [0, 0])
    for c, h in pairs:
        by[c][0] += h
        by[c][1] += 1
    g = list(by.values())
    if len(g) < 2:
        return [None, None]
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        k = n = 0
        for _ in g:
            a, b = g[rng.randrange(len(g))]
            k += a
            n += b
        vals.append(k / n if n else 0.0)
    vals.sort()
    return [round(100 * vals[int(0.025 * (n_boot - 1))], 1), round(100 * vals[int(0.975 * (n_boot - 1))], 1)]


def rate(ids, hit, drug_of, boot=True):
    ids = list(ids)
    k = sum(1 for i in ids if hit(i))
    out = {"k": k, "n": len(ids), "pct": round(100.0 * k / len(ids), 1) if ids else None, "wilson95": wilson(k, len(ids))}
    if boot:
        out["drug_cluster95"] = cluster_ci([(drug_of[i], int(hit(i))) for i in ids])
    return out


def fmt(r):
    if not r or not r["n"]:
        return "–"
    s = "%d/%d = %.1f%% [%s, %s]" % (r["k"], r["n"], r["pct"], r["wilson95"][0], r["wilson95"][1])
    if r.get("drug_cluster95") and r["drug_cluster95"][0] is not None:
        s += " (drug-boot %s–%s)" % tuple(r["drug_cluster95"])
    return s


def load_reference(adjudicated, rows):
    """-> (err set, nonerr set, meta).  Adjudicated: error Y & type unit/basis = err; N = nonerr (other error types are
    neither).  Provisional: auto unit/basis = err, auto correct = nonerr."""
    if not adjudicated:
        err = {i for i, r in rows.items() if r["auto_class"] in ("unit_error", "basis_error")}
        non = {i for i, r in rows.items() if r["auto_class"] == "correct"}
        return err, non, {"reference": "PROVISIONAL auto labels (rd_extract) -- not the pre-registered reference standard"}
    key = {}
    with (RD2_DIR / "qc" / "rd2_adjudication_key.csv").open(encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            key[r["check_id"]] = r
    err, non, src, other = set(), set(), {}, Counter()
    with Path(adjudicated).open(encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            k = key[r["check_id"]]
            iid = k["instance_id"]
            src[iid] = k["sources"]
            yn = (r.get("human_answer_dose_is_error (Y/N/unclear)") or "").strip().upper()[:1]
            typ = (r.get("human_error_type (unit/basis/value/time/other_population_or_indication/none)") or "").strip().lower()
            if yn == "Y" and typ in ERR_TYPES:
                err.add(iid)
            elif yn == "N":
                non.add(iid)
            else:
                other[(yn or "blank") + ":" + (typ or "blank")] += 1
    n_ctrl = int(next(iter(key.values()))["n_selected_controls"]) if key else 0
    n_rest = int(next(iter(key.values()))["n_rest"]) if key else 0
    return err, non, {"reference": "pharmacist adjudication (%s)" % adjudicated, "sources": src, "other_labels": dict(other),
                      "n_controls": n_ctrl, "n_rest": n_rest}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adjudicated", default="", help="filled rd2_adjudication_sheet.csv (reference standard)")
    ap.add_argument("--out", default=str(RD2_DIR / "report"))
    args = ap.parse_args()
    rows = {r["instance_id"]: r for r in read_jsonl(RD2 / "instances.jsonl")}
    if not rows:
        raise SystemExit("no RD2 instances")
    drug = {i: r["drug"] for i, r in rows.items()}
    err, non, meta = load_reference(args.adjudicated, rows)
    prov = not args.adjudicated
    rep = OrderedDict(generated=time.strftime("%Y-%m-%dT%H:%M:%S%z"), provisional=prov, reference=meta["reference"],
                      n_instances=len(rows), n_err=len(err), n_nonerr=len(non))
    # descriptive
    rep["auto_class_by_generator"] = {"%s|%s" % k: v for k, v in sorted(Counter((r["generator"], r["auto_class"]) for r in rows.values()).items())}
    rep["err_by_stratum_condition"] = {"%s|%s" % k: v for k, v in sorted(Counter((rows[i].get("stratum"), rows[i]["answer_condition"]) for i in err).items())}
    # P1
    p1 = OrderedDict()
    for name, f in PAPER.items():
        vm = verdict_map(RD2 / "scores" / (f + ".jsonl"))
        if not vm:
            p1[name] = {"missing": str(RD2 / "scores" / (f + ".jsonl"))}
            continue
        e = [i for i in err if vm.get(i) in ("PASS", "FAIL")]
        c = [i for i in non if vm.get(i) in ("PASS", "FAIL")]
        p1[name] = {"pass_on_errors": rate(e, lambda i: vm[i] == "PASS", drug),
                    "pass_on_errors_parsefail_as_fail": rate([i for i in err if i in vm], lambda i: vm[i] == "PASS", drug, False),
                    "pass_on_nonerrors": rate(c, lambda i: vm[i] == "PASS", drug),
                    "parse_fail_on_errors": sum(1 for i in err if vm.get(i) == "PARSE_FAIL"),
                    "unscored_errors": sum(1 for i in err if i not in vm)}
    rep["P1_paper_checkers"] = p1
    # P2 basis check
    bc = {r["instance_id"]: r for r in read_jsonl(RD2_DIR / "basis_check" / "per_item.jsonl")}
    p2 = OrderedDict()
    if bc:
        srcs = meta.get("sources") or {}
        indep = [i for i in err if prov or ("A_auto" in srcs.get(i, "") or "C_control" in srcs.get(i, ""))]
        for v in ("full", "strict"):
            fl = lambda i, v=v: bool(bc.get(i, {}).get("flag_" + v))  # noqa: E731
            flagged = [i for i in rows if fl(i)]
            d = {"recall_independent_errors": rate(indep, fl, drug), "recall_all_errors": rate(list(err), fl, drug),
                 "flag_rate_all": rate(list(rows), fl, drug, False),
                 "flag_rate_on_nonerrors": rate(list(non), fl, drug, False)}
            if not prov:
                fp = [i for i in flagged if i in non]
                adjud = [i for i in flagged if i in err or i in non]
                d["ppv"] = rate(adjud, lambda i: i in err, drug, False)
                ctrl = [i for i, s in srcs.items() if s == "C_control"]
                neg_rate = (sum(1 for i in ctrl if i in non) / len(ctrl)) if ctrl else None
                est_neg = len([i for i in non if "C_control" not in srcs.get(i, "")]) + (neg_rate or 0) * meta["n_rest"]
                d["false_alarm_rate_est"] = {"fp_flags": len(fp), "est_negatives": round(est_neg, 1),
                                             "pct": round(100.0 * len(fp) / est_neg, 2) if est_neg else None}
            p2[v] = d
    rep["P2_basis_check_fdb95de"] = p2
    # P3 transfer
    p3 = OrderedDict()
    ftd = RD2_DIR / "ft"
    for p in sorted(ftd.glob("*__rd2_raw.jsonl")):
        vm = verdict_map(p)
        nm = p.name.split("__")[0]
        p3["FT " + nm] = {"fail_on_errors": rate([i for i in err if i in vm], lambda i: vm[i] == "FAIL", drug),
                          "pass_on_nonerrors": rate([i for i in non if i in vm], lambda i: vm[i] == "PASS", drug)}
    unf = OrderedDict()
    for var in ("unf_v1", "unf_v2"):
        for f in SMALL:
            raw = verdict_map(RD2 / "scores" / (f + ".jsonl"))
            ch = verdict_map(RD2 / "unf" / ("scores_" + var) / (f + ".jsonl"))
            if not raw or not ch:
                continue
            vm = dict(raw, **ch)
            unf["%s %s" % (f, var)] = {
                "pass_on_errors_raw": rate([i for i in err if raw.get(i) in ("PASS", "FAIL")], lambda i: raw[i] == "PASS", drug, False),
                "pass_on_errors_unf": rate([i for i in err if vm.get(i) in ("PASS", "FAIL")], lambda i: vm[i] == "PASS", drug, False),
                "pass_on_nonerrors_raw": rate([i for i in non if raw.get(i) in ("PASS", "FAIL")], lambda i: raw[i] == "PASS", drug, False),
                "pass_on_nonerrors_unf": rate([i for i in non if vm.get(i) in ("PASS", "FAIL")], lambda i: vm[i] == "PASS", drug, False)}
        for p in sorted(ftd.glob("*__rd2unf_%s.jsonl" % var.replace("unf_v1", "unf"))):
            nm = p.name.split("__")[0]
            raw = verdict_map(ftd / ("%s__rd2_raw.jsonl" % nm))
            vm = dict(raw, **verdict_map(p))
            unf["FT %s %s" % (nm, var)] = {
                "fail_on_errors_raw": rate([i for i in err if i in raw], lambda i: raw[i] == "FAIL", drug, False),
                "fail_on_errors_unf": rate([i for i in err if i in vm], lambda i: vm[i] == "FAIL", drug, False),
                "pass_on_nonerrors_raw": rate([i for i in non if i in raw], lambda i: raw[i] == "PASS", drug, False),
                "pass_on_nonerrors_unf": rate([i for i in non if i in vm], lambda i: vm[i] == "PASS", drug, False)}
    p3["UNF"] = unf
    rep["P3_transfer"] = p3
    # S local judges
    sj = OrderedDict()
    for p in sorted((RD2_DIR / "judges").glob("*__rd2.jsonl")):
        vm = verdict_map(p)
        sj[p.name.split("__")[0]] = {"pass_on_errors": rate([i for i in err if vm.get(i) in ("PASS", "FAIL")], lambda i: vm[i] == "PASS", drug),
                                     "pass_on_nonerrors": rate([i for i in non if vm.get(i) in ("PASS", "FAIL")], lambda i: vm[i] == "PASS", drug, False),
                                     "parse_fail_on_errors": sum(1 for i in err if vm.get(i) == "PARSE_FAIL")}
    rep["S_local_judges"] = sj
    out = Path(args.out)
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1, default=str) + "\n")
    tag = "PROVISIONAL (auto labels, NOT the reference standard)" if prov else "reference = pharmacist adjudication"
    L = ["# RD2 report — %s" % tag, "", "Generated %s by scripts/journal5/rd2_report.py. Instances %d; natural unit/basis errors %d; "
         "non-errors %d. Wilson 95%% CI; drug-cluster bootstrap in parentheses." % (rep["generated"], len(rows), len(err), len(non)), "",
         "## P1 Paper checkers: PASS rate on natural unit/basis errors", "", "| checker | PASS on errors | PASS on non-errors | parse fails |",
         "|---|---|---|---|"]
    for k, d in p1.items():
        L.append("| %s | %s | %s | %s |" % (k, fmt(d.get("pass_on_errors")), fmt(d.get("pass_on_nonerrors")),
                                           d.get("parse_fail_on_errors", d.get("missing", ""))))
    L += ["", "## P2 Frozen basis check (fdb95de)", "", "| variant | recall (independent errors) | recall (all errors) | flag rate | flag rate on non-errors | PPV | false-alarm est. |", "|---|---|---|---|---|---|---|"]
    for v, d in p2.items():
        fa = d.get("false_alarm_rate_est") or {}
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (v, fmt(d["recall_independent_errors"]), fmt(d["recall_all_errors"]),
                                                          fmt(d["flag_rate_all"]), fmt(d["flag_rate_on_nonerrors"]), fmt(d.get("ppv")),
                                                          ("%s%%" % fa.get("pct")) if fa else "–"))
    L += ["", "## P3 Transfer", "", "| model | FAIL on errors | PASS on non-errors |", "|---|---|---|"]
    for k, d in p3.items():
        if k != "UNF":
            L.append("| %s | %s | %s |" % (k, fmt(d["fail_on_errors"]), fmt(d["pass_on_nonerrors"])))
    L += ["", "| checker x UNF | errors raw | errors UNF | non-errors raw | non-errors UNF |", "|---|---|---|---|---|"]
    for k, d in unf.items():
        a, b = ("fail_on_errors_raw", "fail_on_errors_unf") if k.startswith("FT ") else ("pass_on_errors_raw", "pass_on_errors_unf")
        L.append("| %s (%s) | %s | %s | %s | %s |" % (k, "FAIL" if k.startswith("FT ") else "PASS", fmt(d[a]), fmt(d[b]),
                                                     fmt(d["pass_on_nonerrors_raw"]), fmt(d["pass_on_nonerrors_unf"])))
    L += ["", "## S Local LLM judges (chain-3 path)", "", "| judge | PASS on errors | PASS on non-errors | parse fails |", "|---|---|---|---|"]
    for k, d in sj.items():
        L.append("| %s | %s | %s | %d |" % (k, fmt(d["pass_on_errors"]), fmt(d["pass_on_nonerrors"]), d["parse_fail_on_errors"]))
    out.with_suffix(".md").write_text("\n".join(L) + "\n")
    log("RD2_report", provisional=prov, n_err=len(err), n_nonerr=len(non), out=str(out.with_suffix(".md")))


if __name__ == "__main__":
    main()
