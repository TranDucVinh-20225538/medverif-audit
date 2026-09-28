# QC samples

Random sample, seed 42, up to 2 items for each of DOSE/POLARITY × C0, E1-evid, E1-claim, E2, INV-claim. DOSE edits prefer one `x2` and one `x10` when both exist. Changed spans are marked with « ». Sampled 20 instances from 1695.
### D0138__C0__none

- type: `DOSE`
- condition: `C0`
- magnitude: `none`
- expected faithfulness verdict: `PASS`
- base_id: `D0138`

Highlighted diff (`« »` marks the span)

```
claim span: The goal for older children is to receive 0.8 to «2 g» of protein per kilogram of body weight each day.
edit distance: 0
```

Evidence before

```
Protein delivery in PN is via amino acids in the dextrose solution. The goal is 0.8 to 2 g protein/kg/24 hr for older children, 1.5 to 3 g/kg/24 hr for full-term and older infants, and 2.5 to 3.5 g/kg/24 hr for preterm infants.
```

Evidence after

```
Protein delivery in PN is via amino acids in the dextrose solution. The goal is 0.8 to 2 g protein/kg/24 hr for older children, 1.5 to 3 g/kg/24 hr for full-term and older infants, and 2.5 to 3.5 g/kg/24 hr for preterm infants.
```

Claim before

```
The goal for older children is to receive 0.8 to 2 g of protein per kilogram of body weight each day.
```

Claim after

```
The goal for older children is to receive 0.8 to 2 g of protein per kilogram of body weight each day.
```

### D0054__C0__none

- type: `DOSE`
- condition: `C0`
- magnitude: `none`
- expected faithfulness verdict: `PASS`
- base_id: `D0054`

Highlighted diff (`« »` marks the span)

```
claim span: Some patients have found relief with medications such as gabapentin, with doses up to «2100 mg».
edit distance: 0
```

Evidence before

```
The use of drugs in treating this movement disorder has met with variable success. Clonazepam (0.25 to 0.5 mg/d, increasing gradually to 3.0 to 6.0 mg/d), sodium valproate (250 mg/d, increasing to 1000 mg/d), and gabapentin (up to 2100 mg) have suppressed the movement in some cases, particularly the last of these drugs, which reportedly has had a dramatic effect in some patients. Also, tetrabenazine and haloperidol have been helpful on occasion.
```

Evidence after

```
The use of drugs in treating this movement disorder has met with variable success. Clonazepam (0.25 to 0.5 mg/d, increasing gradually to 3.0 to 6.0 mg/d), sodium valproate (250 mg/d, increasing to 1000 mg/d), and gabapentin (up to 2100 mg) have suppressed the movement in some cases, particularly the last of these drugs, which reportedly has had a dramatic effect in some patients. Also, tetrabenazine and haloperidol have been helpful on occasion.
```

Claim before

```
Some patients have found relief with medications such as gabapentin, with doses up to 2100 mg.
```

Claim after

```
Some patients have found relief with medications such as gabapentin, with doses up to 2100 mg.
```

### D0015__E1-evid__x2

- type: `DOSE`
- condition: `E1-evid`
- magnitude: `x2`
- expected faithfulness verdict: `FAIL`
- base_id: `D0015`

Highlighted diff (`« »` marks the span)

```
evidence before: This compound, a potent steroid with both glucocorticoid and mineralocorticoid activity, is the most widely used mineralocorticoid. Oral doses of «0.1 mg» two to seven times weekly have potent salt-retaining activity and are used in the treatment of adrenocortical insufficiency associated with mineralocorticoid deficiency. These dosages are too small to have important anti-inflammatory or antigrowth effects.
evidence after: This compound, a potent steroid with both glucocorticoid and mineralocorticoid activity, is the most widely used mineralocorticoid. Oral doses of «0.2 mg» two to seven times weekly have potent salt-retaining activity and are used in the treatment of adrenocortical insufficiency associated with mineralocorticoid deficiency. These dosages are too small to have important anti-inflammatory or antigrowth effects.
evidence edit distance: 1
evidence confined to span: True
claim unchanged
```

Evidence before

```
This compound, a potent steroid with both glucocorticoid and mineralocorticoid activity, is the most widely used mineralocorticoid. Oral doses of 0.1 mg two to seven times weekly have potent salt-retaining activity and are used in the treatment of adrenocortical insufficiency associated with mineralocorticoid deficiency. These dosages are too small to have important anti-inflammatory or antigrowth effects.
```

Evidence after

