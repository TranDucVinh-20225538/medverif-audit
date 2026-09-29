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
| v1b_medscore | 0.570 | 230/230 | 0.951 | 432/432 | 0.970 | 101/128 |
| v1c_medscore | 0.670 | 230/230 | 0.981 | 432/432 | 0.460 | 124/128 |
| v2a_minicheck | 0.365 | 230/230 | 0.954 | 432/432 | 0.099 | 81/128 |
| v2b_bespoke | 0.535 | 230/230 | 0.961 | 432/432 | 0.812 | 101/128 |
| v3_alignscore | 0.504 | 230/230 | 0.977 | 432/432 | 0.259 | 81/128 |
| v4_ragas_nli | 0.896 | 230/230 | 0.995 | 432/432 | 0.861 | 101/128 |
| v5_ragas_nli | 0.835 | 230/230 | 1.000 | 432/432 | 0.980 | 101/128 |
| v6_ragas_gpt4o_mini | 0.839 | 230/230 | 0.991 | 432/432 | 0.703 | 101/128 |
| v6_ragas_haiku45 | 0.935 | 230/230 | 0.991 | 432/432 | 0.960 | 101/128 |
| v6_ragas_llama31_8b | 0.674 | 230/230 | 0.986 | 432/432 | 0.267 | 101/128 |
| v6_ragas_mistral_small32 | 0.700 | 230/230 | 0.991 | 432/432 | 0.970 | 101/128 |
| v6_ragas_nli | — | 0/230 | — | 0/432 | — | 0/128 |

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
| v1_medscore | 115 | 0.991 (115/115) | 0.617 (115/115) |
| v1b_medscore | 115 | 0.983 (115/115) | 0.157 (115/115) |
| v1c_medscore | 114 | 0.904 (114/114) | 0.447 (114/114) |
| v2a_minicheck | 111 | 0.486 (111/111) | 0.198 (111/111) |
| v2b_bespoke | 115 | 0.687 (115/115) | 0.383 (115/115) |
| v3_alignscore | 109 | 0.541 (109/109) | 0.431 (109/109) |
| v4_ragas_nli | 114 | 1.000 (111/114) | 0.816 (114/114) |
| v5_ragas_nli | 115 | 0.983 (115/115) | 0.687 (115/115) |
| v6_ragas_gpt4o_mini | 111 | 0.928 (111/111) | 0.739 (111/111) |
| v6_ragas_haiku45 | 112 | 0.982 (112/112) | 0.884 (112/112) |
| v6_ragas_llama31_8b | 110 | 0.845 (110/110) | 0.491 (110/110) |
| v6_ragas_mistral_small32 | 115 | 0.922 (115/115) | 0.478 (115/115) |
| v6_ragas_nli | 0 | — (0/0) | — (0/0) |

### LLM judges (|C0 PASS)

| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---:|---:|
| v1_medscore | 115 | 0.991 (115/115) | 0.617 (115/115) |
| v4_ragas_nli | 114 | 1.000 (111/114) | 0.816 (114/114) |
| v1b_medscore | 115 | 0.983 (115/115) | 0.157 (115/115) |
| v5_ragas_nli | 115 | 0.983 (115/115) | 0.687 (115/115) |

