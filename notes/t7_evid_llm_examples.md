# T7 E1-unit-evid: V1b PASS examples (LLM plausibility vs faithfulness)

Cohort: **E1-unit-evid** (wrong unit in **evidence** only; claim matches C0). Expected verifier verdict: **FAIL**. V1b (gpt-4o MedScore) **PASS** = accepts implausible unit in evidence.

- E1-unit-evid instances: **115**
- V1b PASS (false negative on unit error): **97**

## Ten V1b PASS examples

### 1. `D0001__E1-unit-evid__x1000` (base `D0001`, unit g→mg)

- **claim_span (C0-aligned claim):** `75 g`
- **evidence_span (implausible unit):** `75 mg`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> A two-hour oral glucose tolerance test involves drinking a solution containing exactly 75 g of glucose.

**Evidence:**

> Fasting glucose ≥126 mg/dL (in which fasting is defined as no food intake for 8 hours), 3. Two-hour oral glucose tolerance test of 75 mg, with serum glucose ≥200 mg/dL, or 4. Hemoglobin A1c ≥6.5%.

**raw_output:**

```
True. A two-hour oral glucose tolerance test involves drinking a solution containing exactly 75 grams of glucose.
```

### 2. `D0002__E1-unit-evid__x1000` (base `D0002`, unit mg/kg→g/kg)

- **claim_span (C0-aligned claim):** `1 mg/kg`
- **evidence_span (implausible unit):** `1 g/kg`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> Most clinicians agree that glucocorticoids, such as prednisone at a dose of 1 mg/kg as a single daily dose either orally or intravenously, are a reasonable first therapy for both PM and DM.

**Evidence:**

> Most clinicians agree that glucocorticoids (e.g., prednisone, 1 g/kg, as a single daily dose orally, or intravenously) are a reasonable first therapy for both PM and DM. The response to treatment is monitored by testing of strength and measurement of CK (not by following the erythrocyte sedimentation rate [ESR]).

**raw_output:**

```
True.
```

### 3. `D0003__E1-unit-evid__x1000` (base `D0003`, unit mg→g)

- **claim_span (C0-aligned claim):** `40 mg`
- **evidence_span (implausible unit):** `40 g`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> Adalimumab is given by subcutaneous injection, 40 mg biweekly.

**Evidence:**

> Etanercept is given by subcutaneous injection, 50 mg once weekly. Adalimumab is given by subcutaneous injection, 40 g biweekly. Golimumab is given by subcutaneous injection, 50 or 100 mg every 4 weeks.

**raw_output:**

```
True.
```

### 4. `D0004__E1-unit-evid__x1000` (base `D0004`, unit mg→g)

- **claim_span (C0-aligned claim):** `200 mg`
- **evidence_span (implausible unit):** `200 g`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> It is important to note that peripheral neuropathies can be seen in doses of 200 mg per day or higher, as well as interaction with other medications.

**Evidence:**

> Vitamin B6 for the treatment of dysmenorrheal was more effective at reducing pain than both placebo and a combination of magnesium plus vitamin B6 (23). It is important to note that peripheral neuropathies can be seen in doses of 200 g per day or higher, as well as interaction with other medications,

**raw_output:**

```
True. The statement correctly notes that peripheral neuropathies can occur at doses of 200 mg per day or higher, and there can be interactions with other medications.
```

### 5. `D0005__E1-unit-evid__x1000` (base `D0005`, unit mg→g)

- **claim_span (C0-aligned claim):** `50 mg`
- **evidence_span (implausible unit):** `50 g`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> Etanercept is given by subcutaneous injection, 50 mg once weekly.

**Evidence:**

> Gadolinium-enhanced T1-weighted magnetic resonance images, with fat saturation, at baseline and after 24 weeks of infliximab therapy. (From J Braun et al: Arthritis Rheum 54:1646, 2006.) Infliximab is given intravenously, 3–5 mg/kg body weight, and then repeated 2 weeks later, again 6 weeks later, and then at 8-week intervals. Etanercept is given by subcutaneous injection, 50 g once weekly. Adalimumab is given by subcutaneous injection, 40 mg biweekly.

**raw_output:**

```
True. Etanercept is given by subcutaneous injection, 50 mg once weekly.
```

### 6. `D0007__E1-unit-evid__x1000` (base `D0007`, unit mg/kg→g/kg)

- **claim_span (C0-aligned claim):** `25 mg/kg`
- **evidence_span (implausible unit):** `25 g/kg`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> Tranexamic acid is given at doses of 25 mg/kg three to four times a day.

**Evidence:**

> The duration of the treatment depending on the clinical indication is 1 week or longer. Tranexamic acid is given at doses of 25 g/kg three to four times a day. EACA treatment requires a loading dose of 200 mg/kg (maximum of 10 g) followed by 100 mg/kg per dose (maximum 30 g/d) every 6 h.