```
This compound, a potent steroid with both glucocorticoid and mineralocorticoid activity, is the most widely used mineralocorticoid. Oral doses of 0.2 mg two to seven times weekly have potent salt-retaining activity and are used in the treatment of adrenocortical insufficiency associated with mineralocorticoid deficiency. These dosages are too small to have important anti-inflammatory or antigrowth effects.
```

Claim before

```
Oral doses of 0.1 mg two to seven times weekly can help retain salt and are used to treat adrenocortical insufficiency related to mineralocorticoid deficiency.
```

Claim after

```
Oral doses of 0.1 mg two to seven times weekly can help retain salt and are used to treat adrenocortical insufficiency related to mineralocorticoid deficiency.
```

### D0023__E1-evid__x10

- type: `DOSE`
- condition: `E1-evid`
- magnitude: `x10`
- expected faithfulness verdict: `FAIL`
- base_id: `D0023`

Highlighted diff (`« »` marks the span)

```
evidence before: Failure of aldosterone to suppress below 140 pmol/L (5 ng/dL) is indicative of autonomous mineralocorticoid excess. Alternative tests are the oral sodium loading test (300 mmol NaCl/d for 3 days) or the fludrocortisone suppression test («0.1 mg» q6h with 30 mmol NaCl q8h for 4 days); the latter can be difficult because of the risk of profound hypokalemia and increased hypertension. In patients with overt hypokalemic hypertension, strongly positive ARR, and concurrently increased aldosterone levels, confirmatory testing is usually not necessary.
evidence after: Failure of aldosterone to suppress below 140 pmol/L (5 ng/dL) is indicative of autonomous mineralocorticoid excess. Alternative tests are the oral sodium loading test (300 mmol NaCl/d for 3 days) or the fludrocortisone suppression test («1 mg» q6h with 30 mmol NaCl q8h for 4 days); the latter can be difficult because of the risk of profound hypokalemia and increased hypertension. In patients with overt hypokalemic hypertension, strongly positive ARR, and concurrently increased aldosterone levels, confirmatory testing is usually not necessary.
evidence edit distance: 2
evidence confined to span: True
claim unchanged
```

Evidence before

```
Failure of aldosterone to suppress below 140 pmol/L (5 ng/dL) is indicative of autonomous mineralocorticoid excess. Alternative tests are the oral sodium loading test (300 mmol NaCl/d for 3 days) or the fludrocortisone suppression test (0.1 mg q6h with 30 mmol NaCl q8h for 4 days); the latter can be difficult because of the risk of profound hypokalemia and increased hypertension. In patients with overt hypokalemic hypertension, strongly positive ARR, and concurrently increased aldosterone levels, confirmatory testing is usually not necessary.
```

Evidence after

```
Failure of aldosterone to suppress below 140 pmol/L (5 ng/dL) is indicative of autonomous mineralocorticoid excess. Alternative tests are the oral sodium loading test (300 mmol NaCl/d for 3 days) or the fludrocortisone suppression test (1 mg q6h with 30 mmol NaCl q8h for 4 days); the latter can be difficult because of the risk of profound hypokalemia and increased hypertension. In patients with overt hypokalemic hypertension, strongly positive ARR, and concurrently increased aldosterone levels, confirmatory testing is usually not necessary.
```

Claim before

```
The fludrocortisone suppression test involves taking 0.1 mg every 6 hours.
```

Claim after

```
The fludrocortisone suppression test involves taking 0.1 mg every 6 hours.
```

### D0044__E1-claim__x2

- type: `DOSE`
- condition: `E1-claim`
- magnitude: `x2`
- expected faithfulness verdict: `FAIL`
- base_id: `D0044`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: The drug is given under the skin in amounts starting at «50 μg», several times a day, with the dose adjusted based on how you respond.
claim after: The drug is given under the skin in amounts starting at «100 μg», several times a day, with the dose adjusted based on how you respond.
claim edit distance: 2
claim confined to span: True
```

Evidence before

```
The somatostatin analogue octreotide has been successful in diet-refractory cases. This drug is administered subcutaneously (50 μg tid), titrated according to clinical response. A long-acting depot formulation of octreotide can be administered once every 28 days and provides symptom relief comparable to the short-acting agent.
```

Evidence after

```
The somatostatin analogue octreotide has been successful in diet-refractory cases. This drug is administered subcutaneously (50 μg tid), titrated according to clinical response. A long-acting depot formulation of octreotide can be administered once every 28 days and provides symptom relief comparable to the short-acting agent.
```

Claim before

```
The drug is given under the skin in amounts starting at 50 μg, several times a day, with the dose adjusted based on how you respond.
```

Claim after

```
The drug is given under the skin in amounts starting at 100 μg, several times a day, with the dose adjusted based on how you respond.
```

### D0043__E1-claim__x10

- type: `DOSE`
- condition: `E1-claim`
- magnitude: `x10`
- expected faithfulness verdict: `FAIL`
- base_id: `D0043`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: Adults taking a medication, such as glucocorticoids in a daily dose ≥«5 mg» prednisone or equivalent for ≥3 months, may be at risk for low bone mass or bone loss.
claim after: Adults taking a medication, such as glucocorticoids in a daily dose ≥«50 mg» prednisone or equivalent for ≥3 months, may be at risk for low bone mass or bone loss.
claim edit distance: 1
claim confined to span: True
```

