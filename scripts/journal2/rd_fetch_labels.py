#!/usr/bin/env python3
"""(RD-0, box: needs internet) Download a reproducible sample of FDA drug-label dosage sections.

Source: openFDA drug label endpoint (https://api.fda.gov/drug/label.json; SPL content from DailyMed,
public domain / CC0 per open.fda.gov/license).  One label per drug: the most recent (effective_time
desc) HUMAN PRESCRIPTION DRUG label whose openfda.generic_name matches the drug exactly and that has a
`dosage_and_administration` section with at least one parseable dose (value + unit).

Drug order (deterministic): drugs mentioned in the paper's DOSE bases first (main v3 + main_ext +
expand claims/evidence, matched against the lexicon below), then the remaining lexicon in listed
order, until --n drugs have a usable label.

Outputs (NEW files only):
  data/real_labels/labels.jsonl        one row per drug: drug, in_dose_bases, set_id, spl id, version,
                                       effective_time, openfda names/route/manufacturer, D&A text
                                       (truncated to --max-chars), dosage_forms_and_strengths text
  data/real_labels/manifest.json       query, counts, misses, retrieval time, sha256 of labels.jsonl
  data/real_labels/README.md           provenance + license
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from unit_norm_fix import find_spans  # noqa: E402

OUT = ROOT / "data/real_labels"
API = "https://api.fda.gov/drug/label.json"

# Common generic drugs (oral/parenteral, adult + pediatric use), fixed order. Not exhaustive.
LEXICON = """
acetaminophen acyclovir adalimumab albuterol alendronate allopurinol alprazolam amikacin amiodarone amitriptyline
amlodipine amoxicillin ampicillin anastrozole apixaban aripiprazole atenolol atorvastatin azathioprine azithromycin
baclofen benazepril bisoprolol bumetanide buprenorphine bupropion buspirone captopril carbamazepine carvedilol
cefazolin cefdinir cefepime cefixime ceftazidime ceftriaxone cefuroxime cephalexin cetirizine chlorthalidone
ciprofloxacin citalopram clarithromycin clindamycin clonazepam clonidine clopidogrel colchicine cyclophosphamide
cyclosporine dabigatran dapagliflozin daptomycin dexamethasone diazepam diclofenac digoxin diltiazem diphenhydramine
dobutamine donepezil dopamine doxycycline duloxetine empagliflozin enalapril enoxaparin epinephrine ertapenem
erythromycin escitalopram esomeprazole ethambutol famotidine fentanyl ferrous filgrastim finasteride fluconazole
fluoxetine fluticasone folic fosfomycin furosemide gabapentin gentamicin glimepiride glipizide glyburide haloperidol
heparin hydralazine hydrochlorothiazide hydrocodone hydrocortisone hydromorphone hydroxychloroquine ibuprofen imipenem
indomethacin insulin ipratropium irbesartan isoniazid isosorbide ivermectin ketamine ketorolac labetalol lamotrigine
lansoprazole letrozole levetiracetam levofloxacin levothyroxine lidocaine linezolid lisinopril lithium loperamide
loratadine lorazepam losartan magnesium meloxicam memantine meropenem metformin methadone methotrexate
methylprednisolone metoclopramide metoprolol metronidazole midazolam minocycline mirtazapine montelukast morphine
moxifloxacin mycophenolate naloxone naproxen nifedipine nitrofurantoin nitroglycerin norepinephrine nystatin
olanzapine omeprazole ondansetron oseltamivir oxcarbazepine oxycodone pantoprazole paroxetine penicillin phenobarbital
phenytoin pioglitazone piperacillin potassium pravastatin prednisolone prednisone pregabalin primaquine probenecid
prochlorperazine promethazine propofol propranolol propylthiouracil pyrazinamide quetiapine ramipril ranitidine
rifampin risperidone rivaroxaban rocuronium rosuvastatin sertraline sildenafil simvastatin sitagliptin sodium
spironolactone sucralfate sulfamethoxazole sumatriptan tacrolimus tamoxifen tamsulosin terbinafine testosterone
tetracycline theophylline tizanidine topiramate torsemide tramadol trazodone triamcinolone trimethoprim valacyclovir
valproate valsartan vancomycin venlafaxine verapamil voriconazole warfarin zolpidem abacavir acetazolamide
albendazole amphotericin atovaquone benznidazole cefotaxime chloroquine clotrimazole dapsone desmopressin
didanosine efavirenz emtricitabine entecavir ganciclovir lamivudine mebendazole mefloquine nevirapine praziquantel
pyrimethamine ribavirin ritonavir tenofovir zidovudine alteplase atropine calcium dantrolene dexmedetomidine esmolol
etomidate flumazenil glucagon labetalol mannitol neostigmine octreotide oxytocin phenylephrine succinylcholine
vasopressin vecuronium methyldopa terbutaline nicardipine clevidipine argatroban bivalirudin fondaparinux
""".split()
LEXICON = list(dict.fromkeys(LEXICON))  # de-dup, keep order


def dose_base_texts() -> str:
    texts = []
    for rel in ("data/v3/instances_main.jsonl", "data/main_ext/instances_main_ext.jsonl", "data/expand/instances_main.jsonl"):
        p = ROOT / rel
        if not p.is_file():
            continue
        for line in p.open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("type") == "DOSE" and r.get("condition") == "C0":
                texts.append((r.get("claim") or "") + " " + (r.get("evidence") or ""))
    return " ".join(texts).lower()


def get(url: str, tries: int = 4) -> dict | None:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "medverif-audit-journal2/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            time.sleep(2 * (i + 1))
        except Exception:  # noqa: BLE001
            time.sleep(2 * (i + 1))
    return None


def fetch(drug: str) -> dict | None:
    q = ('openfda.generic_name.exact:"%s" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG" '
         'AND _exists_:dosage_and_administration') % drug.upper()
    url = API + "?" + urllib.parse.urlencode({"search": q, "sort": "effective_time:desc", "limit": 1})
    data = get(url)
    if not data or not data.get("results"):  # generic_name may be a combination / salt form -> word match
        q2 = ('openfda.generic_name:"%s" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG" '
              'AND _exists_:dosage_and_administration') % drug
        data = get(API + "?" + urllib.parse.urlencode({"search": q2, "sort": "effective_time:desc", "limit": 1}))
        if not data or not data.get("results"):
            return None
        hit = data["results"][0]
        hit["_match"] = "word"
        return hit
    hit = data["results"][0]
    hit["_match"] = "exact"
    return hit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--max-chars", type=int, default=8000)
    ap.add_argument("--outdir", default=str(OUT))
    ap.add_argument("--sleep", type=float, default=0.3)
    args = ap.parse_args()
    outd = Path(args.outdir)
    outd.mkdir(parents=True, exist_ok=True)
    base_txt = dose_base_texts()
    in_bases = [d for d in LEXICON if re.search(r"\b%s\b" % re.escape(d), base_txt)]
    order = in_bases + [d for d in LEXICON if d not in in_bases]
    rows, misses = [], []
    for drug in order:
        if len(rows) >= args.n:
            break
        hit = fetch(drug)
        time.sleep(args.sleep)
        if not hit:
            misses.append({"drug": drug, "why": "no_label"})
            continue
        da = " ".join(hit.get("dosage_and_administration") or []).strip()
        if not find_spans(da):
            misses.append({"drug": drug, "why": "no_dose_span"})
            continue
        of = hit.get("openfda") or {}
        rows.append({
            "drug": drug, "in_dose_bases": drug in in_bases, "match": hit["_match"],
            "set_id": hit.get("set_id"), "spl_id": hit.get("id"), "version": hit.get("version"),
            "effective_time": hit.get("effective_time"),
            "generic_name": of.get("generic_name"), "brand_name": of.get("brand_name"), "route": of.get("route"),
            "manufacturer_name": of.get("manufacturer_name"), "product_type": of.get("product_type"),
            "dosage_and_administration": da[: args.max_chars], "da_truncated": len(da) > args.max_chars,
            "da_chars_full": len(da),
            "dosage_forms_and_strengths": " ".join(hit.get("dosage_forms_and_strengths") or [])[:1500],
            "dailymed_url": "https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=%s" % hit.get("set_id"),
        })
        print(json.dumps({"drug": drug, "ok": True, "n": len(rows), "eff": hit.get("effective_time")}), flush=True)
    lab = outd / "labels.jsonl"
    with lab.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    sha = hashlib.sha256(lab.read_bytes()).hexdigest()
    man = {"retrieved": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "api": API,
           "query": "openfda.generic_name.exact:<DRUG> AND product_type HUMAN PRESCRIPTION DRUG AND _exists_:dosage_and_administration; sort effective_time:desc; limit 1 (fallback: generic_name word match)",
           "n_target": args.n, "n_labels": len(rows), "n_in_dose_bases": sum(r["in_dose_bases"] for r in rows),
           "lexicon_size": len(LEXICON), "lexicon_in_dose_bases": in_bases, "misses": misses,
           "max_chars": args.max_chars, "labels_sha256": sha, "script": "scripts/journal2/rd_fetch_labels.py"}
    (outd / "manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    (outd / "README.md").write_text(
        "# Real drug-label sample (journal experiment 1: real-world dose errors)\n\n"
        "One FDA Structured Product Label per drug, `dosage_and_administration` section (truncated to %d chars) and "
        "`dosage_forms_and_strengths`, downloaded from the openFDA drug label API on %s by "
        "`scripts/journal2/rd_fetch_labels.py` (query and per-drug misses in `manifest.json`; set_id/version/"
        "effective_time per row allow re-fetching the exact label from DailyMed).\n\n"
        "License: openFDA data (SPL content from DailyMed / NLM) is public domain, released under CC0 "
        "(https://open.fda.gov/license/). Not medical advice; labels may have been updated since retrieval.\n"
        % (args.max_chars, man["retrieved"]))
    print(json.dumps({k: v for k, v in man.items() if k not in ("misses", "lexicon_in_dose_bases")}, indent=1))


if __name__ == "__main__":
    main()
