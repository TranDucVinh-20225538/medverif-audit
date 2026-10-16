# RD2 label audit → provisional v3

Read-only audit over `amend1/labels_v2.jsonl` (job artifacts unchanged). **v3** = v2 scored set minus non-dose slots; `correct_suspect` held out (not counted as correct).

## 1. Non-dose slot exclusions

- Scored answers (instances): **5688**
- Answers excluded: **1038** (18.2%)
- Distinct questions excluded: **102** / 480
- Reason counts (answer-level, may stack):

| reason tag | n answers |
|---|---:|
| `extract:non_dose_unit:mL/min` | 327 |
| `gold:renal_clearance_threshold` | 252 |
| `gold:non_dose_unit:mL/min` | 189 |
| `extract:renal_clearance_threshold` | 146 |
| `gold:volume_mL` | 102 |
| `gold:reconstitution_volume` | 82 |
| `extract:volume_mL` | 77 |
| `gold:lab_threshold` | 76 |
| `gold:rounding_increment` | 72 |
| `gold:iron_LIC_threshold` | 71 |
| `extract:rounding_increment` | 60 |
| `extract:lab_threshold` | 60 |
| `extract:iron_LIC_threshold` | 59 |
| `extract:reconstitution_volume` | 57 |
| `gold:bag_or_dilution_volume` | 36 |
| `gold:non_dose_unit:mcg/mL` | 34 |
| `extract:non_dose_unit:mcg/mL` | 32 |
| `extract:bag_or_dilution_volume` | 25 |
| `extract:non_dose_unit:mL/minute` | 25 |
| `gold:non_dose_unit:LIC` | 24 |
| `extract:non_dose_unit:mg Fe/g` | 14 |
| `gold:non_dose_unit:mL/minute` | 12 |
| `gold:non_dose_unit:mL per hour` | 12 |
| `matched:lab_threshold` | 12 |
| `extract:non_dose_unit:mL/hour` | 11 |

Files: `excluded_non_dose.csv`, `excluded_non_dose_questions.csv`.

## 2. `correct_suspect` (stricter side-check on v2=correct, non-excluded)

- Flagged: **257** / 3037 v2-correct remaining after non-dose exclusion
- These are **not** counted as correct under v3 (`class_v3=correct_suspect`, `ref_v3` empty).

### 20 examples

1. `RD2_alglucosidase_2__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:1 mg/kg/hour_vs_evidence_2 mg/kg/hr
   - primary_v2=`1 mg/kg/hour` matched=`1 mg/kg/hr`
   - answer: The initial infusion rate should be no more than 1 mg/kg/hour.
2. `RD2_atovaquone_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — tablet_vs_mL_formulation
   - primary_v2=`750 mg` matched=`750 mg`
   - answer: The recommended oral dosage is 750 mg (1 tablet) twice daily (total daily dose = 1500 mg) administered with food for 21 days.
3. `RD2_atracurium_1__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — primary_vs_matched_numeric:0.5 mg/kg_vs_0.3 to 0.5 mg/kg
   - primary_v2=`0.5 mg/kg` matched=`0.3 to 0.5 mg/kg`
   - answer: The recommended initial bolus dose for atracurium besylate injection is 0.5 mg/kg.
4. `RD2_busulfan_1__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:60 mg/kg_vs_evidence_0.8 mg per kg
   - primary_v2=`60 mg/kg` matched=`60 mg per kg`
   - answer: The dose is 60 mg/kg intravenously.
5. `RD2_carmustine_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:150 mg/m²_vs_evidence_75 to 100 mg/m2
   - primary_v2=`150 mg/m2` matched=`150 to 200 mg/m2`
   - answer: The dose is 150 mg/m².
6. `RD2_cefotaxime_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:150 mg per kg_vs_evidence_50 mg/kg per dose;primary_vs_matched_numeric:150 mg per kg_vs_50 to 180 mg/kg
   - primary_v2=`150 mg per kg` matched=`50 to 180 mg/kg`
   - answer: The recommended daily dose for body weights less than 50 kg is 150 mg per kg.