Evidence before

```
Adults with a condition (e.g., rheumatoid arthritis) or taking a medication (e.g., glucocorticoids in a daily dose ≥5 mg prednisone or equivalent for ≥3 months) associated with low bone mass or bone loss Source: From the 2014 National Osteoporosis Foundation Clinician’s Guide to the Prevention and Treatment of Osteoporosis. © National Osteoporosis Foundation. 2494 fracture over a 5or 10-year period.
```

Evidence after

```
Adults with a condition (e.g., rheumatoid arthritis) or taking a medication (e.g., glucocorticoids in a daily dose ≥5 mg prednisone or equivalent for ≥3 months) associated with low bone mass or bone loss Source: From the 2014 National Osteoporosis Foundation Clinician’s Guide to the Prevention and Treatment of Osteoporosis. © National Osteoporosis Foundation. 2494 fracture over a 5or 10-year period.
```

Claim before

```
Adults taking a medication, such as glucocorticoids in a daily dose ≥5 mg prednisone or equivalent for ≥3 months, may be at risk for low bone mass or bone loss.
```

Claim after

```
Adults taking a medication, such as glucocorticoids in a daily dose ≥50 mg prednisone or equivalent for ≥3 months, may be at risk for low bone mass or bone loss.
```

### D0176__E2__x2

- type: `DOSE`
- condition: `E2`
- magnitude: `x2`
- expected faithfulness verdict: `PASS`
- base_id: `D0176`

Highlighted diff (`« »` marks the span)

```
evidence before: A corollary of this idea is that supplementation of diet with fish oils might protect against atherosclerosis. One study of Dutch men whose usual daily diet contained «30 g» of fish showed a substantially lower frequency of death from coronary heart disease than that among comparable control subjects. However, other studies have shown that omega-3 fatty acid supplements do not reduce the risk of cardiovascular diseases, suggesting that yet unknown components of fish may be required for cardioprotection.
evidence after: A corollary of this idea is that supplementation of diet with fish oils might protect against atherosclerosis. One study of Dutch men whose usual daily diet contained «60 g» of fish showed a substantially lower frequency of death from coronary heart disease than that among comparable control subjects. However, other studies have shown that omega-3 fatty acid supplements do not reduce the risk of cardiovascular diseases, suggesting that yet unknown components of fish may be required for cardioprotection.
evidence edit distance: 1
evidence confined to span: True
claim before: One study found that Dutch men who regularly consumed «30 g» of fish in their daily diet had a lower frequency of death from coronary heart disease compared to similar individuals who did not.
claim after: One study found that Dutch men who regularly consumed «60 g» of fish in their daily diet had a lower frequency of death from coronary heart disease compared to similar individuals who did not.
claim edit distance: 1
claim confined to span: True
```

Evidence before

```
A corollary of this idea is that supplementation of diet with fish oils might protect against atherosclerosis. One study of Dutch men whose usual daily diet contained 30 g of fish showed a substantially lower frequency of death from coronary heart disease than that among comparable control subjects. However, other studies have shown that omega-3 fatty acid supplements do not reduce the risk of cardiovascular diseases, suggesting that yet unknown components of fish may be required for cardioprotection.
```

Evidence after

```
A corollary of this idea is that supplementation of diet with fish oils might protect against atherosclerosis. One study of Dutch men whose usual daily diet contained 60 g of fish showed a substantially lower frequency of death from coronary heart disease than that among comparable control subjects. However, other studies have shown that omega-3 fatty acid supplements do not reduce the risk of cardiovascular diseases, suggesting that yet unknown components of fish may be required for cardioprotection.
```

Claim before

```
One study found that Dutch men who regularly consumed 30 g of fish in their daily diet had a lower frequency of death from coronary heart disease compared to similar individuals who did not.
```

