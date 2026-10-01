"""Median score drop C0 - condition (paired by base, C0-PASS bases) for MiniCheck variants."""
import sys, statistics, json
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path[:0] = [f"{ROOT}/scripts", f"{ROOT}/src", f"{ROOT}/analysis"]
import paper_numbers_final as pnf
from t15_card_report import load_main_dose_instances, join_rows
from verifier_labels import verifier_display_name
import build_cpu_prelim as bcp
from analyze import load_joined

out = {}
# (1) the original prelim computation (cpu_early cohort), rerun
try:
    joined = load_joined(bcp.INSTANCES, bcp.VERDICTS) if hasattr(bcp, "INSTANCES") else None
except Exception as e:
    joined = None; print("prelim load failed:", e)
if joined is not None:
    for ver in bcp.VERIFIERS:
        block = [r for r in joined if r["verifier"] == ver and r["type"] == "DOSE"]
        d = bcp.dose_paired_drops(block)
        out[f"prelim_cpu_early::{ver}"] = {k: (round(statistics.median(v), 4) if v else None, len(v)) for k, v in d.items()}

# (2) current main card cohort (110 bases), same pairing rule
inst = load_main_dose_instances()
for slug in ("t6a_minicheck_roberta", "t6a_minicheck_deberta", "v2a_minicheck", "v2b_bespoke"):
    v = pnf.card_verdicts(slug)
    rows = join_rows(inst, v)
    sc = pnf.t13.merged_score_rows(slug)
    by = {}
    for r in rows:
        s = (sc.get(r["instance_id"]) or {}).get("score")
        if not isinstance(s, (int, float)) or r.get("verdict") not in ("PASS", "FAIL"):
            continue
        slot = by.setdefault(r["base_id"], {})
        c, m = r["condition"], r.get("magnitude")
        if c == "C0": slot["c0"] = (float(s), r["verdict"])
        elif c == "INV-claim": slot["inv"] = float(s)
        elif c == "E1-claim" and m in ("x2", "x10"): slot["e1_" + m] = float(s)
    res = {}
    for cond_only in (True, False):
        d = {"inv": [], "e1_x2": [], "e1_x10": []}
        for slot in by.values():
            if "c0" not in slot or (cond_only and slot["c0"][1] != "PASS"):
                continue
            for k in d:
                if k in slot: d[k].append(slot["c0"][0] - slot[k])
        res["c0pass" if cond_only else "all"] = {k: (round(statistics.median(x), 4) if x else None, len(x)) for k, x in d.items()}
    out[f"main110::{verifier_display_name(slug)}"] = res
__import__("os").makedirs(f"{ROOT}/results/grokbot_recompute", exist_ok=True); json.dump(out, open(f"{ROOT}/results/grokbot_recompute/minicheck_drop.json", "w"), indent=1)
for k, v in out.items(): print(k, v)