7. `RD2_cefoxitin_1__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:100 mg per kg per day_vs_evidence_80 to 160 mg/kg of body weight per day;primary_vs_matched_numeric:100 mg per kg per day_vs_80 to 160 mg/kg of body weight per day
   - primary_v2=`100 mg per kg per day` matched=`80 to 160 mg/kg of body weight per day`
   - answer: The recommended dose is 100 mg per kg per day.
8. `RD2_chloroquine_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — base_mg_mismatch;answer_dose_absent_conflict:1000 mg_vs_evidence_5 mg
   - primary_v2=`1000 mg` matched=`1 g`
   - answer: The initial double (loading) dose for adults is 1000 mg of base.
9. `RD2_cisatracurium_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:0.1 to 0.2 mg per kg_vs_evidence_0.15 mg/kg
   - primary_v2=`0.1 to 0.2 mg per kg` matched=`0.1 to 0.15 mg/kg`
   - answer: The recommended dose is 0.1 to 0.2 mg per kg.
10. `RD2_doxorubicin_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — primary_vs_matched_numeric:60 mg/m2_vs_40 to 75 mg/m2
   - primary_v2=`60 mg/m2` matched=`40 to 75 mg/m2`
   - answer: The dose is 60 mg/m² given intravenously every 21 to 28 days.
11. `RD2_doxorubicin_1__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — range_bound_mismatch:60-75_vs_2-75mg/m²;answer_dose_absent_conflict:60 to 75 mg/m²_vs_evidence_75 mg/m2
   - primary_v2=`60 to 75 mg/m2` matched=`60 mg/m2`
   - answer: The recommended dose is 60 to 75 mg/m² intravenously every 21 days.
12. `RD2_fosphenytoin_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — range_bound_mismatch:15-20_vs_100-150mg;range_bound_mismatch:15-20_vs_10-20mg;range_bound_mismatch:15-20_vs_4-6mg;range_bound_mismatch:15-20_vs_10-15mg;range_bound_mismatch:15-20_vs_1-2mg
   - primary_v2=`15 to 20 mg` matched=`10 to 20 mg`
   - answer: The adult loading dose is 15 to 20 mg PE/kg given IV or IM.
13. `RD2_infliximab_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:5 mg per kg_vs_evidence_10 mg/kg
   - primary_v2=`5 mg per kg` matched=`5 mg/kg`
   - answer: The recommended dose is 5 mg per kg.
14. `RD2_mitoxantrone_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:12 mg per square meter_vs_evidence_140 mg/m2
   - primary_v2=`12 mg per m2` matched=`12 mg/m2`
   - answer: The recommended dose is 12 mg per square meter of body surface area (mg/m²).
15. `RD2_obinutuzumab_2__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:650 mg_vs_evidence_50 mg
   - primary_v2=`650 mg` matched=`650–1,000 mg`
   - answer: According to the US prescribing information, the dose is 650 mg acetaminophen.
16. `RD2_pentobarbital_2__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — primary_vs_matched_numeric:500 mg_vs_200 to 500 mg
   - primary_v2=`500 mg` matched=`200 to 500 mg`
   - answer: The dose is 500 mg.
17. `RD2_procainamide_1__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:100 mg_vs_evidence_50 mg per minute
   - primary_v2=`100 mg` matched=`100 to 500 mg`
   - answer: The suggested dose is 100 mg by intramuscular injection.
18. `RD2_tinidazole_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:2 grams_vs_evidence_1 g
   - primary_v2=`2 grams` matched=`2 g`
   - answer: The dose is 2 grams.