Claim after

```
One study found that Dutch men who regularly consumed 60 g of fish in their daily diet had a lower frequency of death from coronary heart disease compared to similar individuals who did not.
```

### D0112__E2__x10

- type: `DOSE`
- condition: `E2`
- magnitude: `x10`
- expected faithfulness verdict: `PASS`
- base_id: `D0112`

Highlighted diff (`« »` marks the span)

```
evidence before: Friedman and colleagues (2008, 2009) conducted a prospective multicenter trial of pregnancies with anti-SSA/Ro antibodies the PR Interval and Dexamethasone (PRIDE) study. Weekly sonographic surveillance was performed, and heart block was treated with maternal oral dexamethasone «4 mg» daily. Unfortu nately, progression from second-to third-degree block was not prevented with maternal dexamethasone therapy, and third degree atrioventricular block was irreversible.
evidence after: Friedman and colleagues (2008, 2009) conducted a prospective multicenter trial of pregnancies with anti-SSA/Ro antibodies the PR Interval and Dexamethasone (PRIDE) study. Weekly sonographic surveillance was performed, and heart block was treated with maternal oral dexamethasone «40 mg» daily. Unfortu nately, progression from second-to third-degree block was not prevented with maternal dexamethasone therapy, and third degree atrioventricular block was irreversible.
evidence edit distance: 1
evidence confined to span: True
claim before: Heart block was treated with maternal oral dexamethasone «4 mg» daily.
claim after: Heart block was treated with maternal oral dexamethasone «40 mg» daily.
claim edit distance: 1
claim confined to span: True
```

Evidence before

```
Friedman and colleagues (2008, 2009) conducted a prospective multicenter trial of pregnancies with anti-SSA/Ro antibodies the PR Interval and Dexamethasone (PRIDE) study. Weekly sonographic surveillance was performed, and heart block was treated with maternal oral dexamethasone 4 mg daily. Unfortu nately, progression from second-to third-degree block was not prevented with maternal dexamethasone therapy, and third degree atrioventricular block was irreversible.
```

Evidence after

```
Friedman and colleagues (2008, 2009) conducted a prospective multicenter trial of pregnancies with anti-SSA/Ro antibodies the PR Interval and Dexamethasone (PRIDE) study. Weekly sonographic surveillance was performed, and heart block was treated with maternal oral dexamethasone 40 mg daily. Unfortu nately, progression from second-to third-degree block was not prevented with maternal dexamethasone therapy, and third degree atrioventricular block was irreversible.
```

Claim before

```
Heart block was treated with maternal oral dexamethasone 4 mg daily.
```

Claim after

```
Heart block was treated with maternal oral dexamethasone 40 mg daily.
```

### D0007__INV-claim__unit_conversion

- type: `DOSE`
- condition: `INV-claim`
- magnitude: `unit_conversion`
- expected faithfulness verdict: `PASS`
- base_id: `D0007`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: Tranexamic acid is given at doses of «25 mg/kg» three to four times a day.
claim after: Tranexamic acid is given at doses of «0.025 g/kg» three to four times a day.
claim edit distance: 4
claim confined to span: True
```

Evidence before

```
The duration of the treatment depending on the clinical indication is 1 week or longer. Tranexamic acid is given at doses of 25 mg/kg three to four times a day. EACA treatment requires a loading dose of 200 mg/kg (maximum of 10 g) followed by 100 mg/kg per dose (maximum 30 g/d) every 6 h.
```

Evidence after

```
The duration of the treatment depending on the clinical indication is 1 week or longer. Tranexamic acid is given at doses of 25 mg/kg three to four times a day. EACA treatment requires a loading dose of 200 mg/kg (maximum of 10 g) followed by 100 mg/kg per dose (maximum 30 g/d) every 6 h.
```

Claim before

```
Tranexamic acid is given at doses of 25 mg/kg three to four times a day.
```

Claim after

```
Tranexamic acid is given at doses of 0.025 g/kg three to four times a day.
```

### D0082__INV-claim__unit_conversion

- type: `DOSE`
- condition: `INV-claim`
- magnitude: `unit_conversion`
- expected faithfulness verdict: `PASS`
- base_id: `D0082`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: If needed, the dosage can be increased to «1.8 mg» daily.
claim after: If needed, the dosage can be increased to «0.0018 g» daily.
claim edit distance: 5
claim confined to span: True
```

Evidence before

