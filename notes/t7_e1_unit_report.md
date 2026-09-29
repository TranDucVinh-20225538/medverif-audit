# T7 E1-unit vs E1-claim vs INV-unit (per verifier)

- E1-unit cohort: **230** instances (115 bases)
- Reference E1-claim x2/x10 (same bases): **215**
- Reference INV-unit (same bases): **66**

| verifier | E1-unit FAIL rate | n | E1-claim x2/x10 FAIL rate | n | INV-unit PASS rate | n |
|---|---:|---:|---:|---:|---:|---:|
| t6a_alignscore_base | 0.230 | 230/230 | — | 0/215 | — | 0/66 |
| t6a_granite_guardian | 0.343 | 230/230 | — | 0/215 | — | 0/66 |
| t6a_hhem | 0.057 | 230/230 | — | 0/215 | — | 0/66 |
| t6a_minicheck_deberta | 0.804 | 230/230 | — | 0/215 | — | 0/66 |
| t6a_minicheck_roberta | 0.348 | 230/230 | — | 0/215 | — | 0/66 |
| t6a_summac_conv | 0.691 | 230/230 | — | 0/215 | — | 0/66 |
| t6a_summac_zs | 0.370 | 230/230 | — | 0/215 | — | 0/66 |
| v1_medscore | 0.804 | 230/230 | 0.991 | 215/215 | 0.667 | 66/66 |
| v1b_medscore | 0.570 | 230/230 | 0.963 | 215/215 | 0.970 | 66/66 |
| v1c_medscore | 0.670 | 230/230 | 0.981 | 215/215 | 0.470 | 66/66 |
| v2a_minicheck | 0.365 | 230/230 | 0.953 | 215/215 | 0.091 | 55/66 |
| v2b_bespoke | 0.535 | 230/230 | 0.958 | 215/215 | 0.788 | 66/66 |
| v3_alignscore | 0.504 | 230/230 | 0.981 | 215/215 | 0.236 | 55/66 |
| v4_ragas_nli | 0.730 | 230/230 | 0.953 | 215/215 | 0.742 | 66/66 |
| v5_ragas_nli | 0.835 | 230/230 | 1.000 | 215/215 | 0.970 | 66/66 |
| v6_ragas_gpt4o_mini | 0.839 | 230/230 | 0.991 | 215/215 | 0.712 | 66/66 |
| v6_ragas_haiku45 | 0.935 | 230/230 | 0.991 | 215/215 | 0.955 | 66/66 |
| v6_ragas_llama31_8b | 0.674 | 230/230 | 0.986 | 215/215 | 0.258 | 66/66 |
| v6_ragas_mistral_small32 | 0.700 | 230/230 | 0.991 | 215/215 | 0.970 | 66/66 |
| v6_ragas_nli | — | 0/230 | — | 0/215 | — | 0/66 |

## Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate)

| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---:|---:|
| t6a_alignscore_base | 21 | 0.095 (21/21) | 0.143 (21/21) |
| t6a_granite_guardian | 22 | 0.273 (22/22) | 0.091 (22/22) |
| t6a_hhem | 21 | 0.000 (21/21) | 0.000 (21/21) |
| t6a_minicheck_deberta | 19 | 0.947 (19/19) | 0.789 (19/19) |
| t6a_minicheck_roberta | 20 | 0.150 (20/20) | 0.150 (20/20) |
| t6a_summac_conv | 14 | 0.643 (14/14) | 0.571 (14/14) |
| t6a_summac_zs | 18 | 0.389 (18/18) | 0.222 (18/18) |
| v1_medscore | 112 | 0.991 (112/112) | 0.607 (112/112) |
| v1b_medscore | 112 | 0.982 (112/112) | 0.152 (112/112) |
| v1c_medscore | 111 | 0.901 (111/111) | 0.441 (111/111) |
| v2a_minicheck | 108 | 0.500 (108/108) | 0.204 (108/108) |
| v2b_bespoke | 112 | 0.679 (112/112) | 0.366 (112/112) |
| v3_alignscore | 106 | 0.538 (106/106) | 0.425 (106/106) |
| v4_ragas_nli | 108 | 0.925 (107/108) | 0.556 (108/108) |
| v5_ragas_nli | 112 | 0.982 (112/112) | 0.688 (112/112) |
| v6_ragas_gpt4o_mini | 108 | 0.926 (108/108) | 0.741 (108/108) |
| v6_ragas_haiku45 | 109 | 0.982 (109/109) | 0.881 (109/109) |
| v6_ragas_llama31_8b | 108 | 0.843 (108/108) | 0.491 (108/108) |
| v6_ragas_mistral_small32 | 112 | 0.920 (112/112) | 0.482 (112/112) |
| v6_ragas_nli | 0 | — (0/0) | — (0/0) |

### LLM judges (|C0 PASS)

| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---:|---:|
| v1_medscore | 112 | 0.991 (112/112) | 0.607 (112/112) |
| v4_ragas_nli | 108 | 0.925 (107/108) | 0.556 (108/108) |
| v1b_medscore | 112 | 0.982 (112/112) | 0.152 (112/112) |
| v5_ragas_nli | 112 | 0.982 (112/112) | 0.688 (112/112) |

