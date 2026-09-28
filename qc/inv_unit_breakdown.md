# INV-claim rows scored in cpu_early (n=68)

Matrix: `data/v3/instances_cpu_early.jsonl`. All **68** valid INV-claim rows here are **DOSE / unit_conversion** (57 main + 11 threshold). **POLARITY / rephrase** INV is not in cpu_early (0 rows).

Pass counts use the logged `verdict` (default score threshold 0.5; see `notes/environment_node30.md`).

## Pass rate by INV kind

| Verifier | Slice | All scored | Conditional on C0 PASS |
| --- | --- | --- | --- |
| v2a_minicheck | DOSE / unit_conversion | 8/68 | 8/66 |
| v2a_minicheck | POLARITY / rephrase (template) | — | — |
| v3_alignscore | DOSE / unit_conversion | 19/68 | 19/65 |
| v3_alignscore | POLARITY / rephrase (template) | — | — |
