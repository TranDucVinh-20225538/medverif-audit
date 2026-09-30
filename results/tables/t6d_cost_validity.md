# T6-D cost vs validity

Scope n=533 (`instances_t6_scope.jsonl`).

| Verifier | $/1k | Paper BAcc | Inv DOSE | Sens E1 x2 | Sens E1 x10 | INV-unit all | INV-unit nat | POL INV tmpl |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1_medscore | 0.026 | 0.72 | 0.671 | 0.983 | 1.000 | 0.671 | 0.657 | 0.971 |
| v1b_medscore | 1.045 | — | — | 0.916 | 0.992 | 0.971 | 1.000 | 1.000 |
| v1c_medscore | 0.059 | — | — | — | — | 1.000 | — | 1.000 |
| v2a_minicheck | 0.000 | 0.78 | — | 0.965 | 0.948 | 0.088 | 0.091 | 0.971 |
| v3_alignscore | 0.000 | 0.81 | — | 0.982 | 0.973 | 0.246 | 0.182 | 1.000 |
| v4_ragas_nli | 0.000 | 0.75 | — | 0.975 | 1.000 | 0.842 | 0.864 | 1.000 |
| v5_ragas_nli | 4.931 | — | — | 1.000 | 1.000 | 1.000 | 1.000 | — |
| v6_ragas_gpt4o_mini | 0.191 | — | — | — | — | 1.000 | — | 1.000 |
| v6_ragas_haiku45 | 1.647 | — | — | — | — | 1.000 | — | 1.000 |
| v6_ragas_llama31_8b | 0.022 | — | — | — | — | 1.000 | — | 1.000 |
| v6_ragas_mistral_small32 | 0.088 | — | — | — | — | 1.000 | — | 1.000 |
