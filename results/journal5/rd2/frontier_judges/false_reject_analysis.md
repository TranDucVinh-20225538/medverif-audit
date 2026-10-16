# RD2 frontier judges — false-reject analysis (v2 correct → FAIL)

**Exploratory.** HTML RAGAS-NLI judges, Slurm job **68548**, run date **2026-10-16** ICT.
False reject = `class_v2 == correct` and judge verdict `FAIL`. PARSE_FAIL excluded (not FAIL).

> Cause codes (a–f) below are **preliminary heuristics** on the 60-case sample; column `human_cause` in the CSV is blank for a human to overwrite.

## 1. Counts: false rejects by judge × mode

| judge | closed | grounded | total |
|---|---:|---:|---:|
| claude | 315 | 377 | 692 |
| gpt4o | 315 | 579 | 894 |
| deepseek | 305 | 500 | 805 |

- Unique instances with ≥1 false reject: **1076** (closed 388, grounded 688)
- All 3 judges FAIL on same v2-correct row: **536**
- Exactly 2 judges FAIL: **243**; exactly 1: **297**

## 2. By generator (any judge FAIL on v2-correct)

| generator | n |
|---|---:|
| `llama31_8b` | 228 |
| `qwen25_14b` | 210 |
| `baichuan_m2_32b` | 181 |
| `gemma3_27b` | 161 |
| `medgemma_27b` | 150 |
| `gpt4o_mini` | 146 |

## 3. By dose type (`primary_basis`)

| dose type | n |
|---|---:|
| weight_/kg | 221 |
| bsa_/m2 | 147 |
| flat | 708 |

## 4. Sample design (seed `20261016`)

- Target: **60** cases — prefer **40** all-3-FAIL + **20** single-FAIL; balance closed/grounded when pool allows.
- Drawn: all3=40, single=20, dual_fill=0; closed=30, grounded=30
- File: `false_reject_sample.csv`

## 5. Preliminary cause mix (60-case sample only)

| code | meaning | n | %% |
|---|---|---:|---:|
| **a** | judge chê thông tin thêm ngoài label (đường dùng, thời gian, cảnh báo…) | 30 | 50% |
| **b** | liều đúng nằm ngoài đoạn label bị cắt / context không đủ | 0 | 0% |
| **c** | khác cách diễn đạt/đơn vị nhưng tương đương | 4 | 7% |
| **d** | nhãn tự động sai — câu thực ra sai | 26 | 43% |
| **e** | judge sai rõ ràng | 0 | 0% |
| **f** | khác | 0 | 0% |

### Closed vs grounded in the sample

| cause | closed | grounded |
|---|---:|---:|
| a | 13 | 17 |
| b | 0 | 0 |
| c | 3 | 1 |
| d | 14 | 12 |
| e | 0 | 0 |
| f | 0 | 0 |

Suspected auto-label wrong (**d**): **26 / 60** in sample (43%).

## 6. Up to 5 example rows per cause (from the sample)

### (a) judge chê thông tin thêm ngoài label (đường dùng, thời gian, cảnh báo…) — 30 in sample

**1. `RD2_alogliptin_1__medgemma_27b__closed`** — alogliptin / closed / `medgemma_27b` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `25 mg`
- Claim: The recommended dose of alogliptin tablets is 25 mg taken orally once daily. This dose is used for improving glycemic control in adults with type 2 diabetes mellitus.
- Answer: The recommended dose of alogliptin tablets is 25 mg taken orally once daily. This dose is used for improving glycemic control in adults with type 2 diabetes mellitus.
- Excerpt (trunc): ( 2.1 ) Can be taken with or without food. ( 2.1 ) Adjust dosage if moderate or severe renal impairment or end-stage renal disease (ESRD). ( 2.2 ) Degree of Renal Impairment Creatinine Clearance (mL/min) Recommended Dosage Moderate ≥30 to <60 12.5 mg once daily Severe/ESRD <30 6.…
- Reason (claude): The context confirms that the recommended dosage of alogliptin tablets is 25 mg taken orally once daily. However, the context does not mention anything about improving glycemic control in adults with type 2 diabetes mellitus. The second part of the statement cannot be inferred from the given context.
- Prelim note: 25 mg daily OK; FAIL on indication sentence not in excerpt

