#!/usr/bin/env python3
"""Write qc/ai_precheck_real_dose_unit_errors.csv: AI-ASSISTED PRE-CHECK of the 47 auto-labelled unit-type errors
(unit_error 15 = same numeral / other unit, basis_error 32) of the real-dose (RD) study.

AI-assisted pre-check by Grok Bot (LLM), not human verification; to be confirmed by a human annotator.
The adjudications below were made by reading, for each row, the cloze question, the FDA-label excerpt and target
sentence the reference dose was extracted from, the LLM answer, and the extracted answer/reference quantities
(results/journal2/real_dose/extract_rows.jsonl).  No API was called.  qc/real_dose_errors_check.csv is NOT modified.

ai_label: true_unit_error | parser_artifact_answer_correct | different_indication_or_population |
          value_error_misclassified | ambiguous
Rules used: true_unit_error = for the slot's own population/regimen, the answer differs from the label by unit or
basis (mg vs mg/kg, mg/kg vs mg/lb, per-day vs per-week, units vs mg, weight-based vs fixed absolute dose);
different_indication_or_population = the answer is a dose the drug's US prescribing information gives for another
population/indication/formulation (closed-book cloze questions often hide the population); value_error_misclassified =
same unit/basis as the label (after fixing the parse) but a wrong number, or a body-size basis swap whose numbers
are not an equivalent; ambiguous = cannot be decided without a human (e.g. a guideline weight-based range that
brackets the label's absolute dose).
Columns also carry each of the 7 checkers' stored verdict (rd_report operating point).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from impact_estimate import CHECKERS, RD, verdicts  # noqa: E402

OUT = ROOT / "qc/ai_precheck_real_dose_unit_errors.csv"
QC = ROOT / "qc/real_dose_errors_check.csv"
HEADER_NOTE = ("# AI-assisted pre-check by Grok Bot (LLM), not human verification; to be confirmed by a human annotator. "
               "Built by scripts/journal2/rd_ai_precheck_build.py; see notes/real_dose_ai_precheck.md")
T, A, D, V, Q = ("true_unit_error", "parser_artifact_answer_correct", "different_indication_or_population",
                 "value_error_misclassified", "ambiguous")
# instance_id suffix (drug_q__generator__mode) -> (ai_label, mechanism, confidence, rationale)
ADJ = {
    "allopurinol_1__gpt4o_mini__grounded": (A, "lost_superscript_m2", "high", "Label '100 mg/m 2' (lost superscript) = answer 100 mg/m²; answer correct."),
    "ivermectin_0__gpt4o_mini__grounded": (A, "split_unit_phrase", "high", "Label '200 mcg of ivermectin per kg of body weight' = answer 200 mcg per kg; parser read only '200 mcg'."),
    "vancomycin_1__gpt4o_mini__grounded": (D, "cloze_slot_mismatch", "med", "Slot is a vial-strength list (500 mg...); answer 10 mg/kg is the pediatric per-dose in the same excerpt, so a legit dose but the wrong slot."),
    "digoxin_0__gpt4o_mini__grounded": (A, "table_header_unit", "high", "Table header says loading dose is in mcg/kg; '10-15 mcg = microgram' is a footnote; answer 10-15 mcg/kg is correct."),
    "methotrexate_1__gpt4o_mini__grounded": (A, "lost_superscript_m2", "high", "Label '500 mg/m 2' = answer 500 mg/m²; answer correct."),
    "acetaminophen_1__gpt4o_mini__closed": (D, "adult_dose_for_pediatric_slot", "low", "Slot is infants (15 mg/kg q6h, max 60 mg/kg/day); answer 500 mg q6h/3 g is an adult OTC regimen (not this IV PI); population hidden by the cloze."),
    "allopurinol_1__gpt4o_mini__closed": (V, "wrong_value_same_basis", "high", "Same basis (mg/m²) as the label (lost superscript), but 300 vs 100 mg/m²: a value error."),
    "cefixime_0__gpt4o_mini__closed": (D, "other_population_in_label", "high", "Slot is the adult 400 mg daily; answer gives the label's pediatric 8 mg/kg/day, which is correct for children."),
    "clonidine_0__gpt4o_mini__closed": (T, "time_basis", "high", "Patch is 0.1 mg/day (changed weekly); answer '0.1 mg/week' is a 7-fold per-day vs per-week error."),
    "cyclophosphamide_0__gpt4o_mini__closed": (V, "bodysize_basis_swap", "low", "Label 40-50 mg/kg (~1500-1900 mg/m² for an adult); answer 300-1500 mg/m² is not in the PI and mostly far lower, so mainly wrong numbers."),
    "cyclophosphamide_1__gpt4o_mini__closed": (T, "dropped_basis", "med", "Label 10-15 mg/kg and 3-5 mg/kg; answer gives fixed 500-1000 mg / 300-400 mg (about right for a 50-70 kg adult, wrong for children); the per-kg basis is dropped."),
    "ivermectin_1__gpt4o_mini__closed": (T, "dropped_basis", "med", "For >=85 kg the label says 150 mcg/kg; answer fixed 5 tablets = 15 mg (176 mcg/kg at 85 kg); weight basis dropped, clinically minor."),
    "pregabalin_1__gpt4o_mini__closed": (D, "adult_dose_for_pediatric_slot", "med", "Slot is pediatric <30 kg (14 mg/kg/day); answer 150 mg (from 150-600 mg/day) is an adult regimen; also per-dose vs per-day unclear."),
    "verapamil_1__gpt4o_mini__closed": (D, "adult_dose_for_pediatric_slot", "med", "Slot is pediatric IV 0.1-0.3 mg/kg; answer 80-120 mg is the adult oral IR single dose (other formulation/population)."),
    "buspirone_1__gpt4o_mini__closed": (T, "dropped_basis", "high", "Methylene-blue threshold is 1 mg per kg; answer '1 mg' drops the per-kg basis (same numeral)."),
    "digoxin_0__gpt4o_mini__closed": (A, "table_header_unit", "high", "Table header unit mcg/kg; answer 10-15 mcg/kg is correct."),
    "glyburide_1__gpt4o_mini__closed": (T, "unit_kind", "high", "Slot is the insulin dose, 20 units; answer '20 mg' swaps the unit kind (same numeral)."),
    "levetiracetam_0__gpt4o_mini__closed": (D, "adult_dose_for_pediatric_slot", "high", "Slot is infants 1-6 months (7 mg/kg bid); answer 500 mg bid -> 1500 mg bid is the label's adult regimen."),
    "meropenem_1__gpt4o_mini__closed": (A, "cloze_slot_mismatch", "low", "Slot is the max-dose column (500 mg); answer gives the dose column 10 mg/kg (correct), but calls the population 'older patients' (table is pediatric >=3 months)."),
    "methotrexate_1__gpt4o_mini__closed": (A, "lost_superscript_m2", "high", "Label '500 mg/m 2' = answer 500 mg/m²; answer correct."),
    "norepinephrine_0__gpt4o_mini__closed": (Q, "guideline_weight_based_range", "med", "Label 8-12 mcg/min (slot is 0.25 mL); answer 0.05-0.5 mcg/kg/min is a guideline weight-based range that brackets the label for ~70 kg; not in the PI."),
    "norepinephrine_1__gpt4o_mini__closed": (Q, "guideline_weight_based_range", "med", "Label 8-12 mcg/min; answer 0.05-0.5 mcg/kg/min (practice range, brackets the label for ~70 kg)."),
    "oxcarbazepine_1__gpt4o_mini__closed": (D, "adult_dose_for_pediatric_slot", "high", "Slot is pediatric 8-10 mg/kg/day; answer 300 mg bid = adult initiation of 600 mg/day bid in the PI."),
    "allopurinol_1__gemma3_27b__grounded": (A, "lost_superscript_m2", "high", "Answer 100 mg/m² (+10 mg/kg/day, max 800 mg/day) matches the label exactly."),
    "losartan_0__gemma3_27b__grounded": (T, "dropped_basis", "high", "Label pediatric 0.7 mg per kg once daily; answer '0.7 mg once daily ... for pediatric patients' drops per kg (grounded!)."),
    "meropenem_1__gemma3_27b__grounded": (A, "cloze_slot_mismatch", "high", "Answer 'dose 10 mg/kg, maximum 500 mg' matches the table exactly; the parser took the first dose."),
    "methotrexate_1__gemma3_27b__grounded": (A, "lost_superscript_m2", "high", "Answer 500 mg/m² matches '500 mg/m 2'."),
    "acetaminophen_1__gemma3_27b__closed": (D, "adult_dose_for_pediatric_slot", "med", "Slot is infants (15 mg/kg); answer explicitly the 'typical adult dose' 650 mg q6h, max 4 g/day (PI adult: 650 mg q4h / 1000 mg q6h)."),
    "ceftriaxone_0__gemma3_27b__closed": (T, "dropped_basis", "high", "Pediatric SSSI 50-75 mg/kg/day; answer '500 mg' for pediatric patients drops the weight basis (e.g. a 20 kg child needs 1-1.5 g)."),
    "cyclophosphamide_0__gemma3_27b__closed": (Q, "bodysize_basis_swap", "med", "Label 40-50 mg/kg (~1.5-1.9 g/m² for an adult); answer 1.0-2.0 g/m² brackets the equivalent in another body-size basis; not in the PI."),
    "cyclophosphamide_1__gemma3_27b__closed": (V, "bodysize_basis_swap", "med", "Label 10-15 mg/kg (~400-600 mg/m²) and 3-5 mg/kg; answer 600-1200 mg/m² and 1.5-3 g/m² twice weekly are far higher: wrong numbers."),
    "epinephrine_0__gemma3_27b__closed": (T, "dropped_basis", "med", "Label titrate 0.05-2 mcg/kg/min; answer fixed 1-4 mcg/min (covers only the very bottom for 70 kg); weight basis dropped."),
    "ethambutol_1__gemma3_27b__closed": (T, "lb_vs_kg", "high", "Label 15 mg/kg (7 mg/lb); answer '15 mg/lb' is a ~2.2-fold overdose (kg vs lb; the parser lost '/lb')."),
    "isoniazid_1__gemma3_27b__closed": (D, "other_indication_in_label", "high", "Slot is preventive adults 300 mg/day; answer 5 mg/kg (max 300 mg) is the PI's adult treatment dose."),
    "ivermectin_0__gemma3_27b__closed": (A, "split_unit_phrase", "high", "Answer 200 micrograms per kg = label '200 mcg of ivermectin per kg'."),
    "ivermectin_1__gemma3_27b__closed": (T, "dropped_basis", "med", "For >=85 kg the label says 150 mcg/kg; answer fixed 5 tablets = 15 mg; weight basis dropped, clinically minor."),
    "pregabalin_1__gemma3_27b__closed": (D, "adult_dose_for_pediatric_slot", "high", "Slot is pediatric <30 kg (14 mg/kg/day); answer 300-600 mg/day is the adult range in the same table."),
    "verapamil_1__gemma3_27b__closed": (D, "adult_dose_for_pediatric_slot", "high", "Slot is pediatric IV mg/kg; answer explicitly the adult oral IR 80-120 mg tid."),
    "buspirone_1__gemma3_27b__closed": (V, "wrong_value_other_quantity", "high", "Methylene-blue threshold 1 mg/kg; answer '300 mg' of buspirone is a different quantity/value entirely."),
    "dobutamine_1__gemma3_27b__closed": (V, "parser_missed_basis", "high", "Answer '20 micrograms per minute per kilogram' = 20 mcg/kg/min (parser missed 'per kilogram'); label 40 mcg/kg/min, so a value error."),
    "filgrastim_1__gemma3_27b__closed": (T, "dropped_basis", "med", "Label 5 mcg/kg/day; answer fixed 300 mcg (a vial size, = 5 mcg/kg only at 60 kg); weight basis dropped."),
    "levetiracetam_0__gemma3_27b__closed": (D, "adult_dose_for_pediatric_slot", "high", "Slot is infants (7 mg/kg bid); answer 500 mg bid -> 1000 mg bid is the adult regimen."),
    "meloxicam_0__gemma3_27b__closed": (D, "other_population_in_label", "low", "Slot is OA/RA 7.5 mg; answer gives a JRA weight-based dose (0.25 mg/kg), which is itself not this PI's JRA dose (7.5 mg if >=60 kg; older PI 0.125 mg/kg)."),
    "meropenem_1__gemma3_27b__closed": (A, "cloze_slot_mismatch", "low", "Slot is max dose 500 mg; answer 10 mg/kg is the correct dose column value but says 'older adults' (table is pediatric)."),
    "methotrexate_1__gemma3_27b__closed": (V, "wrong_value_same_basis", "high", "Same basis (mg/m²); answer 50 vs label 500 mg/m²: a 10-fold value error."),
    "oxcarbazepine_1__gemma3_27b__closed": (D, "adult_dose_for_pediatric_slot", "high", "Slot is pediatric 8-10 mg/kg/day; answer 300 mg bid = adult initiation in the PI."),
    "tacrolimus_0__gemma3_27b__closed": (T, "dropped_basis", "high", "Label 0.2 mg/kg/day in two doses; answer '0.2 mg ... divided in two doses' drops per kg/day (same numeral)."),
}
SHORT = {"t6_minicheck_roberta.jsonl": "minicheck_roberta", "t6_minicheck_deberta.jsonl": "minicheck_deberta",
         "t6_alignscore_base.jsonl": "alignscore_base", "v2a_minicheck.jsonl": "minicheck_flant5", "v3_alignscore.jsonl": "alignscore_large",
         "v4_ragas_nli.jsonl": "ragas_llama70b", "v1_medscore.jsonl": "medscore_mistral24b"}


def short(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> None:
    rows = [json.loads(l) for l in (RD / "extract_rows.jsonl").open(encoding="utf-8")]
    unit = [r for r in rows if r["auto_class"] in ("unit_error", "basis_error")]
    qc = {r["instance_id"]: r["check_id"] for r in csv.DictReader(QC.open(encoding="utf-8-sig"))}
    vd = {SHORT[f]: verdicts(RD / "scores" / f) for f, _, _ in CHECKERS}
    keys = {r["instance_id"][3:] for r in unit}
    missing, extra = keys - set(ADJ), set(ADJ) - keys
    if missing or extra:
        raise SystemExit("adjudication table out of sync: missing %s extra %s" % (sorted(missing), sorted(extra)))
    cols = ["check_id", "instance_id", "drug", "mode", "generator", "auto_class", "auto_subtype", "answer_dose_auto",
            "label_dose_auto", "ai_label", "ai_mechanism", "ai_confidence", "ai_rationale", "label_excerpt", "answer_excerpt"] + \
        ["pass_" + SHORT[f] for f, _, _ in CHECKERS]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        fh.write(HEADER_NOTE + "\n")
        w = csv.writer(fh)
        w.writerow(cols)
        for r in unit:
            lab, mech, conf, why = ADJ[r["instance_id"][3:]]
            w.writerow([qc.get(r["instance_id"], ""), r["instance_id"], r["drug"], r["condition"], r["generator"], r["auto_class"],
                        r.get("subtype", ""), r.get("primary", ""), r.get("matched", ""), lab, mech, conf, why,
                        short(r["target_sentence"], 260), short(r["answer"], 220)] +
                       [vd[SHORT[f]].get(r["instance_id"], "missing") for f, _, _ in CHECKERS])
    print("wrote %s (%d rows)" % (OUT.relative_to(ROOT), len(unit)))


if __name__ == "__main__":
    main()
