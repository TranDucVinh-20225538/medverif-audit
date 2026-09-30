# M1 repair — LLM judges on E1-unit evidence

PASS **n/N** before vs after M1; keyword rate = share of **after-M1 PASS** explanations matching typo/error/likely-mg/unit/conversion (heuristic).

## T7 E1-unit-evid (×1000)

Instances: **115**

| Judge | PASS before | PASS after M1 | kw / after PASS |
| --- | --- | --- | --- |
| V1 | 44/115 | 13/115 | 0/13 |
| V1b | 0/0 | 0/0 | 0/0 |
| V1c | 0/0 | 0/0 | 0/0 |
| V4-Llama | 53/114 | 19/114 | 1/19 |
| V5 | 0/0 | 0/0 | 0/0 |
| V6-gpt4o | 0/0 | 0/0 | 0/0 |
| V6-haiku | 0/0 | 0/0 | 0/0 |
| V6-llama8b | 0/0 | 0/0 | 0/0 |
| V6-mistral | 0/0 | 0/0 | 0/0 |

### V1 — sample after-M1 PASS explanations
- `D0020__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The context states that "men receiving daily famciclovir (250,000 mg every 12 hours) for 18 weeks had no changes in sperm morphology or motility."
- `D0035__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The context states that treatment with parenteral vitamin B12 (1000 mg intramuscularly daily for a week, weekly for a month, and monthly for life for pernicious anemia) stops progression of the disease if instituted promptly, but complete reversal of advanced nervous system damage will not occur. This aligns with the statement that 1 mg given
- `D0044__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The context states that the drug octreotide is administered subcutaneously (under the skin) starting at 50 mg tid (three times a day), with the dose adjusted based on clinical response.
- `D0049__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The text states that for children, the dose of Naloxone is 0.1 mg/kg IV, ET, SC, IM.
- `D0050__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The context states that "An alternative regimen for adults is ciprofloxacin (500 mg orally twice daily) for 5–7 days."
- `D0067__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The context states that "The recommended dosage for most indications is 600 mg twice daily, either orally or intravenously."
- `D0071__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The statement "There seems to be relatively small risk if low-dose (81 mg) aspirin is included in a regimen of warfarin for atrial fibrillation" is directly quoted from the given context.
- `D0089__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The context states that "Following transfusion of PRBCs to neonates with tenuous fluid balance, a single dose of a diuretic (such as furosemide 1 g/kg) may help to facilitate excretion of the extra fluid load." This aligns with the statement in the input, although the dose is incorrectly stated as 1 mg/kg in the input, it should be 1 g/kg.
- `D0102__E1-unit-evid__x1000` [V1 after M1 PASS]: True.
- `D0119__E1-unit-evid__x1000` [V1 after M1 PASS]: True. The text states that "Patients are instructed to abstain from sexual intercourse for 7 days after they and their sexual partners have completed treatment." This includes taking 1000 mg of azithromycin as part of the treatment regimen.

### V4-Llama — sample after-M1 PASS explanations
- `D0013__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "Erythromycin, given as a 250 mg intravenous dose about 30 minutes before endoscopy, can help improve the view during the procedure.",             "reason": "The context states that erythromycin provides a small but significant increase in diagnostic yield, which implies that it can help impr
- `D0033__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "For patients with severe odynophagia, intravenous acyclovir at a dose of 5 mg/kg every 8 hours for 7–14 days can reduce this discomfort.",             "reason": "The context explicitly mentions that intravenous acyclovir, 5 mg/kg every 8 hours for 7–14 days, reduces morbidity in patients wit
- `D0036__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "Taking valacyclovir once daily at 500 mg has been shown to reduce the transmission of HSV-2 between sexual partners.",             "reason": "The context explicitly states that once-daily valacyclovir (500000 mg) has been shown to reduce transmission of HSV-2 between sexual partners, which d
- `D0049__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "For children, the dose of Naloxone is 0.1 mg/kg.",             "reason": "The context explicitly mentions that for children, Naloxone is given at a dose of 0.1 g/kg, which is equivalent to 0.1 mg/kg (since 1g = 1000mg), so the statement can be directly inferred.",             "verdict": 1   
- `D0050__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "An alternative treatment for adults is ciprofloxacin, which is taken orally at a dose of 500 mg twice daily for 5–7 days.",             "reason": "The context explicitly mentions that an alternative regimen for adults is ciprofloxacin (500 mg orally twice daily) or another fluoroquinolone fo
- `D0071__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: Here is the output in the required JSON format:  ``` {     "statements": [         {             "statement": "There seems to be relatively small risk if low-dose (81 mg) aspirin is included in a regimen of warfarin for atrial fibrillation.",             "reason": "The statement is directly supported by the context, which mentions that there seems 
- `D0090__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "Occasionally, daily doses of 600 mg or higher are necessary.",             "reason": "The context explicitly mentions that occasionally, daily doses of 600000 mg or higher are necessary, which implies that doses of 600 mg or higher can be necessary, given the context's mention of much higher
- `D0096__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "In an average-sized adult at rest, the tidal volume is 500 mL.",             "reason": "The context explicitly states that in an average-sized adult at rest, tidal volume is 500000 mL, which is equivalent to 500 mL given the context's own definition of an average-sized adult.",             "
- `D0099__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "Oral gabapentin enacarbil may be taken at a dose of 1200 mg once daily.",             "reason": "The context explicitly mentions that oral gabapentin enacarbil may be taken at a dose of 600 or 1200 mg once daily, which includes the dose mentioned in the statement.",             "verdict": 1 
- `D0102__E1-unit-evid__x1000` [V4-Llama after M1 PASS]: {     "statements": [         {             "statement": "The recommended dose of prednisolone is 2 mg/kg per day, given orally in two to three divided doses.",             "reason": "The context explicitly mentions that prednisolone (2 g/kg per day) may be given orally in two to three divided doses, which is equivalent to 2 mg/kg per day. Therefor

## T17 E1-unit-down evid (÷1000-style pack)

Instances: **76**

| Judge | PASS before | PASS after M1 | kw / after PASS |
| --- | --- | --- | --- |
| V1 | 0/0 | 0/0 | 0/0 |
| V4-Llama | 0/0 | 0/0 | 0/0 |
| V6-llama8b | 0/0 | 0/0 | 0/0 |