**2. `RD2_cefotaxime_2__baichuan_m2_32b__closed`** — cefotaxime / closed / `baichuan_m2_32b` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `1 gram`
- Claim: The dose is 1 gram.
- Answer: The dose is 1 gram.
- Excerpt (trunc): IV Administration: The IV route is preferable for patients with bacteremia, bacterial septicemia, peritonitis, meningitis, or other severe or life-threatening infections, or for patients who may be poor risks because of lowered resistance resulting from such debilitating conditio…
- Reason (claude): The context mentions that a solution can contain "1 gram or 2 grams," indicating that 1 gram is one possible dose, but it is not stated as the definitive or only dose. The statement "The dose is 1 gram" implies it is the sole dose, which is not directly supported.
- Prelim note: judge rejects for missing indication/population/attribution or extra detail

**3. `RD2_dalbavancin_0__gemma3_27b__closed`** — dalbavancin / closed / `gemma3_27b` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `1500 mg`
- Claim: According to US prescribing information, the maximum dalbavancin dose for pediatric patients is 1500 mg. This dose is specified for patients requiring a dose greater than 10 mg/kg, and is not to exceed 1500 mg per dose.
- Answer: According to US prescribing information, the maximum dalbavancin dose for pediatric patients is 1500 mg. This dose is specified for patients requiring a dose greater than 10 mg/kg, and is not to exceed 1500 mg per dose.
- Excerpt (trunc): Adult Patients: Aseptically transfer the required dose of reconstituted dalbavancin for injection solution from the vial(s) to an intravenous bag or bottle containing 5% Dextrose Injection, USP. The diluted solution must have a final dalbavancin concentration of 1 mg/mL to 5 mg/m…
- Reason (claude): The context confirms the maximum dose for pediatric patients is 1,500 mg. However, the context does not mention anything about "patients requiring a dose greater than 10 mg/kg" — it only states the dose varies according to age and weight up to a maximum of 1,500 mg. The specific condition of "greater than 10 mg/kg" cannot be inferred from the given…
- Prelim note: judge rejects for missing indication/population/attribution or extra detail

**4. `RD2_dalbavancin_0__medgemma_27b__closed`** — dalbavancin / closed / `medgemma_27b` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `1500 mg`
- Claim: According to US prescribing information, the maximum dose of dalbavancin for injection in pediatric patients is 1500 mg. This dose is administered as a single intravenous infusion over 30 minutes.
- Answer: According to US prescribing information, the maximum dose of dalbavancin for injection in pediatric patients is 1500 mg. This dose is administered as a single intravenous infusion over 30 minutes.
- Excerpt (trunc): Adult Patients: Aseptically transfer the required dose of reconstituted dalbavancin for injection solution from the vial(s) to an intravenous bag or bottle containing 5% Dextrose Injection, USP. The diluted solution must have a final dalbavancin concentration of 1 mg/mL to 5 mg/m…
- Reason (claude): The context confirms the maximum dose of 1,500 mg for pediatric patients. However, the context does not mention anything about the infusion duration (30 minutes) or that it is administered as a single infusion. Therefore, the full statement cannot be directly inferred from the context.
- Prelim note: dose OK; judge rejects added infusion-duration detail

