#!/usr/bin/env python3
"""(UNF-ADV-3) Report for the adversarial unit-spelling set (CPU, no models, no API).

(a) normalizer level (always): parse accuracy of UNF v1 (src/unit_norm_fix.py, the pre-specified fix, UNCHANGED)
    and of the POST-HOC v2 pre-pass (src/unit_norm_fix_v2.py, written after seeing v1's failures on this set ->
    optimistic), overall / by family / by label, plus the list of failing variants.
(b) checker level (when results/journal2/unf_adv/scores/ exist): per small checker and pack
    (orig = raw text, unf = v1, unf_v2 = post-hoc v2)
      QI = PASS rate on SUPPORTED variants (correct respelling/conversion)
      US = FAIL rate on UNSUPPORTED variants (wrong-unit swap)
    anchor-conditional (the base's own canonical claim must PASS in the same pack, like the card's C0 condition),
    with base-clustered bootstrap CIs and paired deltas vs orig; QI/US after v1 split by whether v1 parsed the
    variant.
Outputs: notes/unf_adversarial.md, results/journal2/unf_adv/report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "data/journal2/unf_adversarial.jsonl"
SCORES = ROOT / "results/journal2/unf_adv/scores"
OUTJ = ROOT / "results/journal2/unf_adv/report.json"
NOTE = ROOT / "notes/unf_adversarial.md"
CHECKERS = [("t6a_minicheck_roberta", "MiniCheck-RoBERTa"), ("t6a_minicheck_deberta", "MiniCheck-DeBERTa"),
            ("t6a_alignscore_base", "AlignScore-base"), ("v2a_minicheck", "MiniCheck-Flan-T5-Large"),
            ("v3_alignscore", "AlignScore-large")]
PACKS = [("orig", "raw text"), ("unf", "UNF v1 (pre-specified)"), ("unf_v2", "UNF v2 (POST-HOC)")]
SEED = 20261001


def read_jsonl(p: Path) -> list:
    if not Path(p).is_file():
        return []
    return [json.loads(l) for l in Path(p).open(encoding="utf-8") if l.strip()]


def verdicts(p: Path) -> dict:
    return {r["instance_id"]: r["verdict"] for r in read_jsonl(p) if r.get("verdict") in ("PASS", "FAIL")}


def boot_rate(rows: list, succ, n_boot: int, seed: int = SEED, paired_other=None) -> dict:
    """rows: (base_id, value 0/1) ; returns rate + base-clustered percentile CI. paired_other: second list -> delta."""
    by = defaultdict(lambda: [0, 0])
    for b, v in rows:
        by[b][0] += v
        by[b][1] += 1
    k = sum(a for a, _ in by.values())
    n = sum(c for _, c in by.values())
    out = {"k": k, "n": n, "rate": 100.0 * k / n if n else None, "ci": [None, None]}
    if n == 0 or len(by) < 2:
        return out
    bases = sorted(by)
    K = np.array([by[b][0] for b in bases], float)
    Nn = np.array([by[b][1] for b in bases], float)
    rng = np.random.default_rng(seed)
    W = rng.multinomial(len(bases), np.full(len(bases), 1.0 / len(bases)), size=n_boot)
    r = 100.0 * (W @ K) / np.maximum(W @ Nn, 1)
    out["ci"] = [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))]
    return out


def paired_delta(a: dict, b: dict, n_boot: int) -> dict:
    """a, b: base -> [k, n] for before / after on the same items; delta of pooled rates (pp) with paired base bootstrap."""
    bases = sorted(set(a) | set(b))
    if not bases:
        return {"delta": None, "ci": [None, None]}
    Ka = np.array([a.get(x, [0, 0])[0] for x in bases], float)
    Na = np.array([a.get(x, [0, 0])[1] for x in bases], float)
    Kb = np.array([b.get(x, [0, 0])[0] for x in bases], float)
    Nb = np.array([b.get(x, [0, 0])[1] for x in bases], float)
    d = 100.0 * (Kb.sum() / max(Nb.sum(), 1) - Ka.sum() / max(Na.sum(), 1))
    if len(bases) < 2:
        return {"delta": d, "ci": [None, None]}
    rng = np.random.default_rng(SEED + 1)
    W = rng.multinomial(len(bases), np.full(len(bases), 1.0 / len(bases)), size=n_boot)
    r = 100.0 * ((W @ Kb) / np.maximum(W @ Nb, 1) - (W @ Ka) / np.maximum(W @ Na, 1))
    return {"delta": d, "ci": [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))]}


def f(s: dict) -> str:
    if not s or s.get("rate") is None:
        return "NA"
    lo, hi = s["ci"]
    return "%.1f [%.1f, %.1f] (n=%d)" % (s["rate"], lo, hi, s["n"]) if lo is not None else "%.1f (n=%d)" % (s["rate"], s["n"])


def fd(d: dict) -> str:
    if d.get("delta") is None:
        return "NA"
    lo, hi = d["ci"]
    return "%+.1f [%+.1f, %+.1f]" % (d["delta"], lo, hi) if lo is not None else "%+.1f" % d["delta"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--scores", default=str(SCORES))
    ap.add_argument("--out-json", default=str(OUTJ))
    ap.add_argument("--out-md", default=str(NOTE))
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args()
    rows = read_jsonl(Path(args.data))
    if not rows:
        raise SystemExit("no adversarial data (run scripts/journal2/unf_adv_build.py)")
    test = [r for r in rows if r["family"] != "anchor"]
    anchors = {r["base_id"]: r for r in rows if r["family"] == "anchor"}
    res = {"generated_by": "scripts/journal2/unf_adv_report.py", "data": str(Path(args.data).name), "n_items": len(test),
           "n_bases": len(anchors), "by_label": dict(Counter(r["label"] for r in test)), "normalizer": {}, "checkers": {}}
    # ---------- (a) normalizer level
    fams = sorted({r["family"] for r in test})
    for v in ("v1", "v2"):
        d = {"overall": boot_rate([(r["base_id"], int(r[v + "_parse_ok"])) for r in test], None, args.boot),
             "pair_level_overall": boot_rate([(r["base_id"], int(r[v + "_pair_ok"])) for r in test], None, args.boot),
             "by_label": {l: boot_rate([(r["base_id"], int(r[v + "_parse_ok"])) for r in test if r["label"] == l], None, args.boot)
                          for l in ("SUPPORTED", "UNSUPPORTED")},
             "by_family": {fa: {"k": sum(r[v + "_parse_ok"] for r in test if r["family"] == fa),
                                "n": sum(1 for r in test if r["family"] == fa)} for fa in fams},
             "failures": [{"id": r["instance_id"], "family": r["family"], "variant": r["variant"], "label": r["label"],
                           "surface": r["surface"], "why": r[v + "_parse_why"]} for r in test if not r[v + "_parse_ok"]],
             "anchors_ok": sum(int(a[v + "_parse_ok"]) for a in anchors.values())}
        res["normalizer"][v] = d
    # ---------- (b) checker level
    sroot = Path(args.scores)
    for ck, name in CHECKERS:
        vd = {p: verdicts(sroot / p / (ck + ".jsonl")) for p, _ in PACKS}
        if not vd["orig"]:
            res["checkers"][name] = {"status": "not scored yet"}
            continue
        out = {"coverage": {p: "%d/%d" % (sum(1 for r in rows if r["instance_id"] in vd[p]), len(rows)) for p, _ in PACKS},
               "packs": {}, "deltas": {}}
        per = {}
        for p, _ in PACKS:
            if not vd[p]:
                continue
            ok_base = {b for b, a in anchors.items() if vd[p].get(a["instance_id"]) == "PASS"}
            m = {}
            for metric, lab, want in (("QI", "SUPPORTED", "PASS"), ("US", "UNSUPPORTED", "FAIL")):
                sel = [r for r in test if r["label"] == lab and r["instance_id"] in vd[p]]
                cond = [r for r in sel if r["base_id"] in ok_base]
                m[metric] = boot_rate([(r["base_id"], int(vd[p][r["instance_id"]] == want)) for r in cond], None, args.boot)
                m[metric + "_uncond"] = boot_rate([(r["base_id"], int(vd[p][r["instance_id"]] == want)) for r in sel], None, args.boot)
                if p != "orig":
                    v = "v1" if p == "unf" else "v2"
                    for flag in (True, False):
                        m["%s_%s_parse_%s" % (metric, v, "ok" if flag else "fail")] = boot_rate(
                            [(r["base_id"], int(vd[p][r["instance_id"]] == want)) for r in cond if bool(r[v + "_parse_ok"]) == flag],
                            None, args.boot)
                m[metric + "_by_family"] = {fa: [sum(int(vd[p][r["instance_id"]] == want) for r in cond if r["family"] == fa),
                                                 sum(1 for r in cond if r["family"] == fa)] for fa in fams}
                # per-base counts on the common anchor-PASS-in-orig set, for paired deltas
                okb0 = {b for b, a in anchors.items() if vd["orig"].get(a["instance_id"]) == "PASS"}
                cnt = defaultdict(lambda: [0, 0])
                for r in sel:
                    if r["base_id"] in okb0:
                        cnt[r["base_id"]][0] += int(vd[p][r["instance_id"]] == want)
                        cnt[r["base_id"]][1] += 1
                per[(p, metric)] = dict(cnt)
            m["anchor_pass"] = "%d/%d" % (len(ok_base), len(anchors))
            out["packs"][p] = m
        for p in ("unf", "unf_v2"):
            for metric in ("QI", "US"):
                if (p, metric) in per:
                    out["deltas"]["%s_%s" % (metric, p)] = paired_delta(per[("orig", metric)], per[(p, metric)], min(args.boot, 2000))
        res["checkers"][name] = out
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n")
    write_md(res, Path(args.out_md), fams)
    print(json.dumps({"wrote": [args.out_json, args.out_md], "v1_parse": res["normalizer"]["v1"]["overall"]["rate"],
                      "v2_parse_posthoc": res["normalizer"]["v2"]["overall"]["rate"],
                      "checkers": {k: ("scored" if "packs" in v else v["status"]) for k, v in res["checkers"].items()}}))


def write_md(res: dict, path: Path, fams: list) -> None:
    n1, n2 = res["normalizer"]["v1"], res["normalizer"]["v2"]
    L = ["# Adversarial unit-spelling test set for the unit-normalization fix (UNF)", "",
         "Generated by `scripts/journal2/unf_adv_report.py`. Data: `data/journal2/unf_adversarial.jsonl` (built by "
         "`scripts/journal2/unf_adv_build.py`): %d claims (%d SUPPORTED = correct respelling/conversion, %d UNSUPPORTED = "
         "wrong-unit swap) over %d evidence bases (UNF-cohort C0 bases + FDA-label excerpts for mg/m2, units, mg/kg/day "
         "and ranges), plus one canonical anchor claim per base." % (res["n_items"], res["by_label"].get("SUPPORTED", 0),
                                                                     res["by_label"].get("UNSUPPORTED", 0), res["n_bases"]), "",
         "**UNF v1** = `src/unit_norm_fix.py`, the pre-specified fix, run unchanged: its numbers are the honest robustness "
         "result. **UNF v2** = `src/unit_norm_fix_v2.py`, a surface pre-pass written AFTER seeing v1's failures on this "
         "very set (post-hoc, tuned on the test set, optimistic); reported separately and never used for the main results.", "",
         "## (a) Normalizer level: does it extract the gold canonical quantity?", "",
         "Correct = exactly one dose span inside the variant with the gold kind/basis/value (gold computed from the recipe, "
         "independently of the normalizer). Base-clustered 95%% CIs. Base claims (anchors) parse correctly: v1 %d/%d." % (
             n1["anchors_ok"], res["n_bases"]), "",
         "| normalizer | all variants | SUPPORTED | UNSUPPORTED | end-to-end pair outcome |", "|---|---|---|---|---|",
         "| UNF v1 (pre-specified) | %s | %s | %s | %s |" % (f(n1["overall"]), f(n1["by_label"]["SUPPORTED"]),
                                                              f(n1["by_label"]["UNSUPPORTED"]), f(n1["pair_level_overall"])),
         "| UNF v2 (POST-HOC) | %s | %s | %s | %s |" % (f(n2["overall"]), f(n2["by_label"]["SUPPORTED"]),
                                                         f(n2["by_label"]["UNSUPPORTED"]), f(n2["pair_level_overall"])), "",
         "Pair outcome: SUPPORTED -> the normalized claim contains the normalized evidence dose (surface identity); "
         "UNSUPPORTED -> the swap is parsed correctly and stays a numeral mismatch.", "",
         "| family | v1 | v2 (post-hoc) |", "|---|---|---|"]
    for fa in fams:
        a, b = n1["by_family"][fa], n2["by_family"][fa]
        L.append("| %s | %d/%d | %d/%d |" % (fa, a["k"], a["n"], b["k"], b["n"]))
    L += ["", "### v1 failing variants (S = SUPPORTED, U = UNSUPPORTED)", ""]
    byv = defaultdict(list)
    for x in n1["failures"]:
        byv[(x["family"], x["variant"])].append(x)
    for (fa, va), xs in sorted(byv.items()):
        L.append("- %s / `%s`: %s" % (fa, va, "; ".join("%s `%s` (%s)" % (x["label"][0], x["surface"].replace("\u00a0", "<nbsp>")
                                                                            .replace("\u2009", "<thin>").replace("\u202f", "<nnbsp>"),
                                                                            x["why"]) for x in xs)))
    L += ["", "### v2 (post-hoc) remaining failures", ""] + ["- %s `%s` (%s)" % (x["label"][0], x["surface"], x["why"]) for x in n2["failures"]]
    L += ["", "## (b) Checker level: QI / US before vs after normalization", ""]
    scored = {k: v for k, v in res["checkers"].items() if "packs" in v}
    if not scored:
        L += ["Not scored yet: run `sbatch jobs/journal2/jr2_UNFADV.sbatch` on the HPC "
              "(the last array task reruns this script).", ""]
    else:
        L += ["QI = PASS on SUPPORTED variants; US = FAIL on UNSUPPORTED variants; anchor-conditional (base's canonical "
              "claim PASSes in the same pack). Δ = pack − raw text in points, paired base-clustered bootstrap on bases whose "
              "anchor PASSes on raw text.", "",
              "| checker | metric | raw text | UNF v1 | Δ v1 | UNF v2 (post-hoc) | Δ v2 | v1, variants v1 parsed | v1, variants v1 failed |",
              "|---|---|---|---|---|---|---|---|---|"]
        for name, d in scored.items():
            P = d["packs"]
            for metric in ("QI", "US"):
                L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    name, metric, f(P.get("orig", {}).get(metric)), f(P.get("unf", {}).get(metric)),
                    fd(d["deltas"].get(metric + "_unf", {})), f(P.get("unf_v2", {}).get(metric)), fd(d["deltas"].get(metric + "_unf_v2", {})),
                    f(P.get("unf", {}).get(metric + "_v1_parse_ok")), f(P.get("unf", {}).get(metric + "_v1_parse_fail"))))
        L += ["", "Coverage / anchor PASS per pack: " + "; ".join("%s %s" % (n, {p: (d["coverage"][p], d["packs"].get(p, {}).get("anchor_pass"))
                                                                           for p in d["coverage"]}) for n, d in scored.items()), ""]
        L += ["### By family (UNF v1, anchor-conditional): QI | US", "", "| checker | " + " | ".join(fams) + " |", "|---|" + "---|" * len(fams)]
        for name, d in scored.items():
            P = d["packs"].get("unf")
            if not P:
                continue
            cells = []
            for fa in fams:
                q, u = P["QI_by_family"][fa], P["US_by_family"][fa]
                cells.append("%s / %s" % ("%d/%d" % tuple(q) if q[1] else "-", "%d/%d" % tuple(u) if u[1] else "-"))
            L.append("| %s | %s |" % (name, " | ".join(cells)))
        L.append("")
    L += ["## Caveats", "",
          "- Variants are synthetic surface rewrites inserted into real claims/evidence; frequencies do not reflect how often "
          "each spelling occurs in practice. RD-label bases use a template claim (\"The recommended dose of X is ...\").",
          "- v1's capital `G` exclusion is by design (protects \"G protein\"); plain-space thousands (`1 000`) are ambiguous "
          "(\"2 500 mg tablets\") and are left unparsed even by v2. Worse than a miss: v1 reads `1 000 mcg` as `000 mcg` = 0 and "
          "REWRITES it (\"Use 1 000 mcg daily.\" vs \"Give 1 mg IM.\" -> \"Use 1 0 mg daily.\"), i.e. a corrupting edit; same for "
          "thin/no-break-space thousands (v2 joins those).",
          "- UNF can only help where it parses; on unparsed variants the checker sees the raw text, so those rows show the "
          "checker's own (unit-blind) behaviour.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
