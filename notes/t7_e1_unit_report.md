# T7 E1-unit vs E1-claim vs INV-unit (per verifier)

- E1-unit cohort: **230** instances (115 bases)
- Reference E1-claim x2/x10 (same bases): **432**
- Reference INV-unit (same bases): **128**

| verifier | E1-unit FAIL rate | n | E1-claim x2/x10 FAIL rate | n | INV-unit PASS rate | n |
|---|---:|---:|---:|---:|---:|---:|
| t6a_alignscore_base | 0.230 | 230/230 | — | 0/432 | — | 0/128 |
| t6a_granite_guardian | 0.343 | 230/230 | — | 0/432 | — | 0/128 |
| t6a_hhem | 0.057 | 230/230 | — | 0/432 | — | 0/128 |
| t6a_minicheck_deberta | 0.804 | 230/230 | — | 0/432 | — | 0/128 |
| t6a_minicheck_roberta | 0.348 | 230/230 | — | 0/432 | — | 0/128 |
| t6a_summac_conv | 0.691 | 230/230 | — | 0/432 | — | 0/128 |
| t6a_summac_zs | 0.370 | 230/230 | — | 0/432 | — | 0/128 |
| v1_medscore | 0.804 | 230/230 | 0.991 | 432/432 | 0.711 | 128/128 |
| v1b_medscore | 0.570 | 230/230 | — | 0/432 | — | 0/128 |
| v1c_medscore | 0.670 | 230/230 | — | 0/432 | — | 0/128 |
| v2a_minicheck | 0.365 | 230/230 | — | 0/432 | — | 0/128 |
| v2b_bespoke | 0.535 | 230/230 | — | 0/432 | — | 0/128 |
| v3_alignscore | 0.504 | 230/230 | — | 0/432 | — | 0/128 |
| v4_ragas_nli | 0.896 | 230/230 | 0.995 | 432/432 | 0.861 | 101/128 |
| v5_ragas_nli | 0.835 | 230/230 | — | 0/432 | — | 0/128 |
| v6_ragas_gpt4o_mini | 0.839 | 230/230 | — | 0/432 | — | 0/128 |
| v6_ragas_haiku45 | 0.935 | 230/230 | — | 0/432 | — | 0/128 |
| v6_ragas_llama31_8b | 0.674 | 230/230 | — | 0/432 | — | 0/128 |
| v6_ragas_mistral_small32 | 0.700 | 230/230 | — | 0/432 | — | 0/128 |
| v6_ragas_nli | — | 0/230 | — | 0/432 | — | 0/128 |

## Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate)

| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---:|---:|
| t6a_alignscore_base | 0 | — (0/0) | — (0/0) |
| t6a_granite_guardian | 0 | — (0/0) | — (0/0) |
| t6a_hhem | 0 | — (0/0) | — (0/0) |
| t6a_minicheck_deberta | 0 | — (0/0) | — (0/0) |
| t6a_minicheck_roberta | 0 | — (0/0) | — (0/0) |
| t6a_summac_conv | 0 | — (0/0) | — (0/0) |
| t6a_summac_zs | 0 | — (0/0) | — (0/0) |
| v1_medscore | 115 | 0.991 (115/115) | 0.617 (115/115) |
| v1b_medscore | 0 | — (0/0) | — (0/0) |
| v1c_medscore | 0 | — (0/0) | — (0/0) |
| v2a_minicheck | 0 | — (0/0) | — (0/0) |
| v2b_bespoke | 0 | — (0/0) | — (0/0) |
| v3_alignscore | 0 | — (0/0) | — (0/0) |
| v4_ragas_nli | 114 | 1.000 (111/114) | 0.816 (114/114) |
| v5_ragas_nli | 0 | — (0/0) | — (0/0) |
| v6_ragas_gpt4o_mini | 0 | — (0/0) | — (0/0) |
| v6_ragas_haiku45 | 0 | — (0/0) | — (0/0) |
| v6_ragas_llama31_8b | 0 | — (0/0) | — (0/0) |
| v6_ragas_mistral_small32 | 0 | — (0/0) | — (0/0) |
| v6_ragas_nli | 0 | — (0/0) | — (0/0) |

