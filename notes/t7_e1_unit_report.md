# T7 E1-unit vs E1-claim vs INV-unit (per verifier)

- E1-unit cohort: **230** instances (115 bases)
- Reference E1-claim x2/x10 (same bases): **207**
- Reference INV-unit (same bases): **62**

| verifier | E1-unit FAIL rate | n | E1-claim x2/x10 FAIL rate | n | INV-unit PASS rate | n |
|---|---:|---:|---:|---:|---:|---:|
| t6a_alignscore_base | 0.230 | 230/230 | — | 0/207 | — | 0/62 |
| t6a_granite_guardian | 0.343 | 230/230 | — | 0/207 | — | 0/62 |
| t6a_hhem | 0.057 | 230/230 | — | 0/207 | — | 0/62 |
| t6a_minicheck_deberta | 0.809 | 230/230 | — | 0/207 | — | 0/62 |
| t6a_minicheck_roberta | 0.348 | 230/230 | — | 0/207 | — | 0/62 |
| t6a_summac_conv | 0.691 | 230/230 | — | 0/207 | — | 0/62 |
| t6a_summac_zs | 0.370 | 230/230 | — | 0/207 | — | 0/62 |
| v1_medscore | 0.804 | 230/230 | 0.995 | 207/207 | 0.677 | 62/62 |
| v1b_medscore | 0.570 | 230/230 | 0.966 | 207/207 | 0.968 | 62/62 |
| v1c_medscore | 0.670 | 230/230 | 0.981 | 207/207 | 0.452 | 62/62 |
| v2a_minicheck | 0.365 | 230/230 | 0.957 | 207/207 | 0.081 | 62/62 |
| v2b_bespoke | 0.535 | 230/230 | 0.971 | 207/207 | 0.774 | 62/62 |
| v3_alignscore | 0.504 | 230/230 | 0.981 | 207/207 | 0.226 | 62/62 |
| v4_ragas_nli | 0.730 | 230/230 | 0.971 | 205/207 | 0.758 | 62/62 |
| v5_ragas_nli | 0.835 | 230/230 | 1.000 | 207/207 | 0.968 | 62/62 |
| v6_ragas_gpt4o_mini | 0.839 | 230/230 | 0.995 | 207/207 | 0.710 | 62/62 |
| v6_ragas_haiku45 | 0.935 | 230/230 | 0.995 | 207/207 | 0.952 | 62/62 |
| v6_ragas_llama31_8b | 0.674 | 230/230 | 0.995 | 207/207 | 0.258 | 62/62 |
| v6_ragas_mistral_small32 | 0.700 | 230/230 | 0.995 | 207/207 | 0.968 | 62/62 |
| v6_ragas_nli | — | 0/230 | — | 0/207 | — | 0/62 |

## Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate)

| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---:|---:|
| t6a_alignscore_base | 22 | 0.136 (22/22) | 0.182 (22/22) |
| t6a_granite_guardian | 23 | 0.304 (23/23) | 0.130 (23/23) |
| t6a_hhem | 22 | 0.000 (22/22) | 0.045 (22/22) |
| t6a_minicheck_deberta | 20 | 0.950 (20/20) | 0.800 (20/20) |
| t6a_minicheck_roberta | 21 | 0.143 (21/21) | 0.190 (21/21) |
| t6a_summac_conv | 15 | 0.600 (15/15) | 0.533 (15/15) |
| t6a_summac_zs | 19 | 0.368 (19/19) | 0.211 (19/19) |
| v1_medscore | 108 | 0.991 (108/108) | 0.602 (108/108) |
| v1b_medscore | 108 | 0.981 (108/108) | 0.139 (108/108) |
| v1c_medscore | 107 | 0.897 (107/107) | 0.439 (107/107) |
| v2a_minicheck | 104 | 0.519 (104/104) | 0.212 (104/104) |
| v2b_bespoke | 108 | 0.676 (108/108) | 0.370 (108/108) |
| v3_alignscore | 102 | 0.539 (102/102) | 0.412 (102/102) |
| v4_ragas_nli | 107 | 0.925 (106/107) | 0.542 (107/107) |
| v5_ragas_nli | 108 | 0.981 (108/108) | 0.685 (108/108) |
| v6_ragas_gpt4o_mini | 104 | 0.923 (104/104) | 0.740 (104/104) |
| v6_ragas_haiku45 | 105 | 0.981 (105/105) | 0.886 (105/105) |
| v6_ragas_llama31_8b | 104 | 0.837 (104/104) | 0.481 (104/104) |
| v6_ragas_mistral_small32 | 108 | 0.917 (108/108) | 0.472 (108/108) |
| v6_ragas_nli | 0 | — (0/0) | — (0/0) |

### LLM judges (|C0 PASS)

| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---:|---:|
| v1_medscore | 108 | 0.991 (108/108) | 0.602 (108/108) |
| v4_ragas_nli | 107 | 0.925 (106/107) | 0.542 (107/107) |
| v1b_medscore | 108 | 0.981 (108/108) | 0.139 (108/108) |
| v5_ragas_nli | 108 | 0.981 (108/108) | 0.685 (108/108) |

