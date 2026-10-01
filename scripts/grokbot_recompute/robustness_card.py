"""Robustness of current Table-2 card cells (same loader/metrics as paper_numbers_final.section_card)."""
import json, sys
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path[:0] = [f"{ROOT}/scripts", f"{ROOT}/src", f"{ROOT}/analysis"]
import paper_numbers_final as pnf
from t15_card_report import T7, join_extra, join_rows, load_main_dose_instances, metrics_block
from verifier_labels import CANONICAL_VERIFIERS, verifier_display_name

inst = load_main_dose_instances()
under = {r["base_id"] for r in inst if r.get("c0_underspecified")}
KEYS = pnf.CARD_KEYS
out = {}
for slug in CANONICAL_VERIFIERS:
    v = pnf.card_verdicts(slug)
    full = join_rows(inst, v) + join_extra(inst, v, T7)
    m = metrics_block(full, set())
    if m["qi_all"].get("rate") is None:
        continue
    weak = [r for r in full if not r.get("weak_e1_contrast")]
    und = [r for r in full if r["base_id"] not in under]
    res = {}
    for name, blk in (("all", full), ("excl_weak", weak), ("excl_underspec", und)):
        mm = metrics_block(blk, set())
        res[name] = {k: (mm[k].get("rate"), mm[k].get("den")) for k in KEYS}
    out[verifier_display_name(slug)] = res
__import__("os").makedirs(f"{ROOT}/results/grokbot_recompute", exist_ok=True); json.dump(out, open(f"{ROOT}/results/grokbot_recompute/robustness_card.json", "w"), indent=1)
rows = []
for name, res in out.items():
    for k in KEYS:
        a, na = res["all"][k]
        for mode in ("excl_weak", "excl_underspec"):
            b, nb = res[mode][k]
            if a is None or b is None:
                continue
            rows.append((mode, abs(b - a) * 100, (b - a) * 100, name, k, a * 100, na, b * 100, nb))
print("configs:", len(out), "flagged weak rows in card:", sum(1 for r in inst if r.get("weak_e1_contrast")), "underspec bases:", len(under))
for mode in ("excl_weak", "excl_underspec"):
    sel = sorted([r for r in rows if r[0] == mode], key=lambda r: -r[1])
    print(f"\n{mode}: max |delta| = {sel[0][1]:.2f} pp; cells >3pp: {sum(1 for r in sel if r[1] > 3)} / {len(sel)}")
    for r in sel[:8]:
        print(f"  {r[3]:32s} {r[4]:12s} {r[5]:5.1f}% (n={r[6]}) -> {r[7]:5.1f}% (n={r[8]})  delta {r[2]:+.2f}")
