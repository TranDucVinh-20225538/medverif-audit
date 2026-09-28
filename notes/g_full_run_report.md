# G full run — INV paraphrase (OpenRouter)

- Generator: `qwen/qwen-2.5-72b-instruct`
- Validator: `google/gemini-2.5-flash` (see `notes/g_inv_validator_model.json`)
- Bases: 133 valid main (DOSE + POLARITY, rule B filter)
- Accepted: **109/133** (82.0%)

## Pass rate by type

| type | passed | total | rate |
|------|--------|-------|------|
| DOSE | 96 | 119 | 80.7% |
| POLARITY | 13 | 14 | 92.9% |

- Attempts log: `data/v3/para_attempts_g.jsonl`
- Instances: `data/v3/instances_g_inv_paraphrase.jsonl`
- Manual review: `qc/inv_manual_review.csv`