```
Treatment is initiated at 0.6 mg and increased after 1 week to 1.2 mg daily. If needed the dosage can be increased to 1.8 mg daily. In clinical trials liraglutide results in a reduction of HbA1c of 0.8–1.5%; weight loss ranges from none to 3.2 kg.
```

Evidence after

```
Treatment is initiated at 0.6 mg and increased after 1 week to 1.2 mg daily. If needed the dosage can be increased to 1.8 mg daily. In clinical trials liraglutide results in a reduction of HbA1c of 0.8–1.5%; weight loss ranges from none to 3.2 kg.
```

Claim before

```
If needed, the dosage can be increased to 1.8 mg daily.
```

Claim after

```
If needed, the dosage can be increased to 0.0018 g daily.
```

### P0033__C0__none

- type: `POLARITY`
- condition: `C0`
- magnitude: `none`
- expected faithfulness verdict: `PASS`
- base_id: `P0033`

Highlighted diff (`« »` marks the span)

```
claim span: Rabies vaccine «is recommended for» long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas.
edit distance: 0
```

Evidence before

```
The two vaccines available in the United States provide >90% protection. Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas; however, in a large-scale study, almost 50% of potential exposures occurred within the first month of travel. Even after receipt of a preexposure rabies vaccine series, two postexposure doses are required.
```

Evidence after

```
The two vaccines available in the United States provide >90% protection. Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas; however, in a large-scale study, almost 50% of potential exposures occurred within the first month of travel. Even after receipt of a preexposure rabies vaccine series, two postexposure doses are required.
```

Claim before

```
Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas.
```

Claim after

```
Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas.
```

### P0144__C0__none

- type: `POLARITY`
- condition: `C0`
- magnitude: `none`
- expected faithfulness verdict: `PASS`
- base_id: `P0144`

Highlighted diff (`« »` marks the span)

```
claim span: Morphine and meperidine «should be used» with caution or avoided in patients with renal insufficiency.
edit distance: 0
```

Evidence before

```
Alfentanil and sufentanil are seldom used, having largely been replaced by remifentanil in the mod-ern era. Morphine and meperidine have active metabolites that are renally excreted and thus should be used with caution or avoided in patients with renal insufficiency.Naloxone, an opioid antagonist, can be used to rapidly reverse the effects of opioids, and is commonly used to rescue patients from opioid-associated respiratory depression. Nalox-one is poorly absorbed orally and is also often combined with oral opioids to prevent abuse by injection use of the combined drug.
```

Evidence after

```
Alfentanil and sufentanil are seldom used, having largely been replaced by remifentanil in the mod-ern era. Morphine and meperidine have active metabolites that are renally excreted and thus should be used with caution or avoided in patients with renal insufficiency.Naloxone, an opioid antagonist, can be used to rapidly reverse the effects of opioids, and is commonly used to rescue patients from opioid-associated respiratory depression. Nalox-one is poorly absorbed orally and is also often combined with oral opioids to prevent abuse by injection use of the combined drug.
```

Claim before

```
Morphine and meperidine should be used with caution or avoided in patients with renal insufficiency.
```

Claim after

```
Morphine and meperidine should be used with caution or avoided in patients with renal insufficiency.
```

### P0060__E1-evid__flip

- type: `POLARITY`
- condition: `E1-evid`
- magnitude: `flip`
- expected faithfulness verdict: `FAIL`
- base_id: `P0060`

Highlighted diff (`« »` marks the span)

```
evidence before: Inhaled beta2-agonists should be added to therapy as needed for further control of asthma. Each drug prescribed «should be used» in maximal dosage before adding an additional agent. Preoperative treatment with combined corticosteroids and an inhaled beta2-adrenergic agonist for a 5-day period may decrease the risk of postoperative bronchospasm in patients with asthma (240).
evidence after: Inhaled beta2-agonists should be added to therapy as needed for further control of asthma. Each drug prescribed «should not be used» in maximal dosage before adding an additional agent. Preoperative treatment with combined corticosteroids and an inhaled beta2-adrenergic agonist for a 5-day period may decrease the risk of postoperative bronchospasm in patients with asthma (240).
evidence edit distance: 4
evidence confined to span: True
claim unchanged
```

Evidence before

```
Inhaled beta2-agonists should be added to therapy as needed for further control of asthma. Each drug prescribed should be used in maximal dosage before adding an additional agent. Preoperative treatment with combined corticosteroids and an inhaled beta2-adrenergic agonist for a 5-day period may decrease the risk of postoperative bronchospasm in patients with asthma (240).
```

Evidence after