**5. `RD2_eculizumab_0__qwen25_14b__closed`** — eculizumab / closed / `qwen25_14b` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `900 mg`
- Claim: According to the US prescribing information for eculizumab, the dose that goes in the [DOSE] placeholder is 900 mg.
- Answer: According to the US prescribing information for eculizumab, the dose that goes in the [DOSE] placeholder is 900 mg.
- Excerpt (trunc): Table 3: Supplemental Dose of SOLIRIS with concomitant IVIg IVIg Frequency Most Recent SOLIRIS Dose Supplemental Soliris Dose per IVIg Cycle Timing of Supplemental SOLIRIS Dose Acute rescue therapy No supplemental SOLIRIS dose needed Equal to or more frequent than every 4 weeks 9…
- Reason (claude): The context does not contain any [DOSE] placeholder. The context mentions various doses (900 mg, 600 mg, 300 mg) in different scenarios, but there is no specific [DOSE] placeholder referenced that can be mapped to 900 mg specifically.
- Prelim note: dose present; FAIL on completeness/specificity

### (b) liều đúng nằm ngoài đoạn label bị cắt / context không đủ — 0 in sample

_No cases in sample._

### (c) khác cách diễn đạt/đơn vị nhưng tương đương — 4 in sample

**1. `RD2_darbepoetin_0__medgemma_27b__grounded`** — darbepoetin / grounded / `medgemma_27b` / fails=claude+deepseek+gpt4o / dose=weight_/kg

- Auto dose v2: `0.45 mcg/kg`
- Claim: According to the label excerpt, the dose is 0.45 mcg/kg intravenously or subcutaneously weekly. This is the recommended starting dose for patients with CKD not on dialysis.
- Answer: According to the label excerpt, the dose is 0.45 mcg/kg intravenously or subcutaneously weekly. This is the recommended starting dose for patients with CKD not on dialysis.
- Excerpt (trunc): - 0.45 mcg/kg intravenously or subcutaneously weekly, or - 0.75 mcg/kg intravenously or subcutaneously every 2 weeks - Intravenous route is recommended for patients on hemodialysis Recommended starting dose for patients with CKD not on dialysis ( 2.2 ): - 0.45 mcg/kg intravenousl…
- Reason (claude): The context states that the recommended starting dose for patients with CKD not on dialysis is 0.45 mcg/kg intravenously or subcutaneously at 4 week intervals, not weekly. The weekly dosing of 0.45 mcg/kg is listed as a general option (and for pediatric patients), but not specifically as the recommended starting dose for CKD patients not on dialysi…
- Prelim note: wording/unit equivalence dispute

**2. `RD2_cefadroxil_2__qwen25_14b__closed`** — cefadroxil / closed / `qwen25_14b` / fails=deepseek / dose=flat

- Auto dose v2: `1 gram`
- Claim: According to the US prescribing information for cefadroxil, the initial dose for adults is 1 gram of cefadroxil monohydrate.
- Answer: According to the US prescribing information for cefadroxil, the initial dose for adults is 1 gram of cefadroxil monohydrate.
- Excerpt (trunc): In the treatment of beta-hemolytic streptococcal infections, a therapeutic dosage of cefadroxil monohydrate should be administered for at least 10 days. Renal Impairment In patients with renal impairment, the dosage of cefadroxil monohydrate should be adjusted according to creati…
- Reason (deepseek): The context mentions that the initial dose for adults is 1000 mg of cefadroxil monohydrate, which is equivalent to 1 gram. However, the context does not specify that this information is from the US prescribing information.
- Prelim note: 1 gram ≡ 1000 mg; FAIL mainly on ‘US PI’ attribution

**3. `RD2_gemcitabine_0__qwen25_14b__closed`** — gemcitabine / closed / `qwen25_14b` / fails=gpt4o / dose=bsa_/m2

- Auto dose v2: `1000 mg/m2`
- Claim: According to the US prescribing information for gemcitabine, the dose that goes in [DOSE] is 1000 mg/m² over 30 minutes on Days 1 and 8 of each 21-day cycle.
- Answer: According to the US prescribing information for gemcitabine, the dose that goes in [DOSE] is 1000 mg/m² over 30 minutes on Days 1 and 8 of each 21-day cycle.
- Excerpt (trunc): 2 DOSAGE AND ADMINISTRATION AVGEMSI is for intravenous use only. Ovarian Cancer: 1,000 mg/m2 over 30 minutes on Days 1 and 8 of each 21-day cycle. ( 2.1 ) Breast Cancer: 1,250 mg/m2 over 30 minutes on Days 1 and 8 of each 21-day cycle. ( 2.2 ) Non-Small Cell Lung Cancer: 1,000 mg…
- Reason (gpt4o): The context provides the dosage of AVGEMSI for ovarian cancer as 1,000 mg/m² over 30 minutes on Days 1 and 8 of each 21-day cycle, which matches the statement. However, the statement refers to gemcitabine, and the context does not explicitly mention gemcitabine, only AVGEMSI.
- Prelim note: dose matches; judge quibble on drug name/context

