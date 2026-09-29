# QC samples — INV paraphrase pilot v2 (OpenRouter)

**WAIT for PI OK** before full paraphrase run.

- Generator: `qwen/qwen-2.5-72b-instruct` (≠ V1 Mistral, ≠ V4 Qwen3-14B)
- Validator: `microsoft/phi-4` (Phi-4)
- Pilot: **10 DOSE + 10 POLARITY** (main subset, QC rule B–valid POLARITY only)
- Pass rate: **11/20** (55.0%)

- Bases: `valid=true` main C0; excludes POLARITY with flip rule B block (e.g. P0009, P0017).
- Rules: qualifier-set match, no fronting, Jaccard ≥ 0.5, not pure permutation, then Phi-4.

## D0001 (DOSE, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
A two-hour oral glucose tolerance test involves drinking a solution containing exactly 75 g of glucose.
```

**Rewrite**
```
A solution containing exactly 75 g of glucose is consumed during a two-hour oral glucose tolerance test.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610297-QdY1OJ8lYeNnNXHQ9Mag", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610298-35QBWOahTgpUYSIxNQLi", "model": "microsoft/phi-4", "tokens": 68, "cost_usd": 4.9e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610299-1siSJnRW1lXceu6Jrqsl", "model": "microsoft/phi-4", "tokens": 121, "cost_usd": 9.59e-06}`

## D0002 (DOSE, main)

**Pass:** False (attempt 3/3)
**Rule:** fronting | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=fronting flu=YES mean=YES
- a2: rule=fronting flu=YES mean=YES
- a3: rule=fronting flu=YES mean=YES

**Original**
```
Most clinicians agree that glucocorticoids, such as prednisone at a dose of 1 mg/kg as a single daily dose either orally or intravenously, are a reasonable first therapy for both PM and DM.
```

**Rewrite**
```
A reasonable first therapy for both PM and DM, according to most clinicians, involves glucocorticoids such as prednisone administered as a single daily dose of 1 mg/kg either orally or intravenously.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610308-55A0tYQMJyXA2st0ezPH", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610310-2y8szo8K3CrO8MJ7u24B", "model": "microsoft/phi-4", "tokens": 91, "cost_usd": 6.51e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610311-IFnulMSLFrKFmu67Anau", "model": "microsoft/phi-4", "tokens": 170, "cost_usd": 1.302e-05}`

## D0003 (DOSE, main)

**Pass:** False (attempt 3/3)
**Rule:** fronting | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=leading_lower flu=YES mean=YES
- a2: rule=fronting flu=YES mean=YES
- a3: rule=fronting flu=YES mean=YES

**Original**
```
Adalimumab is given by subcutaneous injection, 40 mg biweekly.
```

**Rewrite**
```
Biweekly, a subcutaneous injection of 40 mg adalimumab is administered.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610319-RYJw9Se2IwP9LvWyQD1P", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610320-CQZzJXu0GVeg6aQJmxGO", "model": "microsoft/phi-4", "tokens": 67, "cost_usd": 4.83e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610321-jxUm8lzdHB7oHyvOIyaG", "model": "microsoft/phi-4", "tokens": 119, "cost_usd": 9.45e-06}`

## D0004 (DOSE, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
It is important to note that peripheral neuropathies can be seen in doses of 200 mg per day or higher, as well as interaction with other medications.
```

**Rewrite**
```
Doses of 200 mg per day or higher, as well as interaction with other medications, can lead to peripheral neuropathies.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610322-50a9m8FFsACiFHw37NdN", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610324-ujCZYJ0UN2IkELYwIh7C", "model": "microsoft/phi-4", "tokens": 75, "cost_usd": 5.39e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610325-ayjzZP5Vl7lLopcvEaSF", "model": "microsoft/phi-4", "tokens": 141, "cost_usd": 1.099e-05}`

## D0005 (DOSE, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
Etanercept is given by subcutaneous injection, 50 mg once weekly.
```

**Rewrite**
```
A subcutaneous injection of 50 mg is administered once weekly as etanercept.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610326-WbyS6evmfutS2cp2tiMb", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610327-PC2042DYSFLtawVnAFWu", "model": "microsoft/phi-4", "tokens": 67, "cost_usd": 4.83e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610328-BDOrP59AmxyjYQOiicT0", "model": "microsoft/phi-4", "tokens": 119, "cost_usd": 9.45e-06}`

