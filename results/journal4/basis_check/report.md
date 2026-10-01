# Journal 4: dose-basis check — evaluation

Rule `basis-check-1` frozen at commit `fdb95de` (sha256 of `scripts/journal4/basis_check.py` = `92e07d560710`, unchanged since the freeze). Generated 2026-10-01T23:58:51+0700 by `scripts/journal4/basis_check_eval.py` (CPU, deterministic, no model calls). Inputs: answer (`claim`) and label excerpt (`evidence`) of `results/journal2/real_dose/instances.jsonl` only. Percentages with Wilson 95% CIs (rows, not drug-clustered).

**Caveats.** `true12` = AI-precheck `true_unit_error` labels (LLM, not human-verified); `flagged47` = auto unit_error + basis_error rows from `rd_extract.py`. Both are the **DEV set**: the rule was designed after reading them, so recall there is optimistic by construction. `non_flagged47` (1404) is only *presumably* correct: it also contains the auto value errors, other-context matches, time-ambiguous and unverifiable answers, and any unit errors the auto extractor missed — a flag there is a false-alarm **proxy**, not a confirmed false alarm. `auto_correct` (1062) = answers whose first dose matched the label target sentence (cleanest negative proxy).

Variants: **full** = R1 (same-numeral pairs) + R2 (unpaired basis neighbourhood), primary; **strict** = R1 only.

## (a) Recall on the DEV set

| subset | full: flagged | strict: flagged |
|---|---|---|
| true12 (DEV) | 12/12 = 100.0% [75.7, 100.0] | 6/12 = 50.0% [25.4, 74.6] |
| flagged47 (DEV) | 19/47 = 40.4% [27.6, 54.7] | 7/47 = 14.9% [7.4, 27.7] |
| precheck_parser_artifact_answer_correct (DEV, not errors) | 0/12 = 0.0% [0.0, 24.3] | 0/12 = 0.0% [0.0, 24.3] |
| precheck_different_indication_or_population (DEV) | 4/14 = 28.6% [11.7, 54.6] | 0/14 = 0.0% [0.0, 21.5] |
| precheck_value_error_misclassified (DEV) | 2/6 = 33.3% [9.7, 70.0] | 1/6 = 16.7% [3.0, 56.4] |
| precheck_ambiguous (DEV) | 1/3 = 33.3% [6.1, 79.2] | 0/3 = 0.0% [0.0, 56.2] |

Per case (true12):

| check | drug | mechanism (AI) | label dose | answer dose | full | strict |
|---|---|---|---|---|---|---|
| RDQ0050 | ivermectin | dropped_basis | 150 mcg/kg | 15 mg | basis_dropped_unpaired | abstain |
| RDQ0109 | glyburide | unit_kind | 20 units | 20 mg | unit_kind | unit_kind |
| RDQ0126 | buspirone | dropped_basis | 1 mg per kg | 1 mg | basis_dropped | basis_dropped |
| RDQ0137 | ethambutol | lb_vs_kg | 15 mg/kg | 15 mg | basis_changed | basis_changed |
| RDQ0145 | losartan | dropped_basis | 0.7 mg per kg | 0.7 mg | basis_dropped | basis_dropped |
| RDQ0165 | filgrastim | dropped_basis | 5 mcg/kg/day | 300 mcg | basis_dropped_unpaired | abstain |
| RDQ0210 | tacrolimus | dropped_basis | 0.2 mg/kg/day | 0.2 mg | basis_dropped | basis_dropped |
| RDQ0222 | cyclophosphamide | dropped_basis | 10 mg per kg | 500 mg | basis_dropped_unpaired | abstain |
| RDQ0228 | clonidine | time_basis | 0.1 mg/day | 0.1 mg/week | time_basis | time_basis |
| RDQ0247 | ivermectin | dropped_basis | 150 mcg/kg | 15 mg | basis_dropped_unpaired | abstain |
| RDQ0258 | epinephrine | dropped_basis | 0.05 mcg/kg/min | 1-4 micrograms per minute | basis_dropped_unpaired | abstain |
| RDQ0263 | ceftriaxone | dropped_basis | 50 to 75 mg/kg | 500 mg | basis_dropped_unpaired | abstain |

