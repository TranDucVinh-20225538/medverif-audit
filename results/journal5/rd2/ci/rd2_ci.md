# RD2 bootstrap CIs and paired McNemar tests — PROVISIONAL (auto labels)

Generated 2026-10-02T20:47:10+0700 by `scripts/journal5/rd2_ci.py`. Reference: PROVISIONAL auto labels (rd_extract: error = unit_error+basis_error, non-error = correct). Instances 5688; error set 459; non-error set 3654. 10000 cluster-bootstrap resamples (seed 20261002), percentile 95% CI, clustered by question id (qid); drug-clustered CIs are in rd2_ci_rates.csv. PARSE_FAIL excluded from the denominator (count shown). Basis check: PASS = not flagged.

## PASS rates

| family | system | PASS on errors [95% CI] | PASS on non-errors [95% CI] | parse fails (err / non-err) |
|---|---|---|---|---|
| paper_checker | MiniCheck-RoBERTa | 74/459 = 16.1% [11.9, 20.6] | 3040/3654 = 83.2% [81.5, 84.9] | 0 / 0 |
| paper_checker | MiniCheck-DeBERTa | 50/459 = 10.9% [7.5, 14.7] | 2388/3654 = 65.4% [63.5, 67.3] | 0 / 0 |
| paper_checker | AlignScore-base | 87/459 = 19.0% [14.9, 23.1] | 2938/3654 = 80.4% [78.8, 82.0] | 0 / 0 |
| paper_checker | MiniCheck-Flan-T5-Large | 83/459 = 18.1% [13.3, 23.2] | 2605/3654 = 71.3% [69.0, 73.6] | 0 / 0 |
| paper_checker | AlignScore-large | 83/459 = 18.1% [13.7, 22.6] | 3199/3654 = 87.5% [86.0, 89.0] | 0 / 0 |
| paper_checker | Llama-3.3-70B RAGAS-NLI | 30/459 = 6.5% [3.2, 10.5] | 2928/3653 = 80.2% [78.1, 82.2] | 0 / 1 |
| paper_checker | MedScore (Mistral-Small-24B) | 39/459 = 8.5% [5.0, 12.4] | 2910/3654 = 79.6% [77.6, 81.6] | 0 / 0 |
| llm_judge | baichuan_m2_32b | 33/424 = 7.8% [4.0, 12.1] | 2671/3393 = 78.7% [76.6, 80.8] | 35 / 261 |
| llm_judge | llama31_8b | 82/436 = 18.8% [13.7, 23.9] | 3203/3555 = 90.1% [88.5, 91.6] | 23 / 99 |
| llm_judge | medgemma_27b | 34/459 = 7.4% [3.7, 11.6] | 2823/3654 = 77.3% [75.1, 79.4] | 0 / 0 |
| llm_judge | medgemma_4b | 171/459 = 37.3% [31.8, 42.8] | 3355/3652 = 91.9% [90.5, 93.2] | 0 / 2 |
| llm_judge | qwen25_0p5b | 388/429 = 90.4% [87.7, 92.9] | 3353/3524 = 95.1% [94.4, 95.9] | 30 / 130 |
| llm_judge | qwen25_14b | 17/424 = 4.0% [1.1, 7.6] | 2295/3472 = 66.1% [63.6, 68.5] | 35 / 182 |
| llm_judge | qwen25_1p5b | 100/341 = 29.3% [22.7, 36.1] | 2162/2751 = 78.6% [76.1, 80.9] | 118 / 903 |
| llm_judge | qwen25_3b | 17/342 = 5.0% [1.2, 9.8] | 1126/2641 = 42.6% [39.6, 45.6] | 117 / 1013 |
| llm_judge | qwen25_7b | 47/398 = 11.8% [7.2, 16.8] | 2566/3270 = 78.5% [76.3, 80.6] | 61 / 384 |
| ft | FT minicheck_ft5_base | 83/459 = 18.1% [13.3, 23.2] | 2605/3654 = 71.3% [69.0, 73.6] | 0 / 0 |
| ft | FT minicheck_ft5_r0.5 | 131/459 = 28.5% [23.6, 33.7] | 2843/3654 = 77.8% [76.2, 79.4] | 0 / 0 |
| ft | FT minicheck_ft5_r1 | 98/459 = 21.4% [16.8, 26.1] | 2860/3654 = 78.3% [76.7, 79.9] | 0 / 0 |
| ft | FT minicheck_ft5_r2 | 98/459 = 21.4% [16.5, 26.4] | 2747/3654 = 75.2% [73.5, 76.8] | 0 / 0 |
| ft | FT alignscore_large_base | 83/459 = 18.1% [13.7, 22.6] | 3199/3654 = 87.5% [86.0, 89.0] | 0 / 0 |
| ft | FT alignscore_large_r0.5 | 140/459 = 30.5% [25.2, 36.0] | 2953/3654 = 80.8% [79.0, 82.6] | 0 / 0 |
| ft | FT alignscore_large_r1 | 103/459 = 22.4% [17.7, 27.4] | 2803/3654 = 76.7% [74.7, 78.7] | 0 / 0 |
| ft | FT alignscore_large_r2 | 115/459 = 25.1% [20.2, 30.0] | 2713/3654 = 74.2% [72.3, 76.2] | 0 / 0 |
| unf | t6_minicheck_roberta unf_v1 | 68/459 = 14.8% [10.6, 19.4] | 3050/3654 = 83.5% [81.8, 85.1] | 0 / 0 |
| unf | t6_minicheck_deberta unf_v1 | 46/459 = 10.0% [6.5, 14.0] | 2463/3654 = 67.4% [65.5, 69.3] | 0 / 0 |
| unf | t6_alignscore_base unf_v1 | 84/459 = 18.3% [13.9, 23.0] | 3001/3654 = 82.1% [80.6, 83.6] | 0 / 0 |
| unf | v2a_minicheck unf_v1 | 69/459 = 15.0% [10.6, 19.7] | 2596/3654 = 71.0% [68.8, 73.3] | 0 / 0 |
| unf | v3_alignscore unf_v1 | 76/459 = 16.6% [12.6, 20.9] | 3211/3654 = 87.9% [86.4, 89.3] | 0 / 0 |
| unf | FT minicheck_ft5_base unf_v1 | 69/459 = 15.0% [10.6, 19.7] | 2596/3654 = 71.0% [68.8, 73.3] | 0 / 0 |
| unf | FT minicheck_ft5_r0.5 unf_v1 | 110/459 = 24.0% [18.5, 30.0] | 2829/3654 = 77.4% [75.8, 79.0] | 0 / 0 |
| unf | FT minicheck_ft5_r1 unf_v1 | 93/459 = 20.3% [14.9, 26.2] | 2874/3654 = 78.7% [77.1, 80.2] | 0 / 0 |
| unf | FT minicheck_ft5_r2 unf_v1 | 91/459 = 19.8% [14.3, 25.9] | 2752/3654 = 75.3% [73.7, 76.9] | 0 / 0 |
| unf | FT alignscore_large_base unf_v1 | 76/459 = 16.6% [12.6, 20.9] | 3211/3654 = 87.9% [86.4, 89.3] | 0 / 0 |
| unf | FT alignscore_large_r0.5 unf_v1 | 136/459 = 29.6% [23.6, 36.1] | 2987/3654 = 81.7% [80.0, 83.5] | 0 / 0 |
| unf | FT alignscore_large_r1 unf_v1 | 106/459 = 23.1% [17.4, 29.5] | 2920/3654 = 79.9% [77.9, 82.0] | 0 / 0 |
| unf | FT alignscore_large_r2 unf_v1 | 109/459 = 23.7% [18.4, 29.5] | 2864/3654 = 78.4% [76.4, 80.3] | 0 / 0 |
| unf | t6_minicheck_roberta unf_v2 | 68/459 = 14.8% [10.6, 19.4] | 3048/3654 = 83.4% [81.7, 85.1] | 0 / 0 |
| unf | t6_minicheck_deberta unf_v2 | 46/459 = 10.0% [6.5, 14.0] | 2460/3654 = 67.3% [65.5, 69.2] | 0 / 0 |
| unf | t6_alignscore_base unf_v2 | 85/459 = 18.5% [14.0, 23.5] | 3005/3654 = 82.2% [80.7, 83.7] | 0 / 0 |
| unf | v2a_minicheck unf_v2 | 70/459 = 15.3% [10.8, 19.9] | 2596/3654 = 71.0% [68.8, 73.3] | 0 / 0 |
| unf | v3_alignscore unf_v2 | 77/459 = 16.8% [12.6, 21.3] | 3210/3654 = 87.8% [86.4, 89.3] | 0 / 0 |
| unf | FT minicheck_ft5_base unf_v2 | 70/459 = 15.3% [10.8, 19.9] | 2596/3654 = 71.0% [68.8, 73.3] | 0 / 0 |
| unf | FT minicheck_ft5_r0.5 unf_v2 | 110/459 = 24.0% [18.5, 30.0] | 2821/3654 = 77.2% [75.6, 78.8] | 0 / 0 |
| unf | FT minicheck_ft5_r1 unf_v2 | 93/459 = 20.3% [14.9, 26.2] | 2873/3654 = 78.6% [77.1, 80.2] | 0 / 0 |
| unf | FT minicheck_ft5_r2 unf_v2 | 91/459 = 19.8% [14.3, 25.9] | 2749/3654 = 75.2% [73.6, 76.9] | 0 / 0 |
| unf | FT alignscore_large_base unf_v2 | 77/459 = 16.8% [12.6, 21.3] | 3210/3654 = 87.8% [86.4, 89.3] | 0 / 0 |
| unf | FT alignscore_large_r0.5 unf_v2 | 136/459 = 29.6% [23.6, 36.1] | 2988/3654 = 81.8% [80.0, 83.5] | 0 / 0 |
| unf | FT alignscore_large_r1 unf_v2 | 107/459 = 23.3% [17.6, 29.7] | 2921/3654 = 79.9% [77.9, 82.0] | 0 / 0 |
| unf | FT alignscore_large_r2 unf_v2 | 107/459 = 23.3% [18.0, 29.0] | 2866/3654 = 78.4% [76.5, 80.3] | 0 / 0 |
| basis_check | basis_check_full | 224/459 = 48.8% [40.6, 57.0] | 3649/3654 = 99.9% [99.7, 100.0] | 0 / 0 |
| basis_check | basis_check_strict | 346/459 = 75.4% [69.1, 81.1] | 3649/3654 = 99.9% [99.7, 100.0] | 0 / 0 |

