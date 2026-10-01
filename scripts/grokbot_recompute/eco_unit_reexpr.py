"""Count unit re-expressions (same amount, different unit) in T4 ecological answers (original 444 and current 438)."""
import json, re, sys, collections
from decimal import Decimal
from pathlib import Path
import subprocess, tempfile
ROOT = Path(__file__).resolve().parents[2]
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
MASS = {"mg": 1, "milligram": 1, "milligrams": 1, "g": 1000, "gram": 1000, "grams": 1000,
        "mcg": Decimal("0.001"), "µg": Decimal("0.001"), "μg": Decimal("0.001"), "ug": Decimal("0.001"),
        "microgram": Decimal("0.001"), "micrograms": Decimal("0.001"), "kg": 10**6}
VOL = {"ml": 1, "milliliter": 1, "milliliters": 1, "millilitre": 1, "millilitres": 1, "l": 1000, "liter": 1000, "liters": 1000, "litre": 1000, "litres": 1000, "cc": 1}
SURF = {"milligram": "mg", "milligrams": "mg", "gram": "g", "grams": "g", "mcg": "µg", "μg": "µg", "ug": "µg",
        "microgram": "µg", "micrograms": "µg", "milliliter": "ml", "milliliters": "ml", "millilitre": "ml", "millilitres": "ml",
        "liter": "l", "liters": "l", "litre": "l", "litres": "l", "cc": "ml"}
UNITS = sorted(list(MASS) + list(VOL), key=len, reverse=True)
RE = re.compile(rf"(?<![\w.])({NUM})\s*({'|'.join(map(re.escape, UNITS))})(?![a-zA-Z])((?:\s*(?:/|per)\s*(?:kg|m2|m²|min|minute|hour|hr|h|day|d|dose|week))*)", re.I)

def norm_suffix(s):
    s = re.sub(r"\s*per\s*", "/", s.lower()).replace(" ", "")
    s = s.replace("minute", "min").replace("hour", "h").replace("hr", "h").replace("m²", "m2")
    return s

def mentions(text):
    out = []
    for m in RE.finditer(text.replace("\u00a0", " ")):
        u = m.group(2).lower() if m.group(2) not in ("µg", "μg") else "µg"
        if u in MASS: fam, f = "mass", Decimal(str(MASS[u]))
        else: fam, f = "vol", Decimal(str(VOL[u]))
        val = Decimal(m.group(1).replace(",", "")) * f
        out.append(dict(fam=fam, canon=val.normalize(), unit=SURF.get(u, u), raw=m.group(0), suffix=norm_suffix(m.group(3))))
    return out

def classify(span, answer):
    t = mentions(span)
    if not t: return "target_unparsed", None
    t = t[-1]
    am = [a for a in mentions(answer) if a["fam"] == t["fam"]]
    same_amt = [a for a in am if a["canon"] == t["canon"]]
    if any(a["unit"] == t["unit"] for a in same_amt): return "same_unit", None
    if same_amt: return "unit_reexpressed", same_amt[0]["raw"]
    return "target_amount_absent", None

def run(path, label):
    rows = [json.loads(l) for l in open(path)]
    c = collections.Counter(); ex = []
    for r in rows:
        k, raw = classify(r["target_span_evidence"], r.get("answer") or "")
        c[k] += 1
        if k == "unit_reexpressed": ex.append((r["task_id"], r["answerer_id"], r["target_span_evidence"], raw))
    print(f"{label}: n={len(rows)}", dict(c))
    for e in ex: print("   re-expressed:", e)
    return c, ex

if __name__ == "__main__":
    # original 444-answer file = data/t4/eco_answers.jsonl at commit 4d7a46c (before the 2 non-dose bases were dropped)
    tmp = Path(tempfile.gettempdir()) / "eco_answers_444.jsonl"
    tmp.write_bytes(subprocess.check_output(["git", "show", "4d7a46c:data/t4/eco_answers.jsonl"], cwd=ROOT))
    run(str(tmp), "original eco run (commit 4d7a46c)")
    run(str(ROOT / "data/t4/eco_answers.jsonl"), "current cohort")
    # spelled-out surface variants (mg -> milligrams) are counted as same_unit (surface variant), not re-expression
