# POLARITY template rephrase INV (QC review)

Generated from `data/v3/instances_main.jsonl` / `data/v3/instances_audit.jsonl`.

## Why not 78?

- **78** POLARITY bases each get a `rephrase` row from `perturb_one` (equivalent template only: should↔ought, recommended for↔indicated for, G pairs).
- Rows with no kept mapping → `pol_rephrase_nonequivalent`.
- Valid rows also pass the same main gate as POL **C0** after QC **I** (`domain_kind==treatment`, main subset).

- Valid rephrase INV for scoring/analysis: **42**
- Invalid (audit only): **36**

## Template mappings (cue → rephrase) with counts

Counts are over all generated rephrase rows (valid + invalid).

| Table | Cue | Rephrase | n |
| --- | --- | --- | --- |
| `INV_POLARITY` | `should be used` | `ought to be used` | 24 |
| `INV_POLARITY` | `should be given` | `ought to be given` | 17 |
| `INV_POLARITY` | `should be administered` | `ought to be administered` | 14 |
| `INV_POLARITY` | `is recommended for` | `is indicated for` | 10 |
| `INV_POLARITY` | `are recommended for` | `are indicated for` | 4 |
| `INV_POLARITY` | `are indicated for` | `are recommended for` | 2 |
| `UNMAPPED` | `no rephrase INV for 'contraindicated in'` | `` | 2 |
| `UNMAPPED` | `no rephrase INV for 'is not recommended'` | `` | 2 |
| `UNMAPPED` | `no rephrase INV for 'are not indicated'` | `` | 1 |
| `UNMAPPED` | `no rephrase INV for 'are not recommended'` | `` | 1 |
| `UNMAPPED` | `no rephrase INV for 'is not indicated'` | `` | 1 |

## Valid rows for PI review

