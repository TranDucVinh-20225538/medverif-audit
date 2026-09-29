# T13 — best-of-N selection harm

- **Cohort:** DOSE bases with `PI_ok=Y` in `qc/dose3_labels.csv`.
- **Pool per base:** human-gated C0, INV-unit (natural), E1×2 claim+evid, E1-unit-claim×1000 (T7 PI_ok), T4 eco human-correct answers when labeled.
- **Selection:** argmax verifier score; **ties → lower-ranked candidate** (higher rank index).
- **Scores:** continuous `score` / parser fields when present; else PASS=1 / FAIL=0.

- Bases in cohort: **18**; with ≥1 candidate: **18**.

## Selection harm

| verifier | score mode | (a) P(wrong) | (b) P(×1000) | (c) P(inv below wrong) |
|---|---|---:|---:|---:|
| v1b_medscore | continuous | 0.111 [0.000, 0.278] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v4_ragas_nli | continuous | 0.111 [0.000, 0.278] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v1_medscore | continuous | 0.056 [0.000, 0.167] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v1c_medscore | continuous | 0.056 [0.000, 0.167] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| t6_alignscore_base | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6_bespoke_minicheck | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.091 [0.000, 0.273] (n=11) |
| t6_granite_guardian | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6_hhem | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6_minicheck_deberta | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6_minicheck_roberta | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6_summac_conv | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6_summac_zs | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6a_alignscore_base | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6a_granite_guardian | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6a_hhem | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6a_minicheck_deberta | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6a_minicheck_roberta | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6a_summac_conv | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| t6a_summac_zs | continuous | 0.000 [0.000, 0.000] (n=10) | 0.000 [0.000, 0.000] (n=3) | — |
| v2a_minicheck | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.364 [0.091, 0.636] (n=11) |
| v2b_bespoke | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.091 [0.000, 0.273] (n=11) |
| v3_alignscore | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.182 [0.000, 0.455] (n=11) |
| v5_ragas_nli | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v6_ragas_gpt4o_mini | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v6_ragas_haiku45 | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v6_ragas_llama31_8b | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v6_ragas_mistral_small32 | continuous | 0.000 [0.000, 0.000] (n=18) | 0.000 [0.000, 0.000] (n=3) | 0.000 [0.000, 0.000] (n=11) |
| v6_ragas_nli | continuous | 0.000 [0.000, 0.000] (n=5) | 0.000 [0.000, 0.000] (n=1) | — |

## Reward view (INV-unit − ×1000 wrong), paired by base

| verifier | mean Δscore | 95% bootstrap CI | n pairs |
|---|---:|---|---:|
| t6_alignscore_base | — | 0 |
| t6_bespoke_minicheck | 0.3993 [0.0728, 0.6218] | 3 |
| t6_granite_guardian | — | 0 |
| t6_hhem | — | 0 |
| t6_minicheck_deberta | — | 0 |
| t6_minicheck_roberta | — | 0 |
| t6_summac_conv | — | 0 |
| t6_summac_zs | — | 0 |
| t6a_alignscore_base | — | 0 |
| t6a_granite_guardian | — | 0 |
| t6a_hhem | — | 0 |
| t6a_minicheck_deberta | — | 0 |
| t6a_minicheck_roberta | — | 0 |
| t6a_summac_conv | — | 0 |
| t6a_summac_zs | — | 0 |
| v1_medscore | 0.6667 [0.0000, 1.0000] | 3 |
| v1b_medscore | 1.0000 [1.0000, 1.0000] | 3 |
| v1c_medscore | 0.6667 [0.0000, 1.0000] | 3 |
| v2a_minicheck | -0.2992 [-0.8647, 0.0079] | 3 |
| v2b_bespoke | 0.3993 [0.0728, 0.6218] | 3 |
| v3_alignscore | 0.0058 [-0.0025, 0.0178] | 3 |
| v4_ragas_nli | 0.6667 [0.0000, 1.0000] | 3 |
| v5_ragas_nli | 1.0000 [1.0000, 1.0000] | 3 |
| v6_ragas_gpt4o_mini | 1.0000 [1.0000, 1.0000] | 3 |
| v6_ragas_haiku45 | 1.0000 [1.0000, 1.0000] | 3 |
| v6_ragas_llama31_8b | 0.0000 [0.0000, 0.0000] | 3 |
| v6_ragas_mistral_small32 | 1.0000 [1.0000, 1.0000] | 3 |
| v6_ragas_nli | — | 0 |

Figure: `results/figures/t13_best_of_n_wrong_select.png`

