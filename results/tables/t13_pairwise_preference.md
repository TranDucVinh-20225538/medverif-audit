# T13 — pairwise preference (selection harm)

- **Cohort:** all **valid main DOSE** bases (`instances_main.jsonl`).
- **E1-unit ×1000:** **all** valid `E1-unit-claim` / `E1-unit-evid` rows in `data/t7/instances_e1_unit.jsonl` (**112** claim on main DOSE); generator validated by **30/30** PI sample (`qc/t7_PI_ok_labels.csv`).
- **INV-unit natural:** `rule_natural_unit_conversion_label` + `effective_unit_natural_y` (same gate as T9).
- **Metric:** per base pair, contribute **P(wrong ≥ correct)** — 1 if score(wrong)>score(correct), **0.5 on ties**, 0 if lower. **Cluster bootstrap** over bases (95% CI).
- **Scores:** continuous where logged; else LLM **verdict** (PASS=1, FAIL=0) and **logprob** when present.

- Main DOSE bases: **114**. Structural pair counts (both slices exist): (E1-unit-claim×1000 vs INV-unit natural) **55**, (E1-unit-claim×1000 vs INV-unit (all)) **66**, (E1-unit-claim×1000 vs C0) **112**, (E1-unit-evid×1000 vs C0) **112**, (E1-claim×2 vs INV-unit natural) **51**.

## Pairwise table (all verifiers)

