#!/usr/bin/env python3
"""(C4) Report for the second fine-tune -> notes/journal_second_finetune.md (+ JSON).

For AlignScore-large and MiniCheck-Flan-T5 (base and ANLI ratios 0.5 / 1 / 2):
  * main DOSE card (paper definitions, scripts/t15_card_report.metrics_block; C0-conditional,
    base-clustered bootstrap): C0, QI_all, QI_nat, NS, US_claim_up, US_evid_up
  * LLM-AggreFact macro BAcc (stratified n=3000 subsample; same function as T15) + item bootstrap CI
  * out-of-template real RAG: T24b cells and the new journal RAG pack cells (C0-conditional)
Reference row: the published MiniCheck-RoBERTa T15 fine-tune (notes/t15_card.json) when present.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jr_common import FT_DIR, NOTES, ROOT, read_jsonl  # noqa: E402

from t15_card_report import T7, aggrefact_bacc, join_extra, join_rows, load_main_dose_instances, metrics_block  # noqa: E402
from jr_rag_report import boot, cell  # noqa: E402

MODELS = ("alignscore_large", "minicheck_ft5")
TAGS = ("base", "r0.5", "r1", "r2")
KEYS = ("c0_pass_rate", "qi_all", "qi_nat", "ns", "us_claim_up", "us_evid_up")
T24B_CELLS = [("T24b C0 PASS", "T24b-C0", "PASS", False), ("unit-up FAIL given C0", "T24b-unit-up", "FAIL", True),
              ("unit-down FAIL given C0", "T24b-unit-down", "FAIL", True), ("value×10 FAIL given C0", "T24b-value-x10", "FAIL", True)]
RAG_CELLS = [("RAG C0 PASS", "RAG-C0", "PASS", False), ("conv PASS given C0", "RAG-conv", "PASS", True),
             ("value×2 FAIL given C0", "RAG-value-x2", "FAIL", True), ("unit-up FAIL given C0", "RAG-unit-up", "FAIL", True)]


def verdicts(name: str, pack: str):
    return {r["instance_id"]: r["verdict"] for r in read_jsonl(FT_DIR / "scores" / ("%s__%s.jsonl" % (name, pack)))
            if r.get("verdict") in ("PASS", "FAIL")}


def pct(st):
    if not st or st.get("rate") is None:
        return "NA"
    if st.get("lo") is None:
        return "%.1f" % (100 * st["rate"])
    return "%.1f [%.1f, %.1f]" % (100 * st["rate"], 100 * st["lo"], 100 * st["hi"])


def agg_bacc_ci(v, labels, by_ds, B=1000, seed=42):
    common = set(labels) & set(v)
    if not common:
        return None
    pt = aggrefact_bacc({i: {"verdict": v[i]} for i in common}, labels, by_ds, common)
    rng = random.Random(seed)
    per_ds = {ds: [i for i in ids if i in common] for ds, ids in by_ds.items()}
    st = []
    for _ in range(B):
        bacc = []
        for ds, ids in per_ds.items():
            if not ids:
                continue
            s = [ids[rng.randrange(len(ids))] for _ in ids]
            pos = [i for i in s if labels[i] == 1]
            neg = [i for i in s if labels[i] == 0]
            if not pos or not neg:
                continue
            tpr = sum(v[i] == "PASS" for i in pos) / len(pos)
            tnr = sum(v[i] == "FAIL" for i in neg) / len(neg)
            bacc.append((tpr + tnr) / 2)
        if bacc:
            st.append(sum(bacc) / len(bacc))
    st.sort()
    return {"macro_bacc": pt["macro_bacc"], "lo": st[int(0.025 * (len(st) - 1))], "hi": st[int(0.975 * (len(st) - 1))], "n": pt["n"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-md", default=str(NOTES / "journal_second_finetune.md"))
    args = ap.parse_args()
    inst = load_main_dose_instances()
    agg_rows = read_jsonl(ROOT / "data/t8/aggrefact/test.jsonl")
    labels, by_ds = {}, defaultdict(list)
    for r in agg_rows:
        iid = str(r.get("instance_id") or r.get("contamination_identifier") or r.get("id"))
        labels[iid] = int(r["label"])
        by_ds[r.get("dataset", "?")].append(iid)
    # T24b report excludes two threshold-dose questions from all cells (notes/t24b_report.md)
    t24b = [r for r in read_jsonl(ROOT / "data/t24/instances_t24b.jsonl") if r.get("question_id") not in ("T24_037", "T24_066")]
    for r in t24b:
        r.setdefault("question_id", r.get("question_id") or r["base_id"])
    rag = read_jsonl(ROOT / "data/journal/instances_rag.jsonl")
    res = {}
    md = ["# Second fine-tune: AlignScore-large and MiniCheck-Flan-T5 (journal revision)", "",
          "Same recipe as the published MiniCheck-RoBERTa fine-tune (`scripts/t15_train.py`: 3 epochs, lr 2e-5, "
          "batch 8, max_len 512, seed 42, best dev loss, threshold 0.5) on the T15 dose pairs mixed with ANLI at "
          "n_ANLI/n_dose = 0.5 / 1 / 2 (`results/journal/ft/data_manifest.json`). Library inference paths as in the paper.", "",
          "## Main DOSE card (C0-conditional; 95% base-clustered bootstrap CI)", "",
          "| model | " + " | ".join(KEYS) + " |", "|---|" + "---|" * len(KEYS)]
    ref = NOTES / "t15_card.json"
    for m in MODELS:
        for t in TAGS:
            name = "%s_%s" % (m, t)
            v = verdicts(name, "main_dose")
            v.update(verdicts(name, "t7"))
            if not v:
                continue
            mb = metrics_block(join_rows(inst, v) + join_extra(inst, v, T7), set())
            res.setdefault(name, {})["card"] = {k: {kk: mb[k].get(kk) for kk in ("rate", "lo", "hi", "den")} for k in KEYS}
            md.append("| %s | %s |" % (name, " | ".join(pct(mb[k]) for k in KEYS)))
    if ref.is_file():
        md += ["", "Reference (published MiniCheck-RoBERTa base vs ft): see `notes/t15_report.md` / `notes/t15_card.json`."]
    md += ["", "## LLM-AggreFact (macro BAcc over datasets; stratified n=3000, seed 42; item bootstrap CI)", "",
           "| model | macro BAcc [95% CI] | n |", "|---|---|---|"]
    for m in MODELS:
        for t in TAGS:
            name = "%s_%s" % (m, t)
            r = agg_bacc_ci(verdicts(name, "aggrefact"), labels, by_ds) if labels else None
            if r:
                res.setdefault(name, {})["aggrefact"] = r
                md.append("| %s | %.4f [%.4f, %.4f] | %d |" % (name, r["macro_bacc"], r["lo"], r["hi"], r["n"]))
    for title, rows, cells, pack in (("Out-of-template real RAG: T24b", t24b, T24B_CELLS, "t24b"),
                                     ("Out-of-template real RAG: journal RAG pack", rag, RAG_CELLS, "rag")):
        md += ["", "## %s (C0-conditional; bootstrap over questions)" % title, "",
               "| model | " + " | ".join(c[0] for c in cells) + " |", "|---|" + "---|" * len(cells)]
        if not rows:
            md.append("| (pack missing) |" + " |" * len(cells))
            continue
        for m in MODELS:
            for t in TAGS:
                name = "%s_%s" % (m, t)
                v = verdicts(name, pack)
                if not v:
                    continue
                cs = [boot(cell(rows, v, c, w, cond), 1000) for _, c, w, cond in cells]
                res.setdefault(name, {})[pack] = {cells[i][0]: cs[i] for i in range(len(cells))}
                md.append("| %s | %s |" % (name, " | ".join(
                    "NA" if c[0] is None else ("%.1f%% (n=%d)" % (100 * c[0], c[3])) for c in cs)))
    hist = sorted(FT_DIR.glob("train_*.json"))
    if hist:
        md += ["", "## Training runs", "", "| run | best dev loss | epochs (dev loss) | n_train |", "|---|---|---|---|"]
        for p in hist:
            h = json.loads(p.read_text())
            md.append("| %s | %.4f | %s | %d |" % (p.stem, h["best_dev_loss"], ", ".join("%.4f" % e["dev_loss"] for e in h["history"]), h["n_train"]))
    Path(args.out_md).write_text("\n".join(md) + "\n", encoding="utf-8")
    FT_DIR.mkdir(parents=True, exist_ok=True)
    (FT_DIR / "report.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
