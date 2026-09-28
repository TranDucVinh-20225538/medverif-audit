# INV-claim rows in cpu_early

Matrix: `data/v3/instances_cpu_early.jsonl` — **146** valid INV-claim rows: **68** DOSE `unit_conversion`, **78** POLARITY template `rephrase`.

V2/V3 node30 scores (first tranche, n=1216) cover **DOSE unit_conversion only** (8/68 and 19/68 PASS @ 0.5). POLARITY `rephrase` rows are in `data/v3/instances_score_pending_node30.jsonl` (awaiting node30).

Pass counts below use logged `verdict` (score > 0.5; `notes/environment_node30.md`).

## Pass rate by INV kind (scored rows only)

| Verifier | Slice | All scored | Conditional on C0 PASS |
| --- | --- | --- | --- |
| v2a_minicheck | DOSE / unit_conversion | 8/68 | 8/66 |
| v2a_minicheck | POLARITY / rephrase (template) | — | — |
| v3_alignscore | DOSE / unit_conversion | 19/68 | 19/65 |
| v3_alignscore | POLARITY / rephrase (template) | — | — |