## (b) Flag rate (false-alarm proxy) and (c) abstain rate

| subset | n | full: flag | full: abstain | full: no_dose | strict: flag | strict: abstain |
|---|---|---|---|---|---|---|
| all | 1451 | 25/1451 = 1.7% [1.2, 2.5] | 20/1451 = 1.4% [0.9, 2.1] | 3/1451 = 0.2% [0.1, 0.6] | 11/1451 = 0.8% [0.4, 1.4] | 34/1451 = 2.3% [1.7, 3.3] |
| non_flagged47 | 1404 | 6/1404 = 0.4% [0.2, 0.9] | 16/1404 = 1.1% [0.7, 1.8] | 3/1404 = 0.2% [0.1, 0.6] | 4/1404 = 0.3% [0.1, 0.7] | 18/1404 = 1.3% [0.8, 2.0] |
| auto_correct | 1062 | 3/1062 = 0.3% [0.1, 0.8] | 0/1062 = 0.0% [0.0, 0.4] | 0/1062 = 0.0% [0.0, 0.4] | 3/1062 = 0.3% [0.1, 0.8] | 0/1062 = 0.0% [0.0, 0.4] |
| auto_match_other_context | 183 | 0/183 = 0.0% [0.0, 2.1] | 0/183 = 0.0% [0.0, 2.1] | 0/183 = 0.0% [0.0, 2.1] | 0/183 = 0.0% [0.0, 2.1] | 0/183 = 0.0% [0.0, 2.1] |
| auto_value_error | 93 | 1/93 = 1.1% [0.2, 5.8] | 6/93 = 6.5% [3.0, 13.4] | 0/93 = 0.0% [0.0, 4.0] | 0/93 = 0.0% [0.0, 4.0] | 7/93 = 7.5% [3.7, 14.7] |
| auto_time_ambiguous | 50 | 1/50 = 2.0% [0.4, 10.5] | 0/50 = 0.0% [0.0, 7.1] | 0/50 = 0.0% [0.0, 7.1] | 1/50 = 2.0% [0.4, 10.5] | 0/50 = 0.0% [0.0, 7.1] |
| auto_unverifiable | 16 | 1/16 = 6.2% [1.1, 28.3] | 10/16 = 62.5% [38.6, 81.5] | 3/16 = 18.8% [6.6, 43.0] | 0/16 = 0.0% [0.0, 19.4] | 11/16 = 68.8% [44.4, 85.8] |
| flagged47 | 47 | 19/47 = 40.4% [27.6, 54.7] | 4/47 = 8.5% [3.4, 19.9] | 0/47 = 0.0% [0.0, 7.6] | 7/47 = 14.9% [7.4, 27.7] | 16/47 = 34.0% [22.2, 48.3] |
| true12 | 12 | 12/12 = 100.0% [75.7, 100.0] | 0/12 = 0.0% [0.0, 24.3] | 0/12 = 0.0% [0.0, 24.3] | 6/12 = 50.0% [25.4, 74.6] | 6/12 = 50.0% [25.4, 74.6] |

Flag types (full): non_flagged47: {"basis_dropped": 2, "unit_kind": 1, "time_basis": 1, "basis_dropped_unpaired": 2}; auto_correct: {"basis_dropped": 2, "unit_kind": 1}; flagged47: {"basis_dropped_unpaired": 10, "time_basis": 1, "basis_changed_unpaired": 2, "basis_dropped": 3, "unit_kind": 1, "basis_changed": 2}

## Flagged answers outside flagged47 (for human review)

6 answers (by auto class {"correct": 3, "time_ambiguous": 1, "value_error": 1, "unverifiable": 1}; by rule {"R1": 4, "R2": 2}). Full list with snippets: `flagged_outside_flagged47.csv` (columns for a human judgment). First 20 below, sorted auto_correct first, then R1 before R2.