```
Inhaled beta2-agonists should be added to therapy as needed for further control of asthma. Each drug prescribed should not be used in maximal dosage before adding an additional agent. Preoperative treatment with combined corticosteroids and an inhaled beta2-adrenergic agonist for a 5-day period may decrease the risk of postoperative bronchospasm in patients with asthma (240).
```

Claim before

```
Each prescribed drug should be used at the highest dosage before adding another medication.
```

Claim after

```
Each prescribed drug should be used at the highest dosage before adding another medication.
```

### P0120__E1-evid__flip

- type: `POLARITY`
- condition: `E1-evid`
- magnitude: `flip`
- expected faithfulness verdict: `FAIL`
- base_id: `P0120`

Highlighted diff (`« »` marks the span)

```
evidence before: There are anatomic conditions based on angiographic evaluation in which carotid artery stenting should be avoided due to increased procedure-related risks (Table 23-5). In preparation for carotid stenting, the patient «should be given» oral clopidogrel 3 days prior to the intervention if the patient was not already taking the drug. The procedure is done in either the operating room with angiographic capabilities or in a dedicated angiography room.
evidence after: There are anatomic conditions based on angiographic evaluation in which carotid artery stenting should be avoided due to increased procedure-related risks (Table 23-5). In preparation for carotid stenting, the patient «should not be given» oral clopidogrel 3 days prior to the intervention if the patient was not already taking the drug. The procedure is done in either the operating room with angiographic capabilities or in a dedicated angiography room.
evidence edit distance: 4
evidence confined to span: True
claim unchanged
```

Evidence before

```
There are anatomic conditions based on angiographic evaluation in which carotid artery stenting should be avoided due to increased procedure-related risks (Table 23-5). In preparation for carotid stenting, the patient should be given oral clopidogrel 3 days prior to the intervention if the patient was not already taking the drug. The procedure is done in either the operating room with angiographic capabilities or in a dedicated angiography room.
```

Evidence after

```
There are anatomic conditions based on angiographic evaluation in which carotid artery stenting should be avoided due to increased procedure-related risks (Table 23-5). In preparation for carotid stenting, the patient should not be given oral clopidogrel 3 days prior to the intervention if the patient was not already taking the drug. The procedure is done in either the operating room with angiographic capabilities or in a dedicated angiography room.
```

Claim before

```
In preparation for the procedure, you should be given oral clopidogrel 3 days prior to the intervention if you were not already taking the drug.
```

Claim after

```
In preparation for the procedure, you should be given oral clopidogrel 3 days prior to the intervention if you were not already taking the drug.
```

### P0033__E1-claim__flip

- type: `POLARITY`
- condition: `E1-claim`
- magnitude: `flip`
- expected faithfulness verdict: `FAIL`
- base_id: `P0033`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: Rabies vaccine «is recommended for» long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas.
claim after: Rabies vaccine «is not recommended for» long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas.
claim edit distance: 4
claim confined to span: True
```

Evidence before

```
The two vaccines available in the United States provide >90% protection. Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas; however, in a large-scale study, almost 50% of potential exposures occurred within the first month of travel. Even after receipt of a preexposure rabies vaccine series, two postexposure doses are required.
```

Evidence after

```
The two vaccines available in the United States provide >90% protection. Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas; however, in a large-scale study, almost 50% of potential exposures occurred within the first month of travel. Even after receipt of a preexposure rabies vaccine series, two postexposure doses are required.
```

Claim before

```
Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas.
```

Claim after

```
Rabies vaccine is not recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas.
```

### P0065__E1-claim__flip

- type: `POLARITY`
- condition: `E1-claim`
- magnitude: `flip`
- expected faithfulness verdict: `FAIL`
- base_id: `P0065`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: At the earliest sign of infection, high-dose intravenous antibiotic therapy «should be given» and the pregnancy evacuated promptly.
claim after: At the earliest sign of infection, high-dose intravenous antibiotic therapy «should not be given» and the pregnancy evacuated promptly.
claim edit distance: 4
claim confined to span: True
```

Evidence before

```
When pregnancy continues with an IUD in place, the patient must be warned of the symptoms of intrauterine infection and should be cautioned to seek care promptly for fever or ﬂulike symptoms, abdominal cramping, or bleeding. At the earliest sign of infection, high-dose intravenous antibiotic therapy should be given and the pregnancy evacuated promptly. Duration of Use
```

Evidence after

```
When pregnancy continues with an IUD in place, the patient must be warned of the symptoms of intrauterine infection and should be cautioned to seek care promptly for fever or ﬂulike symptoms, abdominal cramping, or bleeding. At the earliest sign of infection, high-dose intravenous antibiotic therapy should be given and the pregnancy evacuated promptly. Duration of Use
```

