#!/usr/bin/env python3
"""(RD2-0, box: needs internet) FDA labels for NEW drugs (none of the RD drugs), for the RD2 question set.

Same source and query as the original RD sample (scripts/journal2/rd_fetch_labels.py, whose fetch() is imported and
reused unchanged): openFDA drug label endpoint, most recent HUMAN PRESCRIPTION DRUG label per generic name with a
dosage_and_administration section containing >= 1 parseable dose (src/unit_norm_fix.find_spans).

Differences from RD (documented in prereg/rd2_prereg.md):
  * lexicon = drugs NOT in RD, ordered to favour error-prone dosing (BSA / weight-based / pediatric / loading-maintenance
    / renal adjustment): oncology, anti-infectives with weight-based or renally adjusted regimens, ICU infusions,
    antidotes, biologics, pediatric antiepileptics; then the remaining unused drugs of the RD lexicon.
  * every label is checked against RD (lexicon name, set_id, openFDA generic/brand names, shared ingredient word) and
    dropped on ANY overlap (rd2_common.label_overlaps_rd1), so RD2 is drug-disjoint from RD.
  * dosage_and_administration kept up to --max-chars 20000 (RD: 8000) so pediatric / renal subsections near the end
    of long sections are eligible; question excerpts stay <= 900 chars exactly as in RD.
Outputs (NEW files): results/journal5/rd2/labels/{labels.jsonl, manifest.json, README.md}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import RD2_LABELS, label_overlaps_rd1, log, rd1_exclusion, sha256_file, write_jsonl  # noqa: E402
from rd_fetch_labels import API, LEXICON as RD_LEXICON, fetch  # noqa: E402
from unit_norm_fix import find_spans  # noqa: E402

# Fixed order: error-prone dosing first.  Not exhaustive; duplicates / RD drugs are removed below.
LEXICON_RD2 = """
carboplatin cisplatin oxaliplatin docetaxel paclitaxel cabazitaxel doxorubicin epirubicin daunorubicin idarubicin
fluorouracil capecitabine gemcitabine irinotecan topotecan etoposide vincristine vinblastine vinorelbine cytarabine
ifosfamide bleomycin pemetrexed bortezomib azacitidine decitabine fludarabine bendamustine cladribine busulfan melphalan
carmustine dacarbazine temozolomide mitomycin mitoxantrone eribulin ixabepilone romidepsin pralatrexate trabectedin
clofarabine nelarabine thiotepa dactinomycin mercaptopurine thioguanine hydroxyurea leucovorin levoleucovorin mesna
dexrazoxane amifostine rasburicase rituximab trastuzumab bevacizumab cetuximab panitumumab daratumumab obinutuzumab
brentuximab blinatumomab pegaspargase ramucirumab pertuzumab ipilimumab
tobramycin streptomycin nafcillin oxacillin cefoxitin cefotetan ceftaroline aztreonam colistimethate tigecycline
telavancin dalbavancin oritavancin tedizolid chloramphenicol rifabutin rifapentine bedaquiline cycloserine ethionamide
caspofungin micafungin anidulafungin posaconazole flucytosine itraconazole foscarnet cidofovir remdesivir peramivir
valganciclovir famciclovir artesunate pentamidine nitazoxanide miltefosine tinidazole sulfadiazine cefprozil
cefpodoxime cefadroxil dicloxacillin
milrinone nitroprusside isoproterenol procainamide ibutilide adenosine cisatracurium atracurium pancuronium remifentanil
sufentanil alfentanil fosphenytoin lacosamide brivaracetam methohexital pentobarbital levocarnitine sugammadex
aminocaproic tranexamic protamine phytonadione eptifibatide tirofiban cangrelor tenecteplase dalteparin edoxaban
acetylcysteine fomepizole deferoxamine hydroxocobalamin physostigmine pralidoxime dimercaprol succimer glucarpidase
epoetin darbepoetin ferumoxytol pamidronate ibandronate calcitonin somatropin caffeine aminophylline doxapram
cosyntropin deferasirox deferiprone eltrombopag romiplostim emicizumab eculizumab ravulizumab infliximab tocilizumab
vedolizumab ustekinumab abatacept golimumab belimumab anakinra canakinumab natalizumab basiliximab everolimus sirolimus
palivizumab imiglucerase agalsidase laronidase idursulfase alglucosidase
ethosuximide felbamate rufinamide clobazam vigabatrin zonisamide primidone cannabidiol ursodiol chlorothiazide bosentan
ambrisentan cyproheptadine hydroxyzine cimetidine glycopyrrolate methylphenidate atomoxetine guanfacine dofetilide
sotalol saxagliptin linagliptin alogliptin
""".split()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=230, help="stop after this many usable NEW labels")
    ap.add_argument("--max-chars", type=int, default=20000)
    ap.add_argument("--out", default=str(RD2_LABELS))
    ap.add_argument("--sleep", type=float, default=0.3)
    args = ap.parse_args()
    excl = rd1_exclusion()
    order = list(dict.fromkeys(LEXICON_RD2 + RD_LEXICON))
    rows, misses = [], []
    for drug in order:
        if len(rows) >= args.n:
            break
        if drug in excl["drugs"]:
            misses.append({"drug": drug, "why": "drug_in_rd"})
            continue
        hit = fetch(drug)
        time.sleep(args.sleep)
        if not hit:
            misses.append({"drug": drug, "why": "no_label"})
            continue
        of = hit.get("openfda") or {}
        lab = {"drug": drug, "set_id": hit.get("set_id"), "generic_name": of.get("generic_name"),
               "brand_name": of.get("brand_name")}
        why = label_overlaps_rd1(lab, excl)
        if why:
            misses.append({"drug": drug, "why": why, "generic_name": of.get("generic_name")})
            continue
        if any(r["set_id"] == hit.get("set_id") for r in rows):
            misses.append({"drug": drug, "why": "duplicate_set_id"})
            continue
        da = " ".join(hit.get("dosage_and_administration") or []).strip()
        if not find_spans(da):
            misses.append({"drug": drug, "why": "no_dose_span"})
            continue
        rows.append({
            "drug": drug, "in_dose_bases": False, "match": hit["_match"],
            "set_id": hit.get("set_id"), "spl_id": hit.get("id"), "version": hit.get("version"),
            "effective_time": hit.get("effective_time"),
            "generic_name": of.get("generic_name"), "brand_name": of.get("brand_name"), "route": of.get("route"),
            "manufacturer_name": of.get("manufacturer_name"), "product_type": of.get("product_type"),
            "dosage_and_administration": da[: args.max_chars], "da_truncated": len(da) > args.max_chars,
            "da_chars_full": len(da),
            "dosage_forms_and_strengths": " ".join(hit.get("dosage_forms_and_strengths") or [])[:1500],
            "dailymed_url": "https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=%s" % hit.get("set_id"),
        })
        log("RD2_fetch", drug=drug, ok=True, n=len(rows), eff=hit.get("effective_time"), match=hit["_match"])
    out = Path(args.out)
    write_jsonl(out, rows)
    man = {"retrieved": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "api": API,
           "query": "same as scripts/journal2/rd_fetch_labels.fetch (exact generic name, HUMAN PRESCRIPTION DRUG, "
                    "_exists_:dosage_and_administration, sort effective_time:desc, limit 1; fallback generic_name word match)",
           "n_target": args.n, "n_labels": len(rows), "lexicon_rd2_size": len(LEXICON_RD2), "order_size": len(order),
           "misses": misses, "max_chars": args.max_chars, "labels_sha256": sha256_file(out),
           "rd_exclusion": {"drugs": len(excl["drugs"]), "set_ids": len(excl["set_ids"]), "names": len(excl["names"]),
                            "ingredient_words": len(excl["words"])},
           "script": "scripts/journal5/rd2_fetch_labels.py"}
    (out.parent / "manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    (out.parent / "README.md").write_text(
        "# RD2 drug-label sample (journal 5)\n\nOne FDA Structured Product Label per NEW drug (no drug, set_id, generic/brand "
        "name or ingredient word shared with the RD sample in data/real_labels/), `dosage_and_administration` (truncated "
        "to %d chars) and `dosage_forms_and_strengths`, downloaded from the openFDA drug label API on %s by "
        "`scripts/journal5/rd2_fetch_labels.py` (query, misses and exclusion reasons in `manifest.json`).\n\n"
        "License: openFDA data (SPL content from DailyMed / NLM) is public domain, released under CC0 "
        "(https://open.fda.gov/license/). Not medical advice; labels may have been updated since retrieval.\n"
        % (args.max_chars, man["retrieved"]))
    log("RD2_fetch", **{k: v for k, v in man.items() if k != "misses"})


if __name__ == "__main__":
    main()