| verifier | family | mode | (1) ×1000 vs INV nat | (1′) ×1000 vs INV all | (2) ×1000 vs C0 | (2′) evid×1000 vs C0 | (3) E1×2 vs INV |
|---|---|---|---|---|---|---|---|
| v2a_minicheck | encoders | continuous | 0.800 [0.691, 0.891] (n=55) | 0.727 [0.621, 0.833] (n=66) | 0.089 [0.045, 0.143] (n=112) | 0.089 [0.036, 0.143] (n=112) | 0.294 [0.176, 0.412] (n=51) |
| v3_alignscore | encoders | continuous | 0.764 [0.655, 0.873] (n=55) | 0.682 [0.561, 0.788] (n=66) | 0.036 [0.009, 0.071] (n=112) | 0.062 [0.018, 0.107] (n=112) | 0.039 [0.000, 0.098] (n=51) |
| t6a_minicheck_roberta | encoders | continuous | — | — | 0.000 [0.000, 0.000] (n=22) | 0.045 [0.000, 0.136] (n=22) | — |
| t6a_minicheck_deberta | encoders | continuous | — | — | 0.000 [0.000, 0.000] (n=22) | 0.045 [0.000, 0.136] (n=22) | — |
| t6a_alignscore_base | encoders | continuous | — | — | 0.136 [0.000, 0.273] (n=22) | 0.182 [0.045, 0.364] (n=22) | — |
| t6a_summac_zs | encoders | continuous | — | — | 0.364 [0.182, 0.591] (n=22) | 0.159 [0.045, 0.318] (n=22) | — |
| t6a_summac_conv | encoders | continuous | — | — | 0.205 [0.091, 0.318] (n=22) | 0.182 [0.068, 0.295] (n=22) | — |
| t6a_hhem | encoders | continuous | — | — | 0.364 [0.182, 0.591] (n=22) | 0.364 [0.182, 0.591] (n=22) | — |
| t6a_granite_guardian | encoders | continuous | — | — | 0.000 [0.000, 0.000] (n=22) | 0.045 [0.000, 0.136] (n=22) | — |
| v2b_bespoke | llm_checker | continuous | 0.200 [0.109, 0.309] (n=55) | 0.227 [0.136, 0.333] (n=66) | 0.000 [0.000, 0.000] (n=112) | 0.027 [0.000, 0.062] (n=112) | 0.039 [0.000, 0.098] (n=51) |
| v6_ragas_llama31_8b | llm_judges | continuous | 0.509 [0.436, 0.582] (n=55) | 0.477 [0.409, 0.545] (n=66) | 0.090 [0.054, 0.126] (n=111) | 0.266 [0.216, 0.311] (n=111) | 0.392 [0.324, 0.451] (n=51) |
| v1c_medscore | llm_judges | continuous | 0.336 [0.255, 0.409] (n=55) | 0.333 [0.265, 0.402] (n=66) | 0.058 [0.027, 0.094] (n=112) | 0.286 [0.237, 0.335] (n=112) | 0.275 [0.206, 0.343] (n=51) |
| v1_medscore | llm_judges | continuous | 0.182 [0.118, 0.245] (n=55) | 0.174 [0.121, 0.235] (n=66) | 0.004 [0.000, 0.013] (n=112) | 0.054 [0.027, 0.085] (n=112) | 0.186 [0.127, 0.255] (n=51) |
| v6_ragas_gpt4o_mini | llm_judges | continuous | 0.173 [0.109, 0.236] (n=55) | 0.189 [0.129, 0.250] (n=66) | 0.054 [0.027, 0.085] (n=112) | 0.143 [0.103, 0.188] (n=112) | 0.137 [0.078, 0.196] (n=51) |
| v4_ragas_nli | llm_judges | continuous | 0.132 [0.066, 0.198] (n=53) | 0.133 [0.078, 0.195] (n=64) | 0.014 [0.000, 0.032] (n=108) | 0.089 [0.051, 0.126] (n=107) | 0.173 [0.102, 0.255] (n=49) |
| v6_ragas_mistral_small32 | llm_judges | continuous | 0.091 [0.045, 0.145] (n=55) | 0.076 [0.038, 0.121] (n=66) | 0.040 [0.018, 0.067] (n=112) | 0.259 [0.214, 0.304] (n=112) | 0.039 [0.010, 0.078] (n=51) |
| v6_ragas_haiku45 | llm_judges | continuous | 0.045 [0.009, 0.091] (n=55) | 0.038 [0.008, 0.076] (n=66) | 0.022 [0.004, 0.045] (n=112) | 0.071 [0.040, 0.107] (n=112) | 0.049 [0.010, 0.088] (n=51) |
| v1b_medscore | llm_judges | continuous | 0.036 [0.009, 0.073] (n=55) | 0.030 [0.008, 0.061] (n=66) | 0.009 [0.000, 0.022] (n=112) | 0.424 [0.388, 0.455] (n=112) | 0.069 [0.020, 0.118] (n=51) |
| v5_ragas_nli | llm_judges | continuous | 0.036 [0.009, 0.073] (n=55) | 0.030 [0.008, 0.061] (n=66) | 0.009 [0.000, 0.022] (n=112) | 0.156 [0.112, 0.196] (n=112) | 0.020 [0.000, 0.049] (n=51) |
| t6_alignscore_base | other | continuous | — | — | 0.136 [0.000, 0.273] (n=22) | 0.182 [0.045, 0.364] (n=22) | — |
| t6_bespoke_minicheck | other | continuous | 0.200 [0.109, 0.309] (n=55) | 0.227 [0.136, 0.333] (n=66) | 0.000 [0.000, 0.000] (n=112) | 0.027 [0.000, 0.062] (n=112) | 0.039 [0.000, 0.098] (n=51) |
| t6_granite_guardian | other | continuous | — | — | 0.000 [0.000, 0.000] (n=22) | 0.045 [0.000, 0.136] (n=22) | — |
| t6_hhem | other | continuous | — | — | 0.364 [0.182, 0.591] (n=22) | 0.364 [0.182, 0.591] (n=22) | — |
| t6_minicheck_deberta | other | continuous | — | — | 0.000 [0.000, 0.000] (n=22) | 0.045 [0.000, 0.136] (n=22) | — |
| t6_minicheck_roberta | other | continuous | — | — | 0.000 [0.000, 0.000] (n=22) | 0.045 [0.000, 0.136] (n=22) | — |
| t6_summac_conv | other | continuous | — | — | 0.205 [0.091, 0.318] (n=22) | 0.182 [0.068, 0.295] (n=22) | — |
| t6_summac_zs | other | continuous | — | — | 0.364 [0.182, 0.591] (n=22) | 0.159 [0.045, 0.318] (n=22) | — |
| v6_ragas_nli | other | none | — | — | — | — | — |

**Figure (pair 1):** `results/figures/t13_pairwise_x1000_vs_inv.png`

## Appendix — superseded best-of-N (footnote only)

The prior **18-base** `PI_ok=Y` best-of-N argmax design was underpowered (×1000 in only 3 bases) and its **tie → lower rank** rule biased **binary** LLM judges. See commit `97d0b79` / `notes/t13_best_of_n.json` for that exploratory table; **do not use for inference.** Primary T13 estimand is pairwise above.

- Legacy example: v1_medscore P(select wrong) ≈ 0.05555555555555555 on n=18 bases.
