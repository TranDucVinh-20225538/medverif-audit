import sys, json, collections
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path[:0] = [f"{ROOT}/scripts", f"{ROOT}/src", f"{ROOT}/analysis"]
import e2_t7_comparison_report as e2
from analyze import read_jsonl, _parsed
import paper_numbers_final as pnf
from t15_card_report import load_main_dose_instances, join_rows
from verifier_labels import CANONICAL_VERIFIERS, verifier_display_name

main = {r["instance_id"]: r for r in read_jsonl(e2.MAIN) if r.get("valid", True)}
exp = {r["instance_id"]: r for r in read_jsonl(e2.EXPAND) if r.get("valid", True)}
print("id overlap main/expand:", len(set(main) & set(exp)))
# Audit the old n=316 for v1_medscore
for slug in ("v1_medscore", "v2a_minicheck", "v3_alignscore", "v4_ragas_nli"):
    sc = e2.merged_scores(slug)
    inst_map = {**exp, **main}
    joined = e2.join(inst_map, sc, slug)
    c0 = e2._c0_pass_bases(joined)
    e2rows = [r for r in joined if r["condition"] == "E2" and r["base_id"] in c0 and _parsed(r)]
    src = collections.Counter("main" if r["instance_id"] in main else "expand" for r in e2rows)
    key = collections.Counter((r["claim"], r["evidence"]) for r in e2rows)
    dups = sum(c - 1 for c in key.values() if c > 1)
    bases = collections.Counter(r["base_id"] for r in e2rows)
    print(slug, "n", len(e2rows), "PASS", sum(r["verdict"] == "PASS" for r in e2rows), "by cohort", dict(src),
          "dup (claim,evidence) pairs", dups, "bases", len(bases), "max rows/base", max(bases.values()))
# Current main card cohort: E2 PASS | C0 PASS (card verdicts)
inst = load_main_dose_instances()
out = {}
for slug in CANONICAL_VERIFIERS:
    v = pnf.card_verdicts(slug)
    rows = join_rows(inst, v)
    c0p = {r["base_id"] for r in rows if r["condition"] == "C0" and r["verdict"] == "PASS"}
    e = [r for r in rows if r["condition"] == "E2" and r["verdict"] in ("PASS", "FAIL")]
    ec = [r for r in e if r["base_id"] in c0p]
    if not e: continue
    out[verifier_display_name(slug)] = dict(
        cond_pass=sum(r["verdict"] == "PASS" for r in ec), cond_n=len(ec),
        all_pass=sum(r["verdict"] == "PASS" for r in e), all_n=len(e))
for k, d in out.items():
    cr = d["cond_pass"]/d["cond_n"] if d["cond_n"] else float("nan")
    print(f"{k:32s} E2|C0 {d['cond_pass']}/{d['cond_n']} = {cr:.1%}   all {d['all_pass']}/{d['all_n']}")
__import__("os").makedirs(f"{ROOT}/results/grokbot_recompute", exist_ok=True); json.dump(out, open(f"{ROOT}/results/grokbot_recompute/e2_main110.json", "w"), indent=1)
