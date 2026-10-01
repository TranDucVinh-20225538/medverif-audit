#!/usr/bin/env python3
"""(J4-BC eval) Evaluate the FROZEN dose-basis check (scripts/journal4/basis_check.py, commit fdb95de) on the RD set.

Run AFTER the freeze commit; does not modify the rule.  CPU only, no model calls.  Python >= 3.8, stdlib only
(imports scripts/journal3/j3_common.verdict_map and scripts/journal4/frontier_judges_rd.vmaps_from_rows so verdicts are
read exactly as in the journal-3/4 reports: stored verdict / score > 0.5 for non-generative checkers, strict paper parser
for RAGAS-style LLM judges).

Outputs (results/journal4/basis_check/):
  per_item.jsonl                 one row per RD answer (1451): statuses / flag types for both variants + per-dose detail
  flagged_outside_flagged47.csv  every answer flagged (full variant) that is NOT one of the 47 auto unit-type rows,
                                 with snippets for human review (false alarm vs missed error)
  report.json / report.md        (a) recall on true12 / flagged47 (DEV set), (b) flag rates (false-alarm proxy),
                                 (c) abstain rates, (d) combined pipeline "checker PASS AND basis check not flagged"
Usage: python scripts/journal4/basis_check_eval.py
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts" / "journal3"))
import basis_check as B  # noqa: E402
from j3_common import read_jsonl, verdict_map  # noqa: E402
from frontier_judges_rd import vmaps_from_rows  # noqa: E402

RD = ROOT / "results" / "journal2" / "real_dose" / "instances.jsonl"
PRE = ROOT / "qc" / "ai_precheck_real_dose_unit_errors.csv"
OUT = ROOT / "results" / "journal4" / "basis_check"
FREEZE_COMMIT = "fdb95de68b376340946f2e251040d3006c20072e"
TZ7 = dt.timezone(dt.timedelta(hours=7))
VARIANTS = ("full", "strict")

CHECKERS = OrderedDict()  # name -> (path, kind)  kind: "verdict" (stored verdict / score>0.5) | "judge" (strict parse)
for nm, f, k in (("MiniCheck-RoBERTa", "t6_minicheck_roberta.jsonl", "verdict"),
                 ("MiniCheck-DeBERTa", "t6_minicheck_deberta.jsonl", "verdict"),
                 ("AlignScore-base", "t6_alignscore_base.jsonl", "verdict"),
                 ("MiniCheck-Flan-T5-Large", "v2a_minicheck.jsonl", "verdict"),
                 ("AlignScore-large", "v3_alignscore.jsonl", "verdict"),
                 ("Llama-3.3-70B RAGAS", "v4_ragas_nli.jsonl", "judge"),
                 ("MedScore (Mistral-Small-24B)", "v1_medscore.jsonl", "verdict")):
    CHECKERS[nm] = (ROOT / "results/journal2/real_dose/scores" / f, k, "journal2 paper checkers")
for p in sorted((ROOT / "results/journal3/ft/scores").glob("*__rd_raw.jsonl")):
    CHECKERS["FT %s" % p.name.split("__")[0]] = (p, "verdict", "journal3 FT on real doses")
for p in sorted((ROOT / "results/journal3/judges/scores").glob("*__rd.jsonl")):
    CHECKERS["judge %s" % p.name.split("__")[0]] = (p, "judge", "journal3 small local LLM judges")
for p in sorted((ROOT / "results/journal4/frontier").glob("*.jsonl")):
    if "__" not in p.name:
        CHECKERS["frontier %s" % p.stem] = (p, "judge", "journal4 frontier (subset only)")


def wilson(k: int, n: int):
    if n == 0:
        return None, None
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, round(100 * (c - h), 1)), min(100.0, round(100 * (c + h), 1))


def rate(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "pct": round(100.0 * k / n, 1) if n else None, "ci95": [lo, hi]}


def fmt(r: dict) -> str:
    if not r["n"]:
        return "–"
    return "%d/%d = %.1f%% [%s, %s]" % (r["k"], r["n"], r["pct"], r["ci95"][0], r["ci95"][1])


def window(text: str, needle: str, w: int = 110) -> str:
    i = text.find(needle) if needle else -1
    if i < 0:
        return ""
    a, b = max(0, i - w), min(len(text), i + len(needle) + w)
    return ("…" if a else "") + text[a:i] + "«" + needle + "»" + text[i + len(needle):b] + ("…" if b < len(text) else "")


def git(*a) -> str:
    try:
        return subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def main() -> None:
    rule_sha = hashlib.sha256((HERE / "basis_check.py").read_bytes()).hexdigest()
    rule_changed = git("diff", "--name-only", FREEZE_COMMIT, "--", "scripts/journal4/basis_check.py")
    if rule_changed:
        raise SystemExit("basis_check.py differs from the freeze commit %s -- refusing to evaluate" % FREEZE_COMMIT)
    rows = read_jsonl(RD)
    with PRE.open(encoding="utf-8") as fh:
        pre = {r["instance_id"]: r for r in csv.DictReader(l for l in fh if not l.startswith("#"))}
    unit = ("unit_error", "basis_error")
    S = OrderedDict()
    S["all"] = [r["instance_id"] for r in rows]
    S["flagged47"] = [r["instance_id"] for r in rows if r["auto_class"] in unit]
    S["true12"] = [r["instance_id"] for r in rows if (pre.get(r["instance_id"]) or {}).get("ai_label") == "true_unit_error"]
    S["non_flagged47"] = [r["instance_id"] for r in rows if r["auto_class"] not in unit]
    S["auto_correct"] = [r["instance_id"] for r in rows if r["auto_class"] == "correct"]
    for ac in ("match_other_context", "value_error", "time_ambiguous", "unverifiable"):
        S["auto_" + ac] = [r["instance_id"] for r in rows if r["auto_class"] == ac]
    for lab in ("parser_artifact_answer_correct", "different_indication_or_population", "value_error_misclassified", "ambiguous"):
        S["precheck_" + lab] = [i for i, p in pre.items() if p["ai_label"] == lab]
    assert len(S["all"]) == 1451 and len(S["flagged47"]) == 47 and len(S["true12"]) == 12, {k: len(v) for k, v in S.items()}

    OUT.mkdir(parents=True, exist_ok=True)
    res, by = {}, {r["instance_id"]: r for r in rows}
    with (OUT / "per_item.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            x = B.check_pair(r["claim"], r["evidence"])
            res[r["instance_id"]] = x
            fh.write(json.dumps(OrderedDict([
                ("instance_id", r["instance_id"]), ("drug", r["drug"]), ("generator", r["generator"]),
                ("answer_condition", r["answer_condition"]), ("auto_class", r["auto_class"]),
                ("ai_label", (pre.get(r["instance_id"]) or {}).get("ai_label", "")),
                ("status_full", x["status_full"]), ("flag_type_full", x["flag_type_full"]),
                ("status_strict", x["status_strict"]), ("flag_type_strict", x["flag_type_strict"]),
                ("n_answer_doses", x["n_answer_doses"]), ("n_evidence_doses", x["n_evidence_doses"]),
                ("doses", x["doses"]), ("rule_version", x["rule_version"])]), ensure_ascii=False) + "\n")

    rep = OrderedDict(generated=dt.datetime.now(TZ7).strftime("%Y-%m-%dT%H:%M:%S%z"), rule_version=B.RULE_VERSION,
                      freeze_commit=FREEZE_COMMIT, rule_sha256=rule_sha, rd_file=str(RD.relative_to(ROOT)),
                      subset_sizes={k: len(v) for k, v in S.items()}, status={}, flag_types={})
    for v in VARIANTS:
        rep["status"][v] = OrderedDict()
        rep["flag_types"][v] = OrderedDict()
        for k, ids in S.items():
            c = Counter(res[i]["status_" + v] for i in ids)
            n = len(ids)
            rep["status"][v][k] = OrderedDict((s, rate(c.get(s, 0), n)) for s in ("flag", "pass", "abstain", "no_dose"))
            rep["flag_types"][v][k] = dict(Counter(res[i]["flag_type_" + v] for i in ids if res[i]["flag_" + v]))

    # per-case table, true12
    rep["true12_cases"] = []
    for i in sorted(S["true12"], key=lambda i: pre[i]["check_id"]):
        p, x = pre[i], res[i]
        rep["true12_cases"].append(OrderedDict(check_id=p["check_id"], instance_id=i, drug=p["drug"], mechanism=p["ai_mechanism"],
                                               label_dose=p["label_dose_auto"], answer_dose=p["answer_dose_auto"],
                                               full=x["flag_type_full"] or x["status_full"],
                                               strict=x["flag_type_strict"] or x["status_strict"]))

    # flagged items outside flagged47 (full variant), for human review
    def evid_conflict(d):
        return d.get("r1_flag_evidence") or (", ".join(d["r2_comparable"][:4]) if d.get("r2_flag") else "")
    fl = []
    for i in S["non_flagged47"]:
        x = res[i]
        if not x["flag_full"]:
            continue
        r = by[i]
        ds = [d for d in x["doses"] if d["r1_flag"] or d["r2_flag"]]
        d0 = sorted(ds, key=lambda d: 0 if d["r1_flag"] else 1)[0]
        et = B.extract_doses(r["evidence"])[0]
        ev_need = d0.get("r1_flag_evidence") or (d0["r2_comparable"][0] if d0["r2_comparable"] else "")
        fl.append(OrderedDict(
            instance_id=i, drug=r["drug"], generator=r["generator"], answer_condition=r["answer_condition"],
            auto_class=r["auto_class"], flag_type_full=x["flag_type_full"], flag_type_strict=x["flag_type_strict"],
            rule="R1" if d0["r1_flag"] else "R2", answer_dose=d0["answer_dose"]["text"], evidence_doses=evid_conflict(d0),
            auto_label_dose=r.get("evidence_span") or "", answer=r["claim"][:400],
            evidence_context=window(et, ev_need)))
    order = {"correct": 0, "time_ambiguous": 1, "value_error": 2, "match_other_context": 3, "unverifiable": 4}
    fl.sort(key=lambda d: (order.get(d["auto_class"], 9), 0 if d["rule"] == "R1" else 1, d["drug"], d["instance_id"]))
    with (OUT / "flagged_outside_flagged47.csv").open("w", newline="", encoding="utf-8") as fh:
        cols = list(fl[0].keys()) + ["human_judgment (false_alarm / real_error / unclear)", "note"] if fl else ["instance_id"]
        w = csv.writer(fh)
        w.writerow(cols)
        for d in fl:
            w.writerow(list(d.values()) + ["", ""])
    rep["flagged_outside_flagged47"] = {"n": len(fl), "by_auto_class": dict(Counter(d["auto_class"] for d in fl)),
                                        "by_rule": dict(Counter(d["rule"] for d in fl)),
                                        "by_flag_type": dict(Counter(d["flag_type_full"] for d in fl))}

    # combined pipeline: checker PASS AND basis-check not flagged
    comb = OrderedDict()
    for nm, (p, kind, grp) in CHECKERS.items():
        if not p.is_file():
            continue
        vm = verdict_map(p) if kind == "verdict" else vmaps_from_rows(read_jsonl(p))[0]
        e = OrderedDict(group=grp, file=str(p.relative_to(ROOT)), verdict_rule="stored verdict / score > 0.5" if kind == "verdict"
                        else "strict paper parser (PARSE_FAIL = not PASS)")
        for k in ("true12", "flagged47", "auto_correct", "non_flagged47"):
            ids = [i for i in S[k] if i in vm]
            if not ids:
                continue
            row = OrderedDict(scored=len(ids), of=len(S[k]),
                              parse_fail=sum(1 for i in ids if vm[i] == "PARSE_FAIL"))
            for v in VARIANTS:
                row["checker_pass"] = rate(sum(1 for i in ids if vm[i] == "PASS"), len(ids))
                row["combined_pass_" + v] = rate(sum(1 for i in ids if vm[i] == "PASS" and not res[i]["flag_" + v]), len(ids))
            if k == "true12":
                row["slipped_checker"] = sorted(by[i]["drug"] for i in ids if vm[i] == "PASS")
                row["slipped_combined_full"] = sorted(by[i]["drug"] for i in ids if vm[i] == "PASS" and not res[i]["flag_full"])
                row["slipped_combined_strict"] = sorted(by[i]["drug"] for i in ids if vm[i] == "PASS" and not res[i]["flag_strict"])
            e[k] = row
        comb[nm] = e
    rep["combined"] = comb
    (OUT / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- markdown
    st = rep["status"]
    L = ["# Journal 4: dose-basis check — evaluation", "",
         "Rule `%s` frozen at commit `%s` (sha256 of `scripts/journal4/basis_check.py` = `%s`, unchanged since the freeze). "
         "Generated %s by `scripts/journal4/basis_check_eval.py` (CPU, deterministic, no model calls). Inputs: answer (`claim`) "
         "and label excerpt (`evidence`) of `%s` only. Percentages with Wilson 95%% CIs (rows, not drug-clustered)."
         % (B.RULE_VERSION, FREEZE_COMMIT[:7], rule_sha[:12], rep["generated"], rep["rd_file"]), "",
         "**Caveats.** `true12` = AI-precheck `true_unit_error` labels (LLM, not human-verified); `flagged47` = auto "
         "unit_error + basis_error rows from `rd_extract.py`. Both are the **DEV set**: the rule was designed after reading them, "
         "so recall there is optimistic by construction. `non_flagged47` (1404) is only *presumably* correct: it also contains "
         "the auto value errors, other-context matches, time-ambiguous and unverifiable answers, and any unit errors the auto "
         "extractor missed — a flag there is a false-alarm **proxy**, not a confirmed false alarm. `auto_correct` (1062) = "
         "answers whose first dose matched the label target sentence (cleanest negative proxy).", "",
         "Variants: **full** = R1 (same-numeral pairs) + R2 (unpaired basis neighbourhood), primary; **strict** = R1 only.", "",
         "## (a) Recall on the DEV set", "", "| subset | full: flagged | strict: flagged |", "|---|---|---|"]
    for k in ("true12", "flagged47", "precheck_parser_artifact_answer_correct", "precheck_different_indication_or_population",
              "precheck_value_error_misclassified", "precheck_ambiguous"):
        L.append("| %s%s | %s | %s |" % (k, " (DEV)" if k in ("true12", "flagged47") else " (DEV, not errors)" if "artifact" in k else
                                         " (DEV)", fmt(st["full"][k]["flag"]), fmt(st["strict"][k]["flag"])))
    L += ["", "Per case (true12):", "", "| check | drug | mechanism (AI) | label dose | answer dose | full | strict |", "|---|---|---|---|---|---|---|"]
    for c in rep["true12_cases"]:
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (c["check_id"], c["drug"], c["mechanism"], c["label_dose"], c["answer_dose"],
                                                        c["full"], c["strict"]))
    L += ["", "## (b) Flag rate (false-alarm proxy) and (c) abstain rate", "",
          "| subset | n | full: flag | full: abstain | full: no_dose | strict: flag | strict: abstain |", "|---|---|---|---|---|---|---|"]
    for k in ("all", "non_flagged47", "auto_correct", "auto_match_other_context", "auto_value_error", "auto_time_ambiguous",
              "auto_unverifiable", "flagged47", "true12"):
        L.append("| %s | %d | %s | %s | %s | %s | %s |" % (k, len(S[k]), fmt(st["full"][k]["flag"]), fmt(st["full"][k]["abstain"]),
                                                       fmt(st["full"][k]["no_dose"]), fmt(st["strict"][k]["flag"]),
                                                       fmt(st["strict"][k]["abstain"])))
    L += ["", "Flag types (full): " + "; ".join("%s: %s" % (k, json.dumps(rep["flag_types"]["full"][k])) for k in
                                               ("non_flagged47", "auto_correct", "flagged47")), "",
          "## Flagged answers outside flagged47 (for human review)", "",
          "%d answers (by auto class %s; by rule %s). Full list with snippets: `flagged_outside_flagged47.csv` (columns for a "
          "human judgment). First 20 below, sorted auto_correct first, then R1 before R2." % (
              len(fl), json.dumps(rep["flagged_outside_flagged47"]["by_auto_class"]), json.dumps(rep["flagged_outside_flagged47"]["by_rule"])),
          "", "| # | drug / gen / mode | auto class | flag | answer dose | evidence dose(s) | answer (trunc.) | evidence context |",
          "|---|---|---|---|---|---|---|---|"]
    esc = lambda s: (s or "").replace("|", "\\|").replace("\n", " ")  # noqa: E731
    for n, d in enumerate(fl[:20], 1):
        L.append("| %d | %s / %s / %s | %s | %s (%s) | %s | %s | %s | %s |" % (
            n, d["drug"], d["generator"], d["answer_condition"], d["auto_class"], d["flag_type_full"], d["rule"], esc(d["answer_dose"]),
            esc(d["evidence_doses"]), esc(d["answer"][:220]), esc(d["evidence_context"][:260])))
    L += ["", "## (d) Combined pipeline: checker PASS AND basis check not flagged", "",
          "Cells = PASS rate of the checker alone -> PASS rate of the combination (`checker PASS` and `not flagged`). On error subsets "
          "PASS = the error slips through (lower is better); on auto_correct PASS = correct answer accepted (higher is better; the "
          "drop is the cost of the basis check). flagged47 is NOT all errors (the precheck calls 12 of them parser artifacts with correct "
          "answers and 14 another population/indication), so its column is descriptive only. Frontier judges were only run on the "
          "true12/flagged47/smoke rows. The true12 columns are DEV-set numbers (the rule flags all 12 by construction).", "",
          "| checker | true12 slip: checker -> +full (+strict) | flagged47 PASS: checker -> +full | auto_correct PASS: checker -> +full (+strict) | true12 still slipping (full) |",
          "|---|---|---|---|---|"]
    for nm, e in comb.items():
        def cell(k, both=False):
            if k not in e:
                return "–"
            r = e[k]
            s = "%d/%d -> %d/%d" % (r["checker_pass"]["k"], r["scored"], r["combined_pass_full"]["k"], r["scored"])
            if both:
                s += " (%d)" % r["combined_pass_strict"]["k"]
            if k == "auto_correct":
                s = "%.1f%% -> %.1f%% (%.1f%%)" % (r["checker_pass"]["pct"], r["combined_pass_full"]["pct"], r["combined_pass_strict"]["pct"])
            if r["parse_fail"]:
                s += " [%d parse-fail]" % r["parse_fail"]
            return s
        L.append("| %s | %s | %s | %s | %s |" % (nm, cell("true12", True), cell("flagged47"), cell("auto_correct"),
                                                 ", ".join(e.get("true12", {}).get("slipped_combined_full", [])) or "none"))
    (OUT / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({"true12_full": st["full"]["true12"]["flag"], "flagged47_full": st["full"]["flagged47"]["flag"],
                      "non_flagged47_full": st["full"]["non_flagged47"]["flag"], "auto_correct_full": st["full"]["auto_correct"]["flag"],
                      "abstain_all_full": st["full"]["all"]["abstain"], "outside_flagged": len(fl)}, indent=1))


if __name__ == "__main__":
    main()
