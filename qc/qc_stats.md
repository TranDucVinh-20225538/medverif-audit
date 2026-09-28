# QC stats

Counts below are copied from `data/extract_stats.json` and `data/llm_stats.json`.

## Extraction (Textbooks only)

- chunks: 125847
- sentences: 795464
- pool DOSE: 1541
- pool POLARITY: 652
- selected for generation: 360
- attempt cap per type: 180
- per-book cap: 25
- per-passage cap: 2
- seed: 42

### Extract drops

- DOSE:calculation: 161
- DOSE:duplicate_sentence: 43
- DOSE:multi_dose: 910
- DOSE:no_dose_context: 892
- DOSE:range_dose: 769
- DOSE:sentence_length: 187285
- DOSE:table_or_figure: 57832
- DOSE:unit_not_convertible: 43
- POLARITY:calculation: 161
- POLARITY:duplicate_sentence: 24
- POLARITY:multi_polarity: 51
- POLARITY:no_drug_context: 1882
- POLARITY:polarity_infinitive: 311
- POLARITY:sentence_length: 187285
- POLARITY:table_or_figure: 57832

### Selection drops

- DOSE:attempt_cap: 790
- DOSE:book_cap: 571
- DOSE:selected: 180
- POLARITY:attempt_cap: 213
- POLARITY:book_cap: 259
- POLARITY:selected: 180

## Generation and validation

- claim generator: Qwen/Qwen2.5-32B-Instruct @ `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`
- support validator and INV checker: microsoft/phi-4 @ `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`
- candidates attempted: 360
- attempted by type: `{"DOSE": 180, "POLARITY": 180}`
- passed span rule: 351
- validator YES: 326
- bases kept after INV check: 246
- bases kept by type: `{"DOSE": 155, "POLARITY": 91}`
- instances: 1695

### LLM and perturb drops

- inv_meaning_rejected: 80
- span_missing_in_claim: 4
- span_not_unique_in_claim: 5
- validator_no: 25

### Instances by type, condition, magnitude

- DOSE|C0|none: 155
- DOSE|E1-claim|x10: 155
- DOSE|E1-claim|x2: 155
- DOSE|E1-evid|x10: 155
- DOSE|E1-evid|x2: 155
- DOSE|E2|x10: 155
- DOSE|E2|x2: 155
- DOSE|INV-claim|unit_conversion: 155
- POLARITY|C0|none: 91
- POLARITY|E1-claim|flip: 91
- POLARITY|E1-evid|flip: 91
- POLARITY|E2|flip: 91
- POLARITY|INV-claim|rephrase: 91

## Label-validity fix (v2)

Main set excludes threshold-governed DOSE bases and scope-marked POLARITY bases.
Counts are copied from `data/v2/rebuild_stats.json` and the instance files.

- bases in (stage 1–2 kept): 246
- DOSE main: 126
- DOSE threshold (excluded from main, scored separately): 29
- POLARITY main: 78
- POLARITY scope excluded: 13
- scope terms: `{"but": 3, "only": 9, "unless": 1}`
- flip_mechanism on main POLARITY C0: `{"not_insert": 31, "lexical": 42, "not_remove": 5}`
- dose_kind on main DOSE: `{"prescriptive": 112, "descriptive": 14}`
- unit INV kept on main: 58
- main DOSE bases with no natural unit INV: 68
- instances main: 1456
- instances threshold: 243
- paraphrase YES bases (any candidate): 233
- main bases with no valid paraphrase INV: 0
- polarity paraphrase instances containing 'ought to': 0 / 78

### paraphrase YES by template

- clause_swap: 115
- front_clinical: 233
- front_record: 229
- trailing_note: 113
- wording_adults: 1
- wording_children: 6
- wording_patients: 1
