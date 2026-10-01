# Journal chain 2 status

Generated 2026-10-01 16:28 +07 by `scripts/journal2/jr2_status.py`.

Slurm jobs: `{"FINAL":"62084","RD1":"62079","UNF":"62082","AT1":"62083","RD4j":"62080","RD4s":"62081","submitted":"2026-10-01T14:53:21+07:00"}`

## Stage markers

| stage | finished | info |
|---|---|---|
| RD1_questions | 2026-10-01T14:53:23+0700 | slurm_job=62079, labels=200, questions=364, drugs_with_question=197, out=/data2/hpcshared/medverif-audit/results/journal2/real_dose/questions.jsonl |
| RD2_generate | 2026-10-01T15:06:48+0700 | slurm_job=62079, answers=1456, expected=1456 |
| RD3_extract | 2026-10-01T15:06:49+0700 | slurm_job=62079, answers=1456, instances=1451, subtypes={'unit_error|per_m2': 5, 'unit_error|per_kg': 8, 'value_error|other': 92, 'basis_error|per_kg': 30, 'basis_error|per_m2': 2, 'unit_error|time_ba |
| RD4_small | 2026-10-01T16:22:22+0700 | slurm_job=62081, checkers=['t6a_minicheck_roberta', 't6a_minicheck_deberta', 't6a_alignscore_base', 'v2a_minicheck', 'v3_alignscore'] |
| RD5_report | 2026-10-01T16:27:10+0700 | slurm_job=62084, spent_usd=0.2422 |

## Real-world dose errors (RD)

- questions 364, answers 1456, instances 1451
- scores: t6_alignscore_base 1451, t6_minicheck_deberta 1451, t6_minicheck_roberta 1451, v2a_minicheck 1451, v3_alignscore 1451, v4_ragas_nli 1388
- real-dose API spend $0.2422 of cap $5.00 (chain 1 ledger untouched)
- report: notes/real_dose_errors.md present

## Unit-normalization fix (UNF)

| checker | orig rows | unf rows |
|---|---|---|
| t6a_minicheck_roberta | 716 | 637 |
| t6a_minicheck_deberta | 716 | 637 |
| t6a_alignscore_base | 716 | 637 |
| v2a_minicheck | 637 | 637 |
| v3_alignscore | 637 | 637 |

- report: notes/unit_normalization_fix.md present

## Attribution (AT)

- attr_as_large.jsonl: 486 items
- attr_mc_ft5.jsonl: 486 items
- attr_mc_roberta.jsonl: 486 items
- report: notes/attribution_mechanism.md present