19. `RD2_tinidazole_2__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:2 grams_vs_evidence_1 g
   - primary_v2=`2 grams` matched=`2 g`
   - answer: The recommended dose for bacterial vaginosis is 2 grams oral once daily for 2 days.
20. `RD2_vincristine_0__baichuan_m2_32b__closed` (closed/baichuan_m2_32b) — answer_dose_absent_conflict:1.5 mg/m²_vs_evidence_1.4 mg/m2
   - primary_v2=`1.5 mg/m2` matched=`1.5–2 mg/m2`
   - answer: The usual dose of Vincristine Sulfate Injection for pediatric patients is 1.5 mg/m².

## 3. Error-label audit sample (n=40, seed 20261016)

Pool: v2 unit_error+basis_error, not non-dose-excluded (pool size 347). Prelim machine guess — **not** human adjudication.

- prelim true_error: **30**; suspect_mislabeled: **10**
- File: `error_audit_sample40.csv` (`human_check` blank).

## 4. Reference set sizes

| set | v2 | v3 |
|---|---:|---:|
| scored in eval frame | 5688 | 4650 |
| error (unit+basis) | 426 | 347 |
| correct / nonerror | 3679 | 2780 |
| excluded_non_dose | — | 1038 |
| correct_suspect (held out) | — | 257 |

## 5. Rates: v2 vs v3 (PARSE_FAIL excluded; Wilson 95% CI)

Metrics: **pass-on-error (leak)** = PASS / (PASS+FAIL) on unit+basis errors; **false-reject** = FAIL / (PASS+FAIL) on correct (v3: not excluded, not `correct_suspect`).

### v3 only — checker/judge × closed/grounded (with Wilson CI)

> **Note (v3):** after non-dose exclusion, **all remaining unit+basis errors are closed-book** (n_error_grounded = 0). Grounded pass-on-error cells are empty by design.


| system | cond | pass-on-error % (k/n; Wilson) | false-reject % (k/n; Wilson) |
|---|---|---|---|
| MiniCheck-RoBERTa | closed | 14.4 (50/347; 11.1–18.5) | 27.0 (180/667; 23.8–30.5) |
| MiniCheck-RoBERTa | grounded | — (0) | 9.7 (204/2113; 8.5–11.0) |
| MiniCheck-DeBERTa | closed | 11.2 (39/347; 8.3–15.0) | 55.9 (373/667; 52.1–59.6) |
| MiniCheck-DeBERTa | grounded | — (0) | 24.8 (523/2113; 23.0–26.6) |
| AlignScore-base | closed | 19.3 (67/347; 15.5–23.8) | 31.3 (209/667; 27.9–35.0) |
| AlignScore-base | grounded | — (0) | 13.6 (287/2113; 12.2–15.1) |
| MiniCheck-Flan-T5-Large | closed | 14.4 (50/347; 11.1–18.5) | 40.9 (273/667; 37.3–44.7) |
| MiniCheck-Flan-T5-Large | grounded | — (0) | 21.2 (448/2113; 19.5–23.0) |
| AlignScore-large | closed | 16.7 (58/347; 13.2–21.0) | 19.2 (128/667; 16.4–22.4) |
| AlignScore-large | grounded | — (0) | 6.7 (141/2113; 5.7–7.8) |
| Llama-3.3-70B RAGAS-NLI | closed | 3.2 (11/347; 1.8–5.6) | 19.8 (132/667; 16.9–23.0) |
| Llama-3.3-70B RAGAS-NLI | grounded | — (0) | 13.4 (284/2113; 12.1–15.0) |
| MedScore (Mistral-Small-24B) | closed | 5.8 (20/347; 3.8–8.7) | 18.6 (124/667; 15.8–21.7) |
| MedScore (Mistral-Small-24B) | grounded | — (0) | 14.9 (314/2113; 13.4–16.4) |
| basis_check_full | closed | 40.1 (139/347; 35.0–45.3) | 0.0 (0/667; 0.0–0.6) |
| basis_check_full | grounded | — (0) | 0.0 (0/2113; 0.0–0.2) |
| basis_check_strict | closed | 70.6 (245/347; 65.6–75.2) | 0.0 (0/667; 0.0–0.6) |
| basis_check_strict | grounded | — (0) | 0.0 (0/2113; 0.0–0.2) |
| Claude Sonnet HTML | closed | 1.7 (6/346; 0.8–3.7) | 22.0 (147/667; 19.1–25.3) |
| Claude Sonnet HTML | grounded | — (0) | 10.4 (219/2113; 9.1–11.7) |
| GPT-4o HTML | closed | 2.3 (8/347; 1.2–4.5) | 23.1 (154/667; 20.1–26.4) |
| GPT-4o HTML | grounded | — (0) | 18.4 (388/2113; 16.8–20.1) |
| DeepSeek Chat HTML | closed | 4.0 (14/347; 2.4–6.7) | 22.2 (148/667; 19.2–25.5) |
| DeepSeek Chat HTML | grounded | — (0) | 15.7 (331/2113; 14.2–17.3) |

Machine-readable: `label_audit_v3_by_system.csv`, `label_audit_v3_rates.csv` (includes v2).

### v2 vs v3 side-by-side (point estimates)

#### Condition: `closed`

| system | leak v2 | leak v3 | Δpp | FR v2 | FR v3 | Δpp |
|---|---|---|---:|---|---|---:|
| MiniCheck-RoBERTa | 14.1 (60/425) | 14.4 (50/347) | +0.3 | 33.2 (333/1002) | 27.0 (180/667) | -6.2 |
| MiniCheck-DeBERTa | 10.4 (44/425) | 11.2 (39/347) | +0.9 | 58.5 (586/1002) | 55.9 (373/667) | -2.6 |
| AlignScore-base | 18.4 (78/425) | 19.3 (67/347) | +1.0 | 36.5 (366/1002) | 31.3 (209/667) | -5.2 |
| MiniCheck-Flan-T5-Large | 15.5 (66/425) | 14.4 (50/347) | -1.1 | 44.5 (446/1002) | 40.9 (273/667) | -3.6 |
| AlignScore-large | 16.5 (70/425) | 16.7 (58/347) | +0.2 | 25.6 (257/1002) | 19.2 (128/667) | -6.5 |
| Llama-3.3-70B RAGAS-NLI | 4.2 (18/425) | 3.2 (11/347) | -1.1 | 28.9 (290/1002) | 19.8 (132/667) | -9.2 |
| MedScore (Mistral-Small-24B) | 6.6 (28/425) | 5.8 (20/347) | -0.8 | 28.0 (281/1002) | 18.6 (124/667) | -9.5 |
| basis_check_full | 44.7 (190/425) | 40.1 (139/347) | -4.6 | 0.4 (4/1002) | 0.0 (0/667) | -0.4 |
| basis_check_strict | 73.4 (312/425) | 70.6 (245/347) | -2.8 | 0.4 (4/1002) | 0.0 (0/667) | -0.4 |
| Claude Sonnet HTML | 2.1 (9/424) | 1.7 (6/346) | -0.4 | 31.4 (315/1002) | 22.0 (147/667) | -9.4 |
| GPT-4o HTML | 3.5 (15/425) | 2.3 (8/347) | -1.2 | 31.4 (315/1002) | 23.1 (154/667) | -8.3 |
| DeepSeek Chat HTML | 4.9 (21/425) | 4.0 (14/347) | -0.9 | 30.4 (305/1002) | 22.2 (148/667) | -8.3 |

#### Condition: `grounded`

| system | leak v2 | leak v3 | Δpp | FR v2 | FR v3 | Δpp |
|---|---|---|---:|---|---|---:|
| MiniCheck-RoBERTa | 0.0 (0/1) | — (0) | +nan | 10.7 (287/2677) | 9.7 (204/2113) | -1.1 |
| MiniCheck-DeBERTa | 0.0 (0/1) | — (0) | +nan | 26.1 (699/2677) | 24.8 (523/2113) | -1.4 |
| AlignScore-base | 0.0 (0/1) | — (0) | +nan | 13.7 (366/2677) | 13.6 (287/2113) | -0.1 |
| MiniCheck-Flan-T5-Large | 0.0 (0/1) | — (0) | +nan | 22.6 (606/2677) | 21.2 (448/2113) | -1.4 |
| AlignScore-large | 0.0 (0/1) | — (0) | +nan | 7.7 (206/2677) | 6.7 (141/2113) | -1.0 |
| Llama-3.3-70B RAGAS-NLI | 0.0 (0/1) | — (0) | +nan | 16.7 (447/2676) | 13.4 (284/2113) | -3.3 |
| MedScore (Mistral-Small-24B) | 0.0 (0/1) | — (0) | +nan | 17.8 (477/2677) | 14.9 (314/2113) | -3.0 |
| basis_check_full | 100.0 (1/1) | — (0) | +nan | 0.0 (1/2677) | 0.0 (0/2113) | -0.0 |
| basis_check_strict | 100.0 (1/1) | — (0) | +nan | 0.0 (1/2677) | 0.0 (0/2113) | -0.0 |
| Claude Sonnet HTML | 0.0 (0/1) | — (0) | +nan | 14.1 (377/2677) | 10.4 (219/2113) | -3.7 |
| GPT-4o HTML | 0.0 (0/1) | — (0) | +nan | 21.6 (579/2677) | 18.4 (388/2113) | -3.3 |
| DeepSeek Chat HTML | 0.0 (0/1) | — (0) | +nan | 18.7 (500/2677) | 15.7 (331/2113) | -3.0 |

#### Condition: `all`

| system | leak v2 | leak v3 | Δpp | FR v2 | FR v3 | Δpp |
|---|---|---|---:|---|---|---:|
| MiniCheck-RoBERTa | 14.1 (60/426) | 14.4 (50/347) | +0.3 | 16.9 (620/3679) | 13.8 (384/2780) | -3.0 |
| MiniCheck-DeBERTa | 10.3 (44/426) | 11.2 (39/347) | +0.9 | 34.9 (1285/3679) | 32.2 (896/2780) | -2.7 |
| AlignScore-base | 18.3 (78/426) | 19.3 (67/347) | +1.0 | 19.9 (732/3679) | 17.8 (496/2780) | -2.1 |
| MiniCheck-Flan-T5-Large | 15.5 (66/426) | 14.4 (50/347) | -1.1 | 28.6 (1052/3679) | 25.9 (721/2780) | -2.7 |
| AlignScore-large | 16.4 (70/426) | 16.7 (58/347) | +0.3 | 12.6 (463/3679) | 9.7 (269/2780) | -2.9 |
| Llama-3.3-70B RAGAS-NLI | 4.2 (18/426) | 3.2 (11/347) | -1.1 | 20.0 (737/3678) | 15.0 (416/2780) | -5.1 |
| MedScore (Mistral-Small-24B) | 6.6 (28/426) | 5.8 (20/347) | -0.8 | 20.6 (758/3679) | 15.8 (438/2780) | -4.8 |
| basis_check_full | 44.8 (191/426) | 40.1 (139/347) | -4.8 | 0.1 (5/3679) | 0.0 (0/2780) | -0.1 |
| basis_check_strict | 73.5 (313/426) | 70.6 (245/347) | -2.9 | 0.1 (5/3679) | 0.0 (0/2780) | -0.1 |
| Claude Sonnet HTML | 2.1 (9/425) | 1.7 (6/346) | -0.4 | 18.8 (692/3679) | 13.2 (366/2780) | -5.6 |
| GPT-4o HTML | 3.5 (15/426) | 2.3 (8/347) | -1.2 | 24.3 (894/3679) | 19.5 (542/2780) | -4.8 |
| DeepSeek Chat HTML | 4.9 (21/426) | 4.0 (14/347) | -0.9 | 21.9 (805/3679) | 17.2 (479/2780) | -4.7 |

## 6. Changes > 2 percentage points (v3 − v2)

| system | condition | metric | v2%% | v3%% | Δpp |
|---|---|---|---:|---:|---:|
| MedScore (Mistral-Small-24B) | closed | fail_on_correct_false_reject | 28.0 | 18.6 | -9.5 |
| Claude Sonnet HTML | closed | fail_on_correct_false_reject | 31.4 | 22.0 | -9.4 |
| Llama-3.3-70B RAGAS-NLI | closed | fail_on_correct_false_reject | 28.9 | 19.8 | -9.2 |
| GPT-4o HTML | closed | fail_on_correct_false_reject | 31.4 | 23.1 | -8.3 |
| DeepSeek Chat HTML | closed | fail_on_correct_false_reject | 30.4 | 22.2 | -8.3 |
| AlignScore-large | closed | fail_on_correct_false_reject | 25.6 | 19.2 | -6.5 |
| MiniCheck-RoBERTa | closed | fail_on_correct_false_reject | 33.2 | 27.0 | -6.2 |
| Claude Sonnet HTML | all | fail_on_correct_false_reject | 18.8 | 13.2 | -5.6 |
| AlignScore-base | closed | fail_on_correct_false_reject | 36.5 | 31.3 | -5.2 |
| Llama-3.3-70B RAGAS-NLI | all | fail_on_correct_false_reject | 20.0 | 15.0 | -5.1 |
| MedScore (Mistral-Small-24B) | all | fail_on_correct_false_reject | 20.6 | 15.8 | -4.8 |
| GPT-4o HTML | all | fail_on_correct_false_reject | 24.3 | 19.5 | -4.8 |
| basis_check_full | all | pass_on_error_leak | 44.8 | 40.1 | -4.8 |
| DeepSeek Chat HTML | all | fail_on_correct_false_reject | 21.9 | 17.2 | -4.7 |
| basis_check_full | closed | pass_on_error_leak | 44.7 | 40.1 | -4.6 |
| Claude Sonnet HTML | grounded | fail_on_correct_false_reject | 14.1 | 10.4 | -3.7 |
| MiniCheck-Flan-T5-Large | closed | fail_on_correct_false_reject | 44.5 | 40.9 | -3.6 |
| GPT-4o HTML | grounded | fail_on_correct_false_reject | 21.6 | 18.4 | -3.3 |
| Llama-3.3-70B RAGAS-NLI | grounded | fail_on_correct_false_reject | 16.7 | 13.4 | -3.3 |
| MiniCheck-RoBERTa | all | fail_on_correct_false_reject | 16.9 | 13.8 | -3.0 |
| DeepSeek Chat HTML | grounded | fail_on_correct_false_reject | 18.7 | 15.7 | -3.0 |
| MedScore (Mistral-Small-24B) | grounded | fail_on_correct_false_reject | 17.8 | 14.9 | -3.0 |
| AlignScore-large | all | fail_on_correct_false_reject | 12.6 | 9.7 | -2.9 |
| basis_check_strict | all | pass_on_error_leak | 73.5 | 70.6 | -2.9 |
| basis_check_strict | closed | pass_on_error_leak | 73.4 | 70.6 | -2.8 |
| MiniCheck-DeBERTa | all | fail_on_correct_false_reject | 34.9 | 32.2 | -2.7 |
| MiniCheck-Flan-T5-Large | all | fail_on_correct_false_reject | 28.6 | 25.9 | -2.7 |
| MiniCheck-DeBERTa | closed | fail_on_correct_false_reject | 58.5 | 55.9 | -2.6 |
| AlignScore-base | all | fail_on_correct_false_reject | 19.9 | 17.8 | -2.1 |

## 7. Takeaways (provisional)

- Non-dose exclusions remove **1038** answers across **102** questions.
- `correct_suspect`: **257** (held out of v3 correct).
- **Small/paper checkers still leak** on closed unit/basis errors under v3 (3.2–19.3% PASS-on-error; /kg and /m² misses remain the story).
- **Frontier HTML judges still catch most closed auto-errors** (leak ~1.7–4.0% v3) but **false-reject on correct stays material** (closed FR ~22–23% after cleaning, down ~8–9 pp from v2).
- **Basis check almost never false-alarms on correct** (v3 closed full: 0.00% FAIL-on-correct) while still missing many basis errors (full leak ~40%).
- Main qualitative conclusions **do not reverse** after v3; largest numeric moves are **false-reject ↓** (non-dose out + correct_suspect held out) and modest **basis leak ↓**.

## Files

- `results/journal5/rd2/analysis/label_audit_v3.md`
- `results/journal5/rd2/analysis/label_v3.csv`
- `results/journal5/rd2/analysis/excluded_non_dose.csv`
- `results/journal5/rd2/analysis/excluded_non_dose_questions.csv`
- `results/journal5/rd2/analysis/correct_suspect.csv`
- `results/journal5/rd2/analysis/error_audit_sample40.csv`
- `results/journal5/rd2/analysis/label_audit_v3_rates.csv`
- `results/journal5/rd2/analysis/label_audit_v3_deltas.csv`