## D0007 (DOSE, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
Tranexamic acid is given at doses of 25 mg/kg three to four times a day.
```

**Rewrite**
```
Doses of 25 mg/kg are administered three to four times a day for tranexamic acid.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610329-jn0Drm0hoAPqMjp49eG1", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610332-F1uJmQu4xDOSnpkVWQM6", "model": "microsoft/phi-4", "tokens": 69, "cost_usd": 4.97e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610332-Dfc82GGjyVyum16lon11", "model": "microsoft/phi-4", "tokens": 124, "cost_usd": 9.8e-06}`

## D0008 (DOSE, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
Infants born to HBsAg-positive mothers should receive HBV vaccine and hepatitis B immunoglobulin (HBIG) (0.5 mL) within 12 hours of birth, with subsequent vaccine doses at 1 month and 6 months of age followed by testing for HBsAg and anti-HBs at 9 to 15 months of age.
```

**Rewrite**
```
Within 12 hours of birth, infants born to HBsAg-positive mothers should be given HBV vaccine and hepatitis B immunoglobulin (0.5 mL), followed by additional vaccine doses at 1 month and 6 months of age and testing for HBsAg and anti-HBs at 9 to 15 months of age.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610333-MPLnuhjoRZuFhTOorLhn", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610337-8CvHRrhz15Ylw6QTpTLM", "model": "microsoft/phi-4", "tokens": 116, "cost_usd": 8.26e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610338-3B7sSc63v0NVUz0wQfP8", "model": "microsoft/phi-4", "tokens": 222, "cost_usd": 1.666e-05}`

## D0009 (DOSE, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
The recommended dose of cefazolin is 2 g.
```

**Rewrite**
```
Cefazolin's recommended dose is 2 g.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610339-Z1oz9nN0bq1rnBlh44Za", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610342-fEQvxQMHlVaKxbMPGv9o", "model": "microsoft/phi-4", "tokens": 60, "cost_usd": 4.34e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610344-iSDYHibED7qQXNZRtUlC", "model": "microsoft/phi-4", "tokens": 107, "cost_usd": 8.61e-06}`

## D0011 (DOSE, main)

**Pass:** True (attempt 2/2)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=ok flu=NO mean=YES

**Original**
```
If you are unable to swallow medications or do not respond well to other treatments, you can receive caspofungin 50 mg daily through an intravenous echinocandin for 7–21 days.
```

**Rewrite**
```
Caspofungin, an intravenous echinocandin, can be administered at 50 mg daily for 7–21 days if you cannot swallow medications or do not respond well to other treatments.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610348-aPtX5G8YZCJVnOfM3KiD", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 2, "seed": 43, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610351-J3guAXy0Ki9EUTLNJxUD", "model": "microsoft/phi-4", "tokens": 90, "cost_usd": 6.44e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610351-aYRCFqQoKhMQEsRtuDJZ", "model": "microsoft/phi-4", "tokens": 167, "cost_usd": 1.281e-05}`

## D0013 (DOSE, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
Erythromycin, given as a 250 mg intravenous dose about 30 minutes before endoscopy, can help improve the view during the procedure.
```

**Rewrite**
```
A 250 mg intravenous dose of erythromycin, administered about 30 minutes before endoscopy, can help improve the view during the procedure.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610352-Ljs0meUztrzD4tpqWhag", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610357-nuk9F9SHf6d6V4Rq6adn", "model": "microsoft/phi-4", "tokens": 80, "cost_usd": 5.74e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610357-LAbrl3L3JAmzmnfHsVQe", "model": "microsoft/phi-4", "tokens": 147, "cost_usd": 1.141e-05}`

## P0004 (POLARITY, main)

**Pass:** False (attempt 3/3)
**Rule:** pure_permutation | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=pure_permutation flu=YES mean=YES
- a2: rule=pure_permutation flu=YES mean=YES
- a3: rule=pure_permutation flu=YES mean=YES

