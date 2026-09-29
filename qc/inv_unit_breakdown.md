# INV-claim rows in cpu_early

Matrix: `data/v3/instances_cpu_early.jsonl` — **118** valid INV-claim rows: **84** DOSE `unit_conversion`, **34** POLARITY template `rephrase`.

V2/V3 node30 scores (first tranche, n=1216) cover **DOSE unit_conversion only** (8/68 and 19/68 PASS @ 0.5). POLARITY `rephrase` rows are in `data/v3/instances_score_pending_node30.jsonl` (awaiting node30).

Pass counts below use logged `verdict` (score > 0.5; `notes/environment_node30.md`).

## Pass rate by INV kind (scored rows only)

| Verifier | Slice | All scored | Conditional on C0 PASS |
| --- | --- | --- | --- |
| v2a_minicheck | DOSE / unit_conversion | 8/66 | 8/64 |
| v2a_minicheck | POLARITY / rephrase (template) | 33/34 | 31/31 |
| v3_alignscore | DOSE / unit_conversion | 18/66 | 18/63 |
| v3_alignscore | POLARITY / rephrase (template) | 34/34 | 34/34 |