Claim before

```
At the earliest sign of infection, high-dose intravenous antibiotic therapy should be given and the pregnancy evacuated promptly.
```

Claim after

```
At the earliest sign of infection, high-dose intravenous antibiotic therapy should not be given and the pregnancy evacuated promptly.
```

### P0110__E2__flip

- type: `POLARITY`
- condition: `E2`
- magnitude: `flip`
- expected faithfulness verdict: `PASS`
- base_id: `P0110`

Highlighted diff (`« »` marks the span)

```
evidence before: Chronic phenytoin use over several decades may occasionally be associated with peripheral neuropathy and probably with a form of cerebellar degeneration (Lindvall and Nilsson); it is not clear if these are strictly dose-related effects or idiosyncratic reactions. An antifolate effect on blood and interference with vitamin K metabolism have also been reported, for which reason pregnant women taking phenytoin (and in fact most other antiepileptic drugs) «should be given» folate supplementation and vitamin K before delivery and the newborn infant also should receive vitamin K to prevent bleeding. Phenytoin should not be used together with disulfiram, chloramphenicol, sulfamethizole, or cyclophosphamide, and the use of either phenobarbital or phenytoin is not advisable in patients receiving warfarin because of the undesirable interactions already described.
evidence after: Chronic phenytoin use over several decades may occasionally be associated with peripheral neuropathy and probably with a form of cerebellar degeneration (Lindvall and Nilsson); it is not clear if these are strictly dose-related effects or idiosyncratic reactions. An antifolate effect on blood and interference with vitamin K metabolism have also been reported, for which reason pregnant women taking phenytoin (and in fact most other antiepileptic drugs) «should not be given» folate supplementation and vitamin K before delivery and the newborn infant also should receive vitamin K to prevent bleeding. Phenytoin should not be used together with disulfiram, chloramphenicol, sulfamethizole, or cyclophosphamide, and the use of either phenobarbital or phenytoin is not advisable in patients receiving warfarin because of the undesirable interactions already described.
evidence edit distance: 4
evidence confined to span: True
claim before: Pregnant women taking phenytoin «should be given» folate supplementation and vitamin K before delivery.
claim after: Pregnant women taking phenytoin «should not be given» folate supplementation and vitamin K before delivery.
claim edit distance: 4
claim confined to span: True
```

Evidence before

```
Chronic phenytoin use over several decades may occasionally be associated with peripheral neuropathy and probably with a form of cerebellar degeneration (Lindvall and Nilsson); it is not clear if these are strictly dose-related effects or idiosyncratic reactions. An antifolate effect on blood and interference with vitamin K metabolism have also been reported, for which reason pregnant women taking phenytoin (and in fact most other antiepileptic drugs) should be given folate supplementation and vitamin K before delivery and the newborn infant also should receive vitamin K to prevent bleeding. Phenytoin should not be used together with disulfiram, chloramphenicol, sulfamethizole, or cyclophosphamide, and the use of either phenobarbital or phenytoin is not advisable in patients receiving warfarin because of the undesirable interactions already described.
```

Evidence after

```
Chronic phenytoin use over several decades may occasionally be associated with peripheral neuropathy and probably with a form of cerebellar degeneration (Lindvall and Nilsson); it is not clear if these are strictly dose-related effects or idiosyncratic reactions. An antifolate effect on blood and interference with vitamin K metabolism have also been reported, for which reason pregnant women taking phenytoin (and in fact most other antiepileptic drugs) should not be given folate supplementation and vitamin K before delivery and the newborn infant also should receive vitamin K to prevent bleeding. Phenytoin should not be used together with disulfiram, chloramphenicol, sulfamethizole, or cyclophosphamide, and the use of either phenobarbital or phenytoin is not advisable in patients receiving warfarin because of the undesirable interactions already described.
```

Claim before

```
Pregnant women taking phenytoin should be given folate supplementation and vitamin K before delivery.
```

Claim after

```
Pregnant women taking phenytoin should not be given folate supplementation and vitamin K before delivery.
```

### P0032__E2__flip

- type: `POLARITY`
- condition: `E2`
- magnitude: `flip`
- expected faithfulness verdict: `PASS`
- base_id: `P0032`

Highlighted diff (`« »` marks the span)