**Original**
```
If uterine perforation was excluded by ultrasonography, intravenous broad-spectrum antibiotic coverage, usually with a cephalosporin, should be administered.
```

**Rewrite**
```
Intravenous broad-spectrum antibiotic coverage, usually with a cephalosporin, should be administered if uterine perforation was excluded by ultrasonography.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610368-wtdqyWRPFeARfmDKmnOr", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610370-FvyTucJpLdDtgzT6aszG", "model": "microsoft/phi-4", "tokens": 82, "cost_usd": 5.88e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610371-gpzotVJ58W4qdruzoAea", "model": "microsoft/phi-4", "tokens": 150, "cost_usd": 1.162e-05}`

## P0019 (POLARITY, main)

**Pass:** True (attempt 2/2)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=ok flu=YES mean=NO

**Original**
```
For the second drug, pemetrexed should be used for non-squamous cell cancer.
```

**Rewrite**
```
Pemetrexed, the second drug, should be used for treating non-squamous cell cancer.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610377-inOSjMRaALJ8jjPMD4B5", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 2, "seed": 43, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610378-dCd76TRjQTo97kNNtIAz", "model": "microsoft/phi-4", "tokens": 83, "cost_usd": 6.93e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610379-eUuLvuK3Lg7rO5bewImD", "model": "microsoft/phi-4", "tokens": 123, "cost_usd": 9.73e-06}`

## P0021 (POLARITY, main)

**Pass:** True (attempt 2/2)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=ok flu=NO mean=YES

**Original**
```
Antibiotic prophylaxis should be used in necrotizing pancreatitis, as recommended by high-level EBM based on extensive studies, though these recommendations were later reversed.
```

**Rewrite**
```
In necrotizing pancreatitis, antibiotic prophylaxis should be used according to high-level EBM that was initially based on extensive studies, although these guidelines were subsequently overturned.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610392-UQJE86Y4cZoUXte6eVOp", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 2, "seed": 43, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610397-uzA92yBlYhpJEgB7a800", "model": "microsoft/phi-4", "tokens": 83, "cost_usd": 5.95e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610399-x27CuVNPQvfluByA3eXV", "model": "microsoft/phi-4", "tokens": 152, "cost_usd": 1.176e-05}`

## P0046 (POLARITY, main)

**Pass:** False (attempt 3/3)
**Rule:** pure_permutation | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=pure_permutation flu=YES mean=YES
- a2: rule=pure_permutation flu=YES mean=YES
- a3: rule=pure_permutation flu=YES mean=YES

**Original**
```
When a woman with an IUD is suspected to have PID, antibiotic therapy should be administered.
```

**Rewrite**
```
Antibiotic therapy should be administered when a woman with an IUD is suspected to have PID.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610415-RMWVafBHobKMzxF6upLa", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610417-k0DkcoZpnctZntcOVZ8T", "model": "microsoft/phi-4", "tokens": 68, "cost_usd": 4.9e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610418-DhK5HgRQrYZNRMHIKC4L", "model": "microsoft/phi-4", "tokens": 121, "cost_usd": 9.59e-06}`

## P0085 (POLARITY, main)

**Pass:** False (attempt 3/3)
**Rule:** pure_permutation | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=pure_permutation flu=YES mean=YES
- a2: rule=pure_permutation flu=YES mean=YES
- a3: rule=pure_permutation flu=YES mean=YES

**Original**
```
If any dose in the series was RV-5 or the vaccine product is unknown for any dose in the series, a total of 3 doses of RV vaccine should be administered.
```

**Rewrite**
```
A total of 3 doses of RV vaccine should be administered if any dose in the series was RV-5 or the vaccine product is unknown for any dose in the series.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610428-AUyK8EqVR6q1JbpXOH05", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610434-5cgGm6en8PDwdp1gHkjg", "model": "microsoft/phi-4", "tokens": 83, "cost_usd": 5.95e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610436-fBlLly301IgGj03ap1ik", "model": "microsoft/phi-4", "tokens": 153, "cost_usd": 1.183e-05}`

## P0087 (POLARITY, main)

**Pass:** True (attempt 1/1)
**Rule:** ok | **Fluency:** YES | **Meaning:** YES

