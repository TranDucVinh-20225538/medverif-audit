# T14 / T3 filter view (#3 — existing scores only)

At each verifier’s **default threshold** (see `configs/verifiers.yaml`):
- **keep rate ×1000** = P(PASS | E1-unit-claim ×1000 wrong) — bad if high (= **1−US**).
- **drop rate INV natural** = P(FAIL | INV-unit natural correct) — bad if high (= **1−QI**).
- **T13 pair (1)** = P(score(×1000) ≥ score(INV natural)) with tie=0.5.

- ×1000 claim instances (main DOSE): **112**; INV natural: **55**.

| verifier | family | keep ×1000 | drop INV | T13 pair(1) | n ×1000 | n INV |
|---|---|---:|---:|---:|---:|---:|
| t6a_alignscore_base | encoders | 0.795 | — | — | 112 | 0 |
| t6a_granite_guardian | encoders | 0.527 | — | — | 112 | 0 |
| t6a_hhem | encoders | 0.964 | — | — | 112 | 0 |
| t6a_minicheck_deberta | encoders | 0.125 | — | — | 112 | 0 |
| t6a_minicheck_roberta | encoders | 0.598 | — | — | 112 | 0 |
| t6a_summac_conv | encoders | 0.330 | — | — | 112 | 0 |
| t6a_summac_zs | encoders | 0.607 | — | — | 112 | 0 |
| v2a_minicheck | encoders | 0.482 | 0.909 | 0.800 | 112 | 55 |
| v3_alignscore | encoders | 0.446 | 0.764 | 0.764 | 112 | 55 |
| v2b_bespoke | llm_checker | 0.321 | 0.200 | 0.200 | 112 | 55 |
| v1_medscore | llm_judges | 0.009 | 0.345 | 0.182 | 112 | 55 |
| v1b_medscore | llm_judges | 0.018 | 0.036 | 0.036 | 112 | 55 |
| v1c_medscore | llm_judges | 0.107 | 0.509 | 0.336 | 112 | 55 |
| v4_ragas_nli | llm_judges | 0.027 | 0.226 | 0.132 | 112 | 53 |
| v5_ragas_nli | llm_judges | 0.018 | 0.036 | 0.036 | 112 | 55 |
| v6_ragas_gpt4o_mini | llm_judges | 0.071 | 0.236 | 0.173 | 112 | 55 |
| v6_ragas_haiku45 | llm_judges | 0.018 | 0.055 | 0.045 | 112 | 55 |
| v6_ragas_llama31_8b | llm_judges | 0.152 | 0.764 | 0.509 | 112 | 55 |
| v6_ragas_mistral_small32 | llm_judges | 0.080 | 0.036 | 0.091 | 112 | 55 |

Figure: `results/figures/t14_t3_filter_reward.png`