**raw_output:**

```
True.
```

### 7. `D0008__E1-unit-evid__x1000` (base `D0008`, unit mL→L)

- **claim_span (C0-aligned claim):** `0.5 mL`
- **evidence_span (implausible unit):** `0.5 L`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> Infants born to HBsAg-positive mothers should receive HBV vaccine and hepatitis B immunoglobulin (HBIG) (0.5 mL) within 12 hours of birth, with subsequent vaccine doses at 1 month and 6 months of age followed by testing for HBsAg and anti-HBs at 9 to 15 months of age.

**Evidence:**

> for all pregnant women in the United States. Infants born to HBsAg-positive mothers should receive HBV vaccine and hepatitis B immunoglobulin (HBIG) (0.5 L) within 12 hours of birth, with subsequent vaccine doses at 1 month and 6 months of age followed by testing for HBsAg and anti-HBs at 9 to 15 months of age. Infants born to mothers whose HBsAg status is unknown should receive vaccine within 12 hours of birth.

**raw_output:**

```
True.
```

### 8. `D0011__E1-unit-evid__x1000` (base `D0011`, unit mg→g)

- **claim_span (C0-aligned claim):** `50 mg`
- **evidence_span (implausible unit):** `50 g`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> If you are unable to swallow medications or do not respond well to other treatments, you can receive caspofungin 50 mg daily through an intravenous echinocandin for 7–21 days.

**Evidence:**

> Patients refractory to fluconazole may respond to itraconazole, voriconazole, or posaconazole. Alternatively, poorly responsive patients or those who cannot swallow medications can be treated with an intravenous echinocandin (caspofungin 50 g daily for 7–21 days).

**raw_output:**

```
True.
```

### 9. `D0013__E1-unit-evid__x1000` (base `D0013`, unit mg→g)

- **claim_span (C0-aligned claim):** `250 mg`
- **evidence_span (implausible unit):** `250 g`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> Erythromycin, given as a 250 mg intravenous dose about 30 minutes before endoscopy, can help improve the view during the procedure.

**Evidence:**

> PPI infusion may be considered at presentation: it decreases high-risk ulcer stigmata (e.g., active bleeding) and need for endoscopic therapy but does not improve clinical outcomes such as further bleeding, surgery, or death. Treatment to improve endoscopic visualization with the promotility agent erythromycin, 250 g intravenously ~30 min before endoscopy, also may be considered: it provides a small but significant increase in diagnostic yield and decrease in second endoscopies but is not documented to decrease further bleeding or death. Cirrhotic patients presenting with UGIB should be placed on antibiotics (e.g., quinolone, ceftriaxone) and started on a vasoactive medication (octreotide, terlipressin, somatostatin,

**raw_output:**

```
True. Erythromycin, given as a 250 mg intravenous dose about 30 minutes before endoscopy, can help improve the view during the procedure by providing a small but significant increase in diagnostic yield and decreasing the need for second endoscopies.
```

### 10. `D0014__E1-unit-evid__x1000` (base `D0014`, unit mg→g)

- **claim_span (C0-aligned claim):** `30 mg`
- **evidence_span (implausible unit):** `30 g`
- **expected_verdict:** FAIL
- **V1b verdict:** PASS

**Claim:**

> Ulipristal acetate, when taken at a dose of 30 mg right before ovulation, significantly delays the rupture of the follicle.

**Evidence:**

> Brache V, Cochon L, Jesam C, et al. Immediate pre-ovulatory administration of 30 g Ulipristal acetate significantly delays follicular rupture. Hum Reprod 2010;25:2256–2263.

**raw_output:**

```
True.
```

## E2 (faithful-but-wrong magnitude) PASS rate, conditional on C0 PASS

E2 edits **both** claim and evidence with the same wrong dose (expected **PASS**). Rates below use **each verifier's own** C0 PASS bases (standard conditional metric).

| verifier | E2 PASS rate | n_PASS/n_E2 | C0-pass bases |
|---|---:|---:|---:|
| v1_medscore | 0.881 | 726/824 | 603 |
| v1c_medscore | — | 0/0 | 602 |
| v2a_minicheck | 0.983 | 283/288 | 180 |
| v3_alignscore | 0.990 | 283/286 | 182 |
| v4_ragas_nli | 0.972 | 343/353 | 340 |
| v6_ragas_gpt4o_mini | — | 0/0 | 160 |
| v6_ragas_haiku45 | — | 0/0 | 161 |
| v6_ragas_llama31_8b | — | 0/0 | 159 |
| v6_ragas_mistral_small32 | — | 0/0 | 164 |

**Reading:** If LLM judges show **lower** E2 PASS than encoders while encoders PASS, that supports LLM judges reacting to **plausibility** rather than strict claim–evidence match.