## Paired McNemar (other vs base; PASS = checker accepts the answer)

Discordant b = base PASS & other FAIL, c = base FAIL & other PASS. Exact binomial if b+c < 25, else chi-square with continuity correction. Holm over all 64 tests (p_holm_all) and within comparison x set (p_holm_family). Δ = other − base PASS rate, 95% qid-cluster bootstrap CI. McNemar ignores clustering.

| comparison | base | other | set | n | base PASS % | other PASS % | Δ pp [95% CI] | b / c | method | p | p_holm_all | p_holm_family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ft_vs_base | FT minicheck_ft5_base | FT minicheck_ft5_r0.5 | error | 459 | 18.1 | 28.5 | 10.5 [5.8, 15.5] | 21 / 69 | chi2_cc | 7.26e-07 | 3.56e-05 | 3.63e-06 |
| ft_vs_base | FT minicheck_ft5_base | FT minicheck_ft5_r0.5 | nonerror | 3654 | 71.3 | 77.8 | 6.5 [4.8, 8.2] | 127 / 365 | chi2_cc | 1.2e-26 | 7.2e-25 | 2.4e-26 |
| ft_vs_base | FT minicheck_ft5_base | FT minicheck_ft5_r1 | error | 459 | 18.1 | 21.4 | 3.3 [-1.1, 7.9] | 27 / 42 | chi2_cc | 0.0919 | 1 | 0.184 |
| ft_vs_base | FT minicheck_ft5_base | FT minicheck_ft5_r1 | nonerror | 3654 | 71.3 | 78.3 | 7.0 [5.3, 8.7] | 120 / 375 | chi2_cc | 3.46e-30 | 2.15e-28 | 1.38e-29 |
| ft_vs_base | FT minicheck_ft5_base | FT minicheck_ft5_r2 | error | 459 | 18.1 | 21.4 | 3.3 [-1.2, 7.9] | 28 / 43 | chi2_cc | 0.0966 | 1 | 0.184 |
| ft_vs_base | FT minicheck_ft5_base | FT minicheck_ft5_r2 | nonerror | 3654 | 71.3 | 75.2 | 3.9 [2.1, 5.6] | 188 / 330 | chi2_cc | 5.82e-10 | 3.09e-08 | 5.82e-10 |
| ft_vs_base | FT alignscore_large_base | FT alignscore_large_r0.5 | error | 459 | 18.1 | 30.5 | 12.4 [6.9, 18.1] | 31 / 88 | chi2_cc | 2.84e-07 | 1.42e-05 | 1.71e-06 |
| ft_vs_base | FT alignscore_large_base | FT alignscore_large_r0.5 | nonerror | 3654 | 87.5 | 80.8 | -6.7 [-8.4, -5.1] | 378 / 132 | chi2_cc | 2.02e-27 | 1.23e-25 | 6.06e-27 |
| ft_vs_base | FT alignscore_large_base | FT alignscore_large_r1 | error | 459 | 18.1 | 22.4 | 4.4 [-0.8, 9.5] | 40 / 60 | chi2_cc | 0.0574 | 1 | 0.172 |
| ft_vs_base | FT alignscore_large_base | FT alignscore_large_r1 | nonerror | 3654 | 87.5 | 76.7 | -10.8 [-12.7, -9.0] | 517 / 121 | chi2_cc | 4e-55 | 2.52e-53 | 2e-54 |
| ft_vs_base | FT alignscore_large_base | FT alignscore_large_r2 | error | 459 | 18.1 | 25.1 | 7.0 [0.6, 13.4] | 54 / 86 | chi2_cc | 0.00879 | 0.387 | 0.0352 |
| ft_vs_base | FT alignscore_large_base | FT alignscore_large_r2 | nonerror | 3654 | 87.5 | 74.2 | -13.3 [-15.1, -11.6] | 556 / 70 | chi2_cc | 1.04e-83 | 6.68e-82 | 6.26e-83 |
| unf_vs_raw | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v1 | error | 459 | 16.1 | 14.8 | -1.3 [-5.2, 2.4] | 16 / 10 | chi2_cc | 0.327 | 1 | 1 |
| unf_vs_raw | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v1 | nonerror | 3654 | 83.2 | 83.5 | 0.3 [-0.3, 0.9] | 23 / 33 | chi2_cc | 0.229 | 1 | 1 |
| unf_vs_raw | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v1 | error | 459 | 10.9 | 10.0 | -0.9 [-2.8, 0.9] | 8 / 4 | exact | 0.388 | 1 | 1 |
| unf_vs_raw | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v1 | nonerror | 3654 | 65.4 | 67.4 | 2.1 [1.4, 2.8] | 16 / 91 | chi2_cc | 8.44e-13 | 4.64e-11 | 1.86e-11 |
| unf_vs_raw | AlignScore-base | t6_alignscore_base unf_v1 | error | 459 | 19.0 | 18.3 | -0.7 [-3.4, 2.1] | 14 / 11 | chi2_cc | 0.689 | 1 | 1 |
| unf_vs_raw | AlignScore-base | t6_alignscore_base unf_v1 | nonerror | 3654 | 80.4 | 82.1 | 1.7 [0.9, 2.6] | 32 / 95 | chi2_cc | 3.76e-08 | 1.92e-06 | 7.15e-07 |
| unf_vs_raw | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v1 | error | 459 | 18.1 | 15.0 | -3.1 [-6.6, -0.2] | 20 / 6 | chi2_cc | 0.0108 | 0.453 | 0.259 |
| unf_vs_raw | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v1 | nonerror | 3654 | 71.3 | 71.0 | -0.2 [-0.7, 0.2] | 31 / 22 | chi2_cc | 0.272 | 1 | 1 |
| unf_vs_raw | AlignScore-large | v3_alignscore unf_v1 | error | 459 | 18.1 | 16.6 | -1.5 [-4.6, 1.1] | 17 / 10 | chi2_cc | 0.248 | 1 | 1 |
| unf_vs_raw | AlignScore-large | v3_alignscore unf_v1 | nonerror | 3654 | 87.5 | 87.9 | 0.3 [-0.1, 0.9] | 15 / 27 | chi2_cc | 0.0896 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v1 | error | 459 | 18.1 | 15.0 | -3.1 [-6.6, -0.2] | 20 / 6 | chi2_cc | 0.0108 | 0.453 | 0.259 |
| unf_vs_raw | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v1 | nonerror | 3654 | 71.3 | 71.0 | -0.2 [-0.7, 0.2] | 31 / 22 | chi2_cc | 0.272 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v1 | error | 459 | 28.5 | 24.0 | -4.6 [-8.4, -1.0] | 34 / 13 | chi2_cc | 0.00353 | 0.162 | 0.0918 |
| unf_vs_raw | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v1 | nonerror | 3654 | 77.8 | 77.4 | -0.4 [-0.8, 0.1] | 36 / 22 | chi2_cc | 0.0878 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v1 | error | 459 | 21.4 | 20.3 | -1.1 [-5.0, 2.8] | 25 / 20 | chi2_cc | 0.551 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v1 | nonerror | 3654 | 78.3 | 78.7 | 0.4 [-0.1, 0.9] | 29 / 43 | chi2_cc | 0.126 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v1 | error | 459 | 21.4 | 19.8 | -1.5 [-5.2, 2.1] | 25 / 18 | chi2_cc | 0.36 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v1 | nonerror | 3654 | 75.2 | 75.3 | 0.1 [-0.3, 0.6] | 32 / 37 | chi2_cc | 0.63 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_base | FT alignscore_large_base unf_v1 | error | 459 | 18.1 | 16.6 | -1.5 [-4.6, 1.1] | 17 / 10 | chi2_cc | 0.248 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_base | FT alignscore_large_base unf_v1 | nonerror | 3654 | 87.5 | 87.9 | 0.3 [-0.1, 0.9] | 15 / 27 | chi2_cc | 0.0896 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v1 | error | 459 | 30.5 | 29.6 | -0.9 [-5.6, 4.0] | 33 / 29 | chi2_cc | 0.703 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v1 | nonerror | 3654 | 80.8 | 81.7 | 0.9 [0.2, 1.7] | 44 / 78 | chi2_cc | 0.00281 | 0.132 | 0.0478 |
| unf_vs_raw | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v1 | error | 459 | 22.4 | 23.1 | 0.7 [-4.1, 5.9] | 26 / 29 | chi2_cc | 0.787 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v1 | nonerror | 3654 | 76.7 | 79.9 | 3.2 [2.1, 4.3] | 49 / 166 | chi2_cc | 2.55e-15 | 1.45e-13 | 6.12e-14 |
| unf_vs_raw | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v1 | error | 459 | 25.1 | 23.7 | -1.3 [-6.0, 4.3] | 32 / 26 | chi2_cc | 0.511 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v1 | nonerror | 3654 | 74.2 | 78.4 | 4.1 [3.0, 5.3] | 40 / 191 | chi2_cc | 5.66e-23 | 3.28e-21 | 1.41e-21 |
| unf_vs_raw | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v2 | error | 459 | 16.1 | 14.8 | -1.3 [-5.2, 2.4] | 16 / 10 | chi2_cc | 0.327 | 1 | 1 |
| unf_vs_raw | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v2 | nonerror | 3654 | 83.2 | 83.4 | 0.2 [-0.4, 0.9] | 26 / 34 | chi2_cc | 0.366 | 1 | 1 |
| unf_vs_raw | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v2 | error | 459 | 10.9 | 10.0 | -0.9 [-2.8, 0.9] | 8 / 4 | exact | 0.388 | 1 | 1 |
| unf_vs_raw | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v2 | nonerror | 3654 | 65.4 | 67.3 | 2.0 [1.3, 2.7] | 20 / 92 | chi2_cc | 1.96e-11 | 1.06e-09 | 4.12e-10 |
| unf_vs_raw | AlignScore-base | t6_alignscore_base unf_v2 | error | 459 | 19.0 | 18.5 | -0.4 [-3.3, 2.6] | 14 / 12 | chi2_cc | 0.845 | 1 | 1 |
| unf_vs_raw | AlignScore-base | t6_alignscore_base unf_v2 | nonerror | 3654 | 80.4 | 82.2 | 1.8 [1.0, 2.7] | 30 / 97 | chi2_cc | 4.73e-09 | 2.46e-07 | 9.45e-08 |
| unf_vs_raw | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v2 | error | 459 | 18.1 | 15.3 | -2.8 [-6.4, 0.0] | 20 / 7 | chi2_cc | 0.0209 | 0.837 | 0.46 |
| unf_vs_raw | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v2 | nonerror | 3654 | 71.3 | 71.0 | -0.2 [-0.7, 0.3] | 33 / 24 | chi2_cc | 0.289 | 1 | 1 |
| unf_vs_raw | AlignScore-large | v3_alignscore unf_v2 | error | 459 | 18.1 | 16.8 | -1.3 [-4.5, 1.5] | 17 / 11 | chi2_cc | 0.345 | 1 | 1 |
| unf_vs_raw | AlignScore-large | v3_alignscore unf_v2 | nonerror | 3654 | 87.5 | 87.8 | 0.3 [-0.2, 0.8] | 16 / 27 | chi2_cc | 0.127 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v2 | error | 459 | 18.1 | 15.3 | -2.8 [-6.4, 0.0] | 20 / 7 | chi2_cc | 0.0209 | 0.837 | 0.46 |
| unf_vs_raw | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v2 | nonerror | 3654 | 71.3 | 71.0 | -0.2 [-0.7, 0.3] | 33 / 24 | chi2_cc | 0.289 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v2 | error | 459 | 28.5 | 24.0 | -4.6 [-8.4, -1.0] | 34 / 13 | chi2_cc | 0.00353 | 0.162 | 0.0918 |
| unf_vs_raw | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v2 | nonerror | 3654 | 77.8 | 77.2 | -0.6 [-1.1, -0.1] | 44 / 22 | chi2_cc | 0.00974 | 0.419 | 0.156 |
| unf_vs_raw | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v2 | error | 459 | 21.4 | 20.3 | -1.1 [-5.0, 2.8] | 25 / 20 | chi2_cc | 0.551 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v2 | nonerror | 3654 | 78.3 | 78.6 | 0.4 [-0.2, 0.9] | 32 / 45 | chi2_cc | 0.171 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v2 | error | 459 | 21.4 | 19.8 | -1.5 [-5.2, 2.1] | 25 / 18 | chi2_cc | 0.36 | 1 | 1 |
| unf_vs_raw | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v2 | nonerror | 3654 | 75.2 | 75.2 | 0.1 [-0.4, 0.5] | 36 / 38 | chi2_cc | 0.907 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_base | FT alignscore_large_base unf_v2 | error | 459 | 18.1 | 16.8 | -1.3 [-4.5, 1.5] | 17 / 11 | chi2_cc | 0.345 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_base | FT alignscore_large_base unf_v2 | nonerror | 3654 | 87.5 | 87.8 | 0.3 [-0.2, 0.8] | 16 / 27 | chi2_cc | 0.127 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v2 | error | 459 | 30.5 | 29.6 | -0.9 [-5.8, 4.0] | 34 / 30 | chi2_cc | 0.708 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v2 | nonerror | 3654 | 80.8 | 81.8 | 1.0 [0.2, 1.8] | 46 / 81 | chi2_cc | 0.00255 | 0.123 | 0.046 |
| unf_vs_raw | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v2 | error | 459 | 22.4 | 23.3 | 0.9 [-4.0, 6.1] | 27 / 31 | chi2_cc | 0.694 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v2 | nonerror | 3654 | 76.7 | 79.9 | 3.2 [2.1, 4.4] | 53 / 171 | chi2_cc | 5.39e-15 | 3.02e-13 | 1.24e-13 |
| unf_vs_raw | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v2 | error | 459 | 25.1 | 23.3 | -1.7 [-6.5, 3.8] | 34 / 26 | chi2_cc | 0.366 | 1 | 1 |
| unf_vs_raw | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v2 | nonerror | 3654 | 74.2 | 78.4 | 4.2 [3.1, 5.4] | 40 / 193 | chi2_cc | 2.33e-23 | 1.37e-21 | 6.06e-22 |