| base_id | mapping | sentence_rule | original | rephrased |
| --- | --- | --- | --- | --- |
| **P0003** | should be administered → ought to be administered (INV_POLARITY) | ok | MMR and varicella vaccines should be administered simultaneously or more than 30 days apart. | MMR and varicella vaccines ought to be administered simultaneously or more than 30 days apart. |
| **P0004** | should be administered → ought to be administered (INV_POLARITY) | ok | If uterine perforation was excluded by ultrasonography, intravenous broad-spectrum antibiotic coverage, usually with a cephalosporin, should be administered. | If uterine perforation was excluded by ultrasonography, intravenous broad-spectrum antibiotic coverage, usually with a cephalosporin, ought to be administered. |
| **P0017** | should be used → ought to be used (INV_POLARITY) | ok | Neither medication should be used with occlusive dressings. | Neither medication ought to be used with occlusive dressings. |
| **P0019** | should be used → ought to be used (INV_POLARITY) | ok | For the second drug, pemetrexed should be used for non-squamous cell cancer. | For the second drug, pemetrexed ought to be used for non-squamous cell cancer. |
| **P0020** | should be administered → ought to be administered (INV_POLARITY) | ok | Fast-acting soluble insulin should be administered as a continuous IV infusion (0.1 U/kg/hour). | Fast-acting soluble insulin ought to be administered as a continuous IV infusion (0.1 U/kg/hour). |
| **P0021** | should be used → ought to be used (INV_POLARITY) | ok | Antibiotic prophylaxis should be used in necrotizing pancreatitis, as recommended by high-level EBM based on extensive studies, though these recommendations were later reversed. | Antibiotic prophylaxis ought to be used in necrotizing pancreatitis, as recommended by high-level EBM based on extensive studies, though these recommendations were later reversed. |
| **P0033** | is recommended for → is indicated for (INV_POLARITY) | ok | Rabies vaccine is recommended for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas. | Rabies vaccine is indicated for long-stay travelers, particularly children (who tend to play with animals and may not report bites), and for persons who may be occupationally exposed to rabies in endemic areas. |
| **P0035** | should be given → ought to be given (INV_POLARITY) | ok | The medication should be given orally or by nasogastric tube or per rectum. | The medication ought to be given orally or by nasogastric tube or per rectum. |
| **P0044** | is recommended for → is indicated for (INV_POLARITY) | ok | The vaccine is recommended for persons staying in rural endemic areas for more than one month or for shorter periods if their activities will increase their risk of exposure. | The vaccine is indicated for persons staying in rural endemic areas for more than one month or for shorter periods if their activities will increase their risk of exposure. |
| **P0046** | should be administered → ought to be administered (INV_POLARITY) | ok | When a woman with an IUD is suspected to have PID, antibiotic therapy should be administered. | When a woman with an IUD is suspected to have PID, antibiotic therapy ought to be administered. |
| **P0048** | are indicated for → are recommended for (INV_POLARITY) | ok | Second-line antituberculosis agents are indicated for the treatment of drug-resistant TB, for patients who are intolerant or allergic to first-line agents, and when first-line supplemental agents are unavailable. | Second-line antituberculosis agents are recommended for the treatment of drug-resistant TB, for patients who are intolerant or allergic to first-line agents, and when first-line supplemental agents are unavailable. |
| **P0049** | should be administered → ought to be administered (INV_POLARITY) | ok | Preoperative antimicrobial therapy should be administered when appropriate, based on clinical guidelines, and occur within a time frame that allows bactericidal concentration of the agent in tissues before the incision is made. | Preoperative antimicrobial therapy ought to be administered when appropriate, based on clinical guidelines, and occur within a time frame that allows bactericidal concentration of the agent in tissues before the incision is made. |
| **P0052** | is recommended for → is indicated for (INV_POLARITY) | ok | Tetracycline, 500 mg qid for 30 days, is recommended for patients who are allergic to these intravenous drugs. | Tetracycline, 500 mg qid for 30 days, is indicated for patients who are allergic to these intravenous drugs. |
| **P0059** | should be used → ought to be used (INV_POLARITY) | ok | In cases of cerebral embolism associated with bacterial endocarditis, anticoagulant therapy should be used cautiously because of the risk of intracranial bleeding. | In cases of cerebral embolism associated with bacterial endocarditis, anticoagulant therapy ought to be used cautiously because of the risk of intracranial bleeding. |
| **P0060** | should be used → ought to be used (INV_POLARITY) | ok | Each prescribed drug should be used at the highest dosage before adding another medication. | Each prescribed drug ought to be used at the highest dosage before adding another medication. |
| **P0065** | should be given → ought to be given (INV_POLARITY) | ok | At the earliest sign of infection, high-dose intravenous antibiotic therapy should be given and the pregnancy evacuated promptly. | At the earliest sign of infection, high-dose intravenous antibiotic therapy ought to be given and the pregnancy evacuated promptly. |
| **P0066** | should be used → ought to be used (INV_POLARITY) | ok | This medication should be used with great caution due to reports of significant renal damage and deaths. | This medication ought to be used with great caution due to reports of significant renal damage and deaths. |
| **P0067** | is recommended for → is indicated for (INV_POLARITY) | ok | Maintenance therapy is recommended for patients who experience a rapid return of symptoms after stopping their medication. | Maintenance therapy is indicated for patients who experience a rapid return of symptoms after stopping their medication. |
| **P0069** | should be used → ought to be used (INV_POLARITY) | ok | If these medications cannot be eliminated, they should be used at the lowest dose possible. | If these medications cannot be eliminated, they ought to be used at the lowest dose possible. |
| **P0073** | should be given → ought to be given (INV_POLARITY) | ok | Women who have not received a tetanus/diphtheria or influenza vaccine should be given these. | Women who have not received a tetanus/diphtheria or influenza vaccine ought to be given these. |
| **P0076** | should be given → ought to be given (INV_POLARITY) | ok | Morphine and other narcotics should be given at optimal doses regularly to manage pain effectively. | Morphine and other narcotics ought to be given at optimal doses regularly to manage pain effectively. |
| **P0085** | should be administered → ought to be administered (INV_POLARITY) | ok | If any dose in the series was RV-5 or the vaccine product is unknown for any dose in the series, a total of 3 doses of RV vaccine should be administered. | If any dose in the series was RV-5 or the vaccine product is unknown for any dose in the series, a total of 3 doses of RV vaccine ought to be administered. |
| **P0086** | should be administered → ought to be administered (INV_POLARITY) | ok | Empiric antibiotic therapy should be administered until bacterial meningitis can be excluded. | Empiric antibiotic therapy ought to be administered until bacterial meningitis can be excluded. |
| **P0087** | should be used → ought to be used (INV_POLARITY) | ok | The most effective and least toxic antibiotic, given in the shortest possible course—ideally a single dose—should be used. | The most effective and least toxic antibiotic, given in the shortest possible course—ideally a single dose—ought to be used. |
| **P0092** | is recommended for → is indicated for (INV_POLARITY) | ok | The oral antifungal agent, fluconazole, used in a single 150-mg dose, is recommended for the treatment of VVC. | The oral antifungal agent, fluconazole, used in a single 150-mg dose, is indicated for the treatment of VVC. |
| **P0094** | should be administered → ought to be administered (INV_POLARITY) | ok | Antibiotics should be administered in full doses parenterally (preferably intravenously) throughout the period of treatment. | Antibiotics ought to be administered in full doses parenterally (preferably intravenously) throughout the period of treatment. |
| **P0095** | should be given → ought to be given (INV_POLARITY) | ok | If the first medicine does not control seizures, a different one should be tried, but frequent changes are not advisable; each should be given an adequate trial before another is substituted. | If the first medicine does not control seizures, a different one should be tried, but frequent changes are not advisable; each ought to be given an adequate trial before another is substituted. |
| **P0097** | should be administered → ought to be administered (INV_POLARITY) | ok | If the patient is febrile, broad-spectrum antibiotic therapy should be administered. | If the patient is febrile, broad-spectrum antibiotic therapy ought to be administered. |
| **P0104** | should be administered → ought to be administered (INV_POLARITY) | ok | The inactivated split influenza virus vaccine should be administered annually to all HIV-infected children at or after 6 months of age. | The inactivated split influenza virus vaccine ought to be administered annually to all HIV-infected children at or after 6 months of age. |
| **P0106** | should be given → ought to be given (INV_POLARITY) | ok | If a seizure has occurred or if there is evidence of cortical vein thrombosis, antiepileptic drugs should be given. | If a seizure has occurred or if there is evidence of cortical vein thrombosis, antiepileptic drugs ought to be given. |
| **P0111** | should be used → ought to be used (INV_POLARITY) | ok | Azithromycin should be used in neonates due to the association between erythromycin treatment and the development of pyloric stenosis. | Azithromycin ought to be used in neonates due to the association between erythromycin treatment and the development of pyloric stenosis. |
| **P0116** | should be administered → ought to be administered (INV_POLARITY) | ok | Antimicrobial agents, including high-dose penicillin G, should be administered to treat the infection. | Antimicrobial agents, including high-dose penicillin G, ought to be administered to treat the infection. |
| **P0120** | should be given → ought to be given (INV_POLARITY) | ok | In preparation for the procedure, you should be given oral clopidogrel 3 days prior to the intervention if you were not already taking the drug. | In preparation for the procedure, you ought to be given oral clopidogrel 3 days prior to the intervention if you were not already taking the drug. |
| **P0124** | should be administered → ought to be administered (INV_POLARITY) | ok | If mechanical ventilation and supportive care are unsuccessful in improving oxygenation, inhaled nitric oxide should be administered. | If mechanical ventilation and supportive care are unsuccessful in improving oxygenation, inhaled nitric oxide ought to be administered. |
| **P0127** | should be given → ought to be given (INV_POLARITY) | ok | After a shock or administration of a drug, CPR should be resumed immediately, and five cycles of CPR should be given before checking for a pulse or rhythm. | After a shock or administration of a drug, CPR should be resumed immediately, and five cycles of CPR ought to be given before checking for a pulse or rhythm. |
| **P0132** | is recommended for → is indicated for (INV_POLARITY) | ok | Contraception is recommended for 2 months after drug cessation. | Contraception is indicated for 2 months after drug cessation. |
| **P0142** | should be given → ought to be given (INV_POLARITY) | ok | For uncomplicated urinary tract infections, an antibiotic that has good activity against E. coli should be given in the interim while awaiting results of the urine culture and sensitivity data. | For uncomplicated urinary tract infections, an antibiotic that has good activity against E. coli ought to be given in the interim while awaiting results of the urine culture and sensitivity data. |
| **P0159** | should be used → ought to be used (INV_POLARITY) | ok | If the penicillin skin test is positive, an alternative antibiotic should be used. | If the penicillin skin test is positive, an alternative antibiotic ought to be used. |
| **P0161** | is recommended for → is indicated for (INV_POLARITY) | ok | Antibiotic treatment is recommended for newborns whose mothers have untreated gonorrhea. | Antibiotic treatment is indicated for newborns whose mothers have untreated gonorrhea. |
| **P0162** | should be administered → ought to be administered (INV_POLARITY) | ok | The antibiotics should be administered just before the surgery starts. | The antibiotics ought to be administered just before the surgery starts. |
| **P0175** | should be used → ought to be used (INV_POLARITY) | ok | Antibiotic prophylaxis should be used in these patients, and uremia should be treated with dialysis as indicated. | Antibiotic prophylaxis ought to be used in these patients, and uremia should be treated with dialysis as indicated. |
| **P0176** | should be administered → ought to be administered (INV_POLARITY) | ok | The final dose in the HepB vaccine series should be administered no earlier than age 24 weeks and at least 16 weeks after the first dose. | The final dose in the HepB vaccine series ought to be administered no earlier than age 24 weeks and at least 16 weeks after the first dose. |

## Invalid rephrase rows (audit)

- `pol_rephrase_domain:unclear`: 26
- `pol_rephrase_nonequivalent`: 7
- `pol_rephrase_domain:other`: 2
- `pol_rephrase_domain:diagnostic_procedure`: 1
