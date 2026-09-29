# T13 — pairwise preference (selection harm)

- **Cohort:** all **valid main DOSE** bases (`instances_main.jsonl`).
- **E1-unit-claim ×1000:** instances in `qc/t7_PI_ok_labels.csv` with `PI_ok=Y` (30/30 PI sample; **16** claim rows).
- **INV-unit natural:** `rule_natural_unit_conversion_label` + `effective_unit_natural_y` (same gate as T9).
- **Metric:** per base pair, contribute **P(wrong ≥ correct)** — 1 if score(wrong)>score(correct), **0.5 on ties**, 0 if lower. **Cluster bootstrap** over bases (95% CI).
- **Scores:** continuous where logged; else LLM **verdict** (PASS=1, FAIL=0) and **logprob** when present.

- Main DOSE bases: **114**. Structural pair counts (both slices exist): (E1-unit-claim×1000 vs INV-unit natural) **8**, (E1-unit-claim×1000 vs C0) **15**, (E1-claim×2 vs INV-unit natural) **51**.

## Pairwise table (all verifiers)

| verifier | mode | (1) ×1000 vs INV | (2) ×1000 vs C0 | (3) E1×2 vs INV |
|---|---|---|---|---|
| t6_alignscore_base | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6_bespoke_minicheck | continuous | 0.250 [0.000, 0.625] (n=8) | 0.000 [0.000, 0.000] (n=15) | 0.039 [0.000, 0.098] (n=51) |
| t6_granite_guardian | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6_hhem | continuous | — | 0.500 [0.000, 1.000] (n=4) | — |
| t6_minicheck_deberta | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6_minicheck_roberta | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6_summac_conv | continuous | — | 0.125 [0.000, 0.375] (n=4) | — |
| t6_summac_zs | continuous | — | 0.250 [0.000, 0.750] (n=4) | — |
| t6a_alignscore_base | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6a_granite_guardian | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6a_hhem | continuous | — | 0.500 [0.000, 1.000] (n=4) | — |
| t6a_minicheck_deberta | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6a_minicheck_roberta | continuous | — | 0.000 [0.000, 0.000] (n=4) | — |
| t6a_summac_conv | continuous | — | 0.125 [0.000, 0.375] (n=4) | — |
| t6a_summac_zs | continuous | — | 0.250 [0.000, 0.750] (n=4) | — |
| v2a_minicheck | continuous | 0.750 [0.375, 1.000] (n=8) | 0.133 [0.000, 0.333] (n=15) | 0.294 [0.176, 0.412] (n=51) |
| v3_alignscore | continuous | 0.625 [0.250, 1.000] (n=8) | 0.067 [0.000, 0.200] (n=15) | 0.039 [0.000, 0.098] (n=51) |
| v6_ragas_llama31_8b | continuous | 0.500 [0.500, 0.500] (n=8) | 0.036 [0.000, 0.107] (n=14) | 0.392 [0.324, 0.451] (n=51) |
| v1c_medscore | continuous | 0.312 [0.125, 0.500] (n=8) | 0.033 [0.000, 0.100] (n=15) | 0.275 [0.206, 0.343] (n=51) |
| v2b_bespoke | continuous | 0.250 [0.000, 0.625] (n=8) | 0.000 [0.000, 0.000] (n=15) | 0.039 [0.000, 0.098] (n=51) |
| v1_medscore | continuous | 0.188 [0.062, 0.375] (n=8) | 0.000 [0.000, 0.000] (n=15) | 0.186 [0.127, 0.255] (n=51) |
| v6_ragas_gpt4o_mini | continuous | 0.125 [0.000, 0.312] (n=8) | 0.100 [0.000, 0.200] (n=15) | 0.137 [0.078, 0.196] (n=51) |
| v4_ragas_nli | continuous | 0.071 [0.000, 0.214] (n=7) | 0.000 [0.000, 0.000] (n=15) | 0.173 [0.102, 0.255] (n=49) |
| v1b_medscore | continuous | 0.062 [0.000, 0.188] (n=8) | 0.000 [0.000, 0.000] (n=15) | 0.069 [0.020, 0.118] (n=51) |
| v5_ragas_nli | continuous | 0.062 [0.000, 0.188] (n=8) | 0.000 [0.000, 0.000] (n=15) | 0.020 [0.000, 0.049] (n=51) |
| v6_ragas_haiku45 | continuous | 0.062 [0.000, 0.188] (n=8) | 0.033 [0.000, 0.100] (n=15) | 0.049 [0.010, 0.088] (n=51) |
| v6_ragas_mistral_small32 | continuous | 0.000 [0.000, 0.000] (n=8) | 0.000 [0.000, 0.000] (n=15) | 0.039 [0.010, 0.078] (n=51) |

**Figure (pair 1):** `results/figures/t13_pairwise_x1000_vs_inv.png`

## Appendix — superseded best-of-N (footnote only)

The prior **18-base** `PI_ok=Y` best-of-N argmax design was underpowered (×1000 in only 3 bases) and its **tie → lower rank** rule biased **binary** LLM judges. See commit `97d0b79` / `notes/t13_best_of_n.json` for that exploratory table; **do not use for inference.** Primary T13 estimand is pairwise above.

- Legacy example: v1_medscore P(select wrong) ≈ 0.05555555555555555 on n=18 bases.