| # | drug / gen / mode | auto class | flag | answer dose | evidence dose(s) | answer (trunc.) | evidence context |
|---|---|---|---|---|---|---|---|
| 1 | allopurinol / gemma3_27b / closed | correct | basis_dropped (R1) | 100 mg | 100 mg/m2 | According to US prescribing information, the initial allopurinol dose is 100 mg orally every 8 to 12 hours (or 150 mg/day for patients with mild renal insufficiency), with a maximum dose of 800 mg per day. Therefore, the | …iated with Cancer Therapy: The recommended dosage is: Adults: 300 to 800 mg orally daily. Pediatric patients: «100 mg/m2» orally every 8 hours to 12 hours (10 mg/kg/day, maximum 800 mg/day) See complete information in the FPI. ( 2.… |
| 2 | glucagon / gpt4o_mini / closed | correct | unit_kind (R1) | 1 unit | 1 mg | The recommended dosage is 1 mg (1 unit) injected subcutaneously or intramuscularly. | …severe hypoglycemia ( 2.2 ) Adults and Pediatric Patients Weighing 20 kg or More: ■ The recommended dosage is «1 mg» (1 mL) injected subcutaneously or intramuscularly into the upper arm, thigh, or buttocks, or intravenously. ■… |
| 3 | ivermectin / gpt4o_mini / closed | correct | basis_dropped (R1) | 200 mcg | 200 mcg of ivermectin per kg | The recommended dosage of ivermectin for the treatment of strongyloidiasis is a single oral dose designed to provide approximately 200 micrograms (mcg) of ivermectin per kg of body weight. | …rmectin tablets for the treatment of strongyloidiasis is a single oral dose designed to provide approximately «200 mcg of ivermectin per kg» of body weight. See Table 1 for dosage guidelines. Patients should take tablets on an empty stomach with wate… |
| 4 | lamotrigine / gpt4o_mini / closed | time_ambiguous | time_basis (R1) | 50 mg | 50 to 100 mg/day | The dose increases should occur no more rapidly than 50 mg every week. | …time that the oral contraceptive is introduced and continue, based on clinical response, no more rapidly than «50 to 100 mg/day» every week. Dose increases should not exceed the recommended rate (see Tables 1 and 5) unless lamotrigine pla… |
| 5 | hydroxychloroquine / gemma3_27b / closed | value_error | basis_dropped_unpaired (R2) | 310 mg | 6.5 mg/kg | According to US prescribing information, the dose for hydroxychloroquine for pediatric patients ≥ 31 kg for once weekly dosing is 310 mg. This dose is typically continued for 8 weeks after stopping exposure. | … doses for 4 weeks after leaving the endemic area: - Adults: 400 mg once a week - Pediatric patients ≥ 31 kg: «6.5 mg/kg» up to 400 mg, once a week Treatment of Uncomplicated Malaria: See Full Prescribing Information (FPI) for comp… |
| 6 | sulfamethoxazole / gemma3_27b / closed | unverifiable | basis_dropped_unpaired (R2) | 200 mg | 40 mg/kg, 8 mg/kg | According to US prescribing information, the dose is 200 mg/40 mg per teaspoonful. Therefore, four teaspoonfuls equates to 800 mg/160 mg. | …igellosis. Children: The recommended dose for children with urinary tract infections or acute otitis media is «40 mg/kg» sulfamethoxazole and 8 mg/kg trimethoprim per 24 hours, given in two divided doses every 12 hours for 10 days… |

## (d) Combined pipeline: checker PASS AND basis check not flagged

Cells = PASS rate of the checker alone -> PASS rate of the combination (`checker PASS` and `not flagged`). On error subsets PASS = the error slips through (lower is better); on auto_correct PASS = correct answer accepted (higher is better; the drop is the cost of the basis check). flagged47 is NOT all errors (the precheck calls 12 of them parser artifacts with correct answers and 14 another population/indication), so its column is descriptive only. Frontier judges were only run on the true12/flagged47/smoke rows. The true12 columns are DEV-set numbers (the rule flags all 12 by construction).

| checker | true12 slip: checker -> +full (+strict) | flagged47 PASS: checker -> +full | auto_correct PASS: checker -> +full (+strict) | true12 still slipping (full) |
|---|---|---|---|---|
| MiniCheck-RoBERTa | 3/12 -> 0/12 (0) | 15/47 -> 12/47 | 77.0% -> 76.8% (76.8%) | none |
| MiniCheck-DeBERTa | 1/12 -> 0/12 (0) | 7/47 -> 6/47 | 71.6% -> 71.5% (71.5%) | none |
| AlignScore-base | 3/12 -> 0/12 (0) | 13/47 -> 10/47 | 85.4% -> 85.3% (85.3%) | none |
| MiniCheck-Flan-T5-Large | 2/12 -> 0/12 (1) | 13/47 -> 11/47 | 72.9% -> 72.7% (72.7%) | none |
| AlignScore-large | 3/12 -> 0/12 (0) | 15/47 -> 12/47 | 87.3% -> 87.2% (87.2%) | none |
| Llama-3.3-70B RAGAS | 1/12 -> 0/12 (0) | 13/47 -> 12/47 | 77.6% -> 77.5% (77.5%) | none |
| MedScore (Mistral-Small-24B) | 1/12 -> 0/12 (0) | 14/47 -> 13/47 | 76.5% -> 76.3% (76.3%) | none |
| FT alignscore_large_base | 3/12 -> 0/12 (0) | 15/47 -> 12/47 | 87.3% -> 87.2% (87.2%) | none |
| FT alignscore_large_r0.5 | 4/12 -> 0/12 (2) | 18/47 -> 12/47 | 80.4% -> 80.3% (80.3%) | none |
| FT alignscore_large_r1 | 7/12 -> 0/12 (3) | 17/47 -> 9/47 | 79.9% -> 79.8% (79.8%) | none |
| FT alignscore_large_r2 | 5/12 -> 0/12 (3) | 15/47 -> 8/47 | 80.0% -> 80.0% (80.0%) | none |
| FT minicheck_ft5_base | 2/12 -> 0/12 (1) | 13/47 -> 11/47 | 72.9% -> 72.7% (72.7%) | none |
| FT minicheck_ft5_r0.5 | 4/12 -> 0/12 (2) | 21/47 -> 14/47 | 79.2% -> 79.0% (79.0%) | none |
| FT minicheck_ft5_r1 | 3/12 -> 0/12 (1) | 20/47 -> 14/47 | 79.3% -> 79.3% (79.3%) | none |
| FT minicheck_ft5_r2 | 4/12 -> 0/12 (1) | 17/47 -> 11/47 | 78.0% -> 77.8% (77.8%) | none |
| judge llama31_8b | 3/12 -> 0/12 (0) [1 parse-fail] | 18/47 -> 15/47 [3 parse-fail] | 86.9% -> 86.8% (86.8%) [36 parse-fail] | none |
| judge medgemma_4b | 5/12 -> 0/12 (2) | 25/47 -> 19/47 | 94.3% -> 94.0% (94.0%) | none |
| judge qwen25_0p5b | 12/12 -> 0/12 (6) | 41/47 -> 24/47 [4 parse-fail] | 91.5% -> 91.2% (91.2%) [50 parse-fail] | none |
| judge qwen25_14b | 2/12 -> 0/12 (0) | 12/47 -> 10/47 [2 parse-fail] | 61.8% -> 61.7% (61.7%) [63 parse-fail] | none |
| judge qwen25_1p5b | 2/12 -> 0/12 (0) [6 parse-fail] | 10/47 -> 7/47 [18 parse-fail] | 61.9% -> 61.7% (61.7%) [279 parse-fail] | none |
| judge qwen25_3b | 0/12 -> 0/12 (0) [5 parse-fail] | 3/47 -> 3/47 [17 parse-fail] | 38.0% -> 37.9% (37.9%) [260 parse-fail] | none |
| judge qwen25_7b | 3/12 -> 0/12 (0) [1 parse-fail] | 13/47 -> 10/47 [9 parse-fail] | 71.9% -> 71.8% (71.8%) [122 parse-fail] | none |
| frontier anthropic_claude-opus-5.5 | 0/12 -> 0/12 (0) | 10/47 -> 10/47 | 50.0% -> 50.0% (50.0%) | none |
| frontier google_gemini-3.1-pro-preview | 0/12 -> 0/12 (0) | 10/47 -> 10/47 | 75.0% -> 75.0% (75.0%) | none |