**Original**
```
The most effective and least toxic antibiotic, given in the shortest possible course—ideally a single dose—should be used.
```

**Rewrite**
```
A single dose, ideally, of the most effective and least toxic antibiotic, given in the shortest possible course, should be used.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610437-6gcUghfaNXP23Fb9JY8K", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 1, "seed": 42, "temperature": 0.0}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610440-K3Z618ei7wBmhmVVMoW0", "model": "microsoft/phi-4", "tokens": 74, "cost_usd": 5.32e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610440-3eLlhz8TWvmeJeRyg6Uh", "model": "microsoft/phi-4", "tokens": 133, "cost_usd": 1.043e-05}`

## P0089 (POLARITY, main)

**Pass:** False (attempt 3/3)
**Rule:** fronting | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=span_count flu=NO mean=YES
- a2: rule=fronting flu=YES mean=YES
- a3: rule=fronting flu=YES mean=YES

**Original**
```
The vaccine is not recommended for pregnant women.
```

**Rewrite**
```
For pregnant women, the vaccine is not recommended.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610448-beq3jjcKDgGVNSWviu1B", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610450-6ZCggs6wIdUZ4rFm53fA", "model": "microsoft/phi-4", "tokens": 58, "cost_usd": 4.2e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610450-q15GOowuwFVbSeS0VJje", "model": "microsoft/phi-4", "tokens": 101, "cost_usd": 8.19e-06}`

## P0097 (POLARITY, main)

**Pass:** False (attempt 3/3)
**Rule:** pure_permutation | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=pure_permutation flu=YES mean=YES
- a2: rule=pure_permutation flu=YES mean=YES
- a3: rule=pure_permutation flu=YES mean=YES

**Original**
```
If the patient is febrile, broad-spectrum antibiotic therapy should be administered.
```

**Rewrite**
```
Broad-spectrum antibiotic therapy should be administered if the patient is febrile.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610461-aYPdDszajAnX7fHJ5F97", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610467-xkE9ren1RcLyJBwWG9cv", "model": "microsoft/phi-4", "tokens": 64, "cost_usd": 4.62e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610468-cTZWft4KpsJGUpbrJ39k", "model": "microsoft/phi-4", "tokens": 115, "cost_usd": 9.17e-06}`

## P0106 (POLARITY, main)

**Pass:** False (attempt 3/3)
**Rule:** pure_permutation | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=pure_permutation flu=YES mean=YES
- a2: rule=pure_permutation flu=YES mean=YES
- a3: rule=pure_permutation flu=YES mean=YES

**Original**
```
If a seizure has occurred or if there is evidence of cortical vein thrombosis, antiepileptic drugs should be given.
```

**Rewrite**
```
Antiepileptic drugs should be given if a seizure has occurred or if there is evidence of cortical vein thrombosis.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610497-PEYcmmBeUZ515qo4aJPz", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610506-AEBwFs1nG7FVx6atXp7f", "model": "microsoft/phi-4", "tokens": 73, "cost_usd": 5.25e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610507-EpJm6FIa0MuyPKxCxpPS", "model": "microsoft/phi-4", "tokens": 133, "cost_usd": 1.043e-05}`

## P0111 (POLARITY, main)

**Pass:** False (attempt 3/3)
**Rule:** fronting | **Fluency:** YES | **Meaning:** YES

**Rejections:**
- a1: rule=pure_permutation flu=YES mean=YES
- a2: rule=fronting flu=YES mean=YES
- a3: rule=fronting flu=YES mean=YES

**Original**
```
Azithromycin should be used in neonates due to the association between erythromycin treatment and the development of pyloric stenosis.
```

**Rewrite**
```
Due to the association between erythromycin treatment and the development of pyloric stenosis, azithromycin should be used in neonates.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790610544-iOmyVvsr8KFAySyrVK9f", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct", "attempt": 3, "seed": 44, "temperature": 0.7}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790610558-pc4FcapUbF9ubdWldlfN", "model": "microsoft/phi-4", "tokens": 79, "cost_usd": 5.67e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790610559-8Pjvb9k6u5sQxhe2Yyo7", "model": "microsoft/phi-4", "tokens": 143, "cost_usd": 1.113e-05}`