**4. `RD2_gemcitabine_2__qwen25_14b__closed`** — gemcitabine / closed / `qwen25_14b` / fails=deepseek / dose=bsa_/m2

- Auto dose v2: `1250 mg/m2`
- Claim: According to the US prescribing information for gemcitabine, the recommended dose that goes in [DOSE] is 1250 mg/m².
- Answer: According to the US prescribing information for gemcitabine, the recommended dose that goes in [DOSE] is 1250 mg/m².
- Excerpt (trunc): 2.2 Breast Cancer Recommended Dose and Schedule The recommended dosage of AVGEMSI is 1,250 mg/m2 intravenously over 30 minutes on Days 1 and 8 of each 21-day cycle in combination with paclitaxel 175 mg/m2 on Day 1 before AVGEMSI administration. Refer to paclitaxel prescribing inf…
- Reason (deepseek): The context specifies the recommended dosage of AVGEMSI as 1,250 mg/m², but it does not explicitly mention gemcitabine or confirm that this dosage applies to gemcitabine.
- Prelim note: AVGEMSI vs gemcitabine naming; dose amount matches

### (d) nhãn tự động sai — câu thực ra sai — 26 in sample

**1. `RD2_atovaquone_0__baichuan_m2_32b__closed`** — atovaquone / closed / `baichuan_m2_32b` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `750 mg`
- Claim: The recommended oral dosage is 750 mg (1 tablet) twice daily (total daily dose = 1500 mg) administered with food for 21 days.
- Answer: The recommended oral dosage is 750 mg (1 tablet) twice daily (total daily dose = 1500 mg) administered with food for 21 days.
- Excerpt (trunc): 1,500 mg (10 mL) once daily with food. (2.1) Treatment of PCP: 750 mg (5 mL) twice daily with food for 21 days. (2.2) Supplied in Bottles: º Bottle: Shake bottle gently before use. (2.3) 2.1 Dosage for the Prevention of P. jirovecii Pneumonia The recommended oral dosage is 1,500 …
- Reason (claude): The context states the recommended oral dosage for treatment is 750 mg (5 mL) twice daily for 21 days, but the statement says "1 tablet" instead of "5 mL." The formulation is an oral suspension measured in mL, not tablets, so "1 tablet" is incorrect and not supported by the context.
- Prelim note: says 1 tablet; label is 5 mL suspension

**2. `RD2_chloroquine_0__gpt4o_mini__closed`** — chloroquine / closed / `gpt4o_mini` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `1,000 mg`
- Claim: The initial double (loading) dose of chloroquine for adults is 1,000 mg (base).
- Answer: The initial double (loading) dose of chloroquine for adults is 1,000 mg (base).
- Excerpt (trunc): Pediatric Dose : The dosage for prophylaxis is 5 mg calculated as base, per kg of body weight, administered once per week on exactly the same day of each week. The pediatric dose should never exceed the adult dose regardless of weight. If circumstances permit, suppressive therapy…
- Reason (claude): The context states the initial double (loading) dose for adults is 1 g (= 600 mg base), not 1,000 mg base. The 1 g refers to the salt form, which equals 600 mg base.
- Prelim note: 1,000 mg base vs label 1 g (=600 mg base) — answer wrong

**3. `RD2_chloroquine_0__qwen25_14b__closed`** — chloroquine / closed / `qwen25_14b` / fails=claude+deepseek+gpt4o / dose=flat