```
evidence before: Because of the risk of fatal measles in children with AIDS, children without severe immunosuppression should receive their first dose of MMR at 12 months of age and may receive the booster as soon as 4 weeks later. Varicella zoster virus (VZV) vaccine «should be given» only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart. Inactivated split influenza virus vaccine should be administered annually to all HIV-infected children at or after 6 months of age.
evidence after: Because of the risk of fatal measles in children with AIDS, children without severe immunosuppression should receive their first dose of MMR at 12 months of age and may receive the booster as soon as 4 weeks later. Varicella zoster virus (VZV) vaccine «should not be given» only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart. Inactivated split influenza virus vaccine should be administered annually to all HIV-infected children at or after 6 months of age.
evidence edit distance: 4
evidence confined to span: True
claim before: The Varicella zoster virus (VZV) vaccine «should be given» only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart.
claim after: The Varicella zoster virus (VZV) vaccine «should not be given» only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart.
claim edit distance: 4
claim confined to span: True
```

Evidence before

```
Because of the risk of fatal measles in children with AIDS, children without severe immunosuppression should receive their first dose of MMR at 12 months of age and may receive the booster as soon as 4 weeks later. Varicella zoster virus (VZV) vaccine should be given only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart. Inactivated split influenza virus vaccine should be administered annually to all HIV-infected children at or after 6 months of age.
```

Evidence after

```
Because of the risk of fatal measles in children with AIDS, children without severe immunosuppression should receive their first dose of MMR at 12 months of age and may receive the booster as soon as 4 weeks later. Varicella zoster virus (VZV) vaccine should not be given only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart. Inactivated split influenza virus vaccine should be administered annually to all HIV-infected children at or after 6 months of age.
```

Claim before

```
The Varicella zoster virus (VZV) vaccine should be given only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart.
```

Claim after

```
The Varicella zoster virus (VZV) vaccine should not be given only to asymptomatic, nonimmunosuppressed children beginning at 12 months of age as two doses of vaccine at least 3 months apart.
```

### P0035__INV-claim__rephrase

- type: `POLARITY`
- condition: `INV-claim`
- magnitude: `rephrase`
- expected faithfulness verdict: `PASS`
- base_id: `P0035`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: The medication «should be given» orally or by nasogastric tube or per rectum.
claim after: The medication «ought to be given» orally or by nasogastric tube or per rectum.
claim edit distance: 7
claim confined to span: True
```

Evidence before

```
should be given orally or by nasogastric tube or per rectum; the drug’s inhibitory action on T4 → T3 conversion makes it the antithyroid drug of choice. If not available, methimazole can be used in doses up to 30 mg every 12 h.
```

Evidence after

```
should be given orally or by nasogastric tube or per rectum; the drug’s inhibitory action on T4 → T3 conversion makes it the antithyroid drug of choice. If not available, methimazole can be used in doses up to 30 mg every 12 h.
```

Claim before

```
The medication should be given orally or by nasogastric tube or per rectum.
```

Claim after

```
The medication ought to be given orally or by nasogastric tube or per rectum.
```

### P0109__INV-claim__rephrase

- type: `POLARITY`
- condition: `INV-claim`
- magnitude: `rephrase`
- expected faithfulness verdict: `PASS`
- base_id: `P0109`

Highlighted diff (`« »` marks the span)

```
evidence unchanged
claim before: Neuroleptics such as haloperidol and pimozide «should be used» only in severely affected patients and usually after trying adrenergic agents.
claim after: Neuroleptics such as haloperidol and pimozide «ought to be used» only in severely affected patients and usually after trying adrenergic agents.
claim edit distance: 7
claim confined to span: True
```

Evidence before

```
Clonidine is started as a bedtime dose of 0.05 mg and increased every several days by 0.05 mg until a total dose of about 0.1 mg three times daily. The neuroleptics haloperidol and pimozide, (and less frequently used sulpiride and tiapride) have proved to be effective therapeutic agents but should be used only in severely affected patients and usually after the adrenergic agents have been tried. Haloperidol is instituted in small doses
```

Evidence after

```
Clonidine is started as a bedtime dose of 0.05 mg and increased every several days by 0.05 mg until a total dose of about 0.1 mg three times daily. The neuroleptics haloperidol and pimozide, (and less frequently used sulpiride and tiapride) have proved to be effective therapeutic agents but should be used only in severely affected patients and usually after the adrenergic agents have been tried. Haloperidol is instituted in small doses
```

Claim before

```
Neuroleptics such as haloperidol and pimozide should be used only in severely affected patients and usually after trying adrenergic agents.
```

Claim after

```
Neuroleptics such as haloperidol and pimozide ought to be used only in severely affected patients and usually after trying adrenergic agents.
```