- Auto dose v2: `1000 mg`
- Claim: According to the US prescribing information for chloroquine, the initial double (loading) dose mentioned is 1000 mg (= 500 mg base), or in children, 10 mg base/kg may be taken in two divided doses, six hours apart.
- Answer: According to the US prescribing information for chloroquine, the initial double (loading) dose mentioned is 1000 mg (= 500 mg base), or in children, 10 mg base/kg may be taken in two divided doses, six hours apart.
- Excerpt (trunc): Pediatric Dose : The dosage for prophylaxis is 5 mg calculated as base, per kg of body weight, administered once per week on exactly the same day of each week. The pediatric dose should never exceed the adult dose regardless of weight. If circumstances permit, suppressive therapy…
- Reason (claude): The context states the initial double (loading) dose is 1 g (= 600 mg base), not 1000 mg (= 500 mg base). The statement incorrectly converts 1 g to 500 mg base when the context clearly states it equals 600 mg base.
- Prelim note: 1000 mg (=500 mg base) vs label 1 g (=600 mg base)

**4. `RD2_cidofovir_0__medgemma_27b__closed`** — cidofovir / closed / `medgemma_27b` / fails=claude+deepseek+gpt4o / dose=weight_/kg

- Auto dose v2: `5 mg/kg`
- Claim: According to US prescribing information, the maintenance dose of cidofovir injection must be reduced from 5 mg/kg to 2.5 mg/kg for an increase in serum creatinine of 0.3 mg/dL above baseline.
- Answer: According to US prescribing information, the maintenance dose of cidofovir injection must be reduced from 5 mg/kg to 2.5 mg/kg for an increase in serum creatinine of 0.3 mg/dL above baseline.
- Excerpt (trunc): 0.85 Creatinine clearance for females = -------------------------------------------------------------- 72 × [serum creatinine (mg/dL)] Maintenance Treatment The recommended maintenance dose of cidofovir injection is 5 mg/kg body weight (given as an intravenous infusion at a const…
- Reason (claude): The context states the dose must be reduced from 5 mg/kg to 3 mg/kg (not 2.5 mg/kg) for an increase in serum creatinine of 0.3 to 0.4 mg/dL above baseline.
- Prelim note: judge cites factual mismatch vs excerpt — auto “correct” likely wrong

**5. `RD2_doxorubicin_1__qwen25_14b__closed`** — doxorubicin / closed / `qwen25_14b` / fails=claude+deepseek+gpt4o / dose=bsa_/m2

- Auto dose v2: `50 to 75 mg/m2`
- Claim: According to the US prescribing information for doxorubicin, the recommended dosage when used as a single agent is 50 to 75 mg/m² intravenously every 21 days. Therefore, [DOSE] would be 50 mg/m².
- Answer: According to the US prescribing information for doxorubicin, the recommended dosage when used as a single agent is 50 to 75 mg/m² intravenously every 21 days. Therefore, [DOSE] would be 50 mg/m².
- Excerpt (trunc): 2.1 Recommended Dosage for Adjuvant Breast Cancer The recommended dosage of doxorubicin hydrochloride for injection is 60 mg/m2 administered as an intravenous bolus on day 1 of each 21-day treatment cycle, in combination with cyclophosphamide, for a total of four cycles. 2.2 Reco…
- Reason (claude): The context states the recommended dosage as a single agent is 60 mg/m2 to 75 mg/m2, not 50 to 75 mg/m2. The statement incorrectly identifies the lower bound as 50 mg/m² instead of 60 mg/m².
- Prelim note: answer 50–75 mg/m²; label single-agent 60–75 mg/m²

### (e) judge sai rõ ràng — 0 in sample

_No cases in sample._

### (f) khác — 0 in sample

_No cases in sample._

## Caveats

- Causes are **machine-assisted preliminary** labels, not adjudicated.
- Prompt text was not stored in judge jsonl (`prompt` field is the slug); evidence/claim come from `instances.jsonl`.
- Question text from `questions.jsonl`; answer text from `answers.jsonl`.
