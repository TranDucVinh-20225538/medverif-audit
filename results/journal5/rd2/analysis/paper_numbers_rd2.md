# RD2 paper numbers (PROVISIONAL automatic labels; v1 = pre-registered, v2 = amendment 1)

Generated 2026-10-05T21:50:49+0700 by `scripts/journal5/rd2_analysis_extra.py`. Amendment: `prereg/rd2_amendment_1.md`, commit `38191827dc9d8116b9072f54d877b8cf32490ad1` (2026-10-05T21:42:19+07:00). Machine-readable: `results/journal5/rd2/analysis/paper_numbers_rd2.json`. No pharmacist label has been used.

## Totals (source: amend1/labels_v2.jsonl, amend1/relabel_diff.md)

| class | v1 closed | v1 grounded | v1 total | v2 closed | v2 grounded | v2 total |
|---|---|---|---|---|---|---|
| correct | 996 | 2658 | 3654 | 1002 | 2677 | 3679 |
| unit_error | 123 | 12 | 135 | 118 | 1 | 119 |
| basis_error | 324 | 0 | 324 | 307 | 0 | 307 |
| value_error | 665 | 3 | 668 | 674 | 2 | 676 |
| match_other_context | 459 | 164 | 623 | 464 | 155 | 619 |
| time_ambiguous | 172 | 35 | 207 | 175 | 37 | 212 |
| unverifiable | 72 | 5 | 77 | 75 | 5 | 80 |
| no_dose | 69 | 3 | 72 | 65 | 3 | 68 |
| **total** | 2880 | 2880 | 5760 | 2880 | 2880 | 5760 |

Unit + basis errors: v1 459, v2 426. Answers scored by checkers: 5688 of 5760 (the no-dose answers were not scored).

## Per-system PASS rates, all answers (source: analysis/rd2_rates_all.csv; Wilson / drug-cluster 5,000 / question-cluster 10,000)

| system | labels | PASS on errors | Wilson | drug | question | PASS on correct | Wilson | drug | question | PF err/corr |
|---|---|---|---|---|---|---|---|---|---|---|
| MiniCheck-RoBERTa | v1 | 74/459 = 16.1 | [13.0, 19.8] | [11.6, 21.0] | [11.9, 20.6] | 3040/3654 = 83.2 | [81.9, 84.4] | [81.5, 84.9] | [81.5, 84.9] | 0/0 |
| MiniCheck-RoBERTa | v2 | 60/426 = 14.1 | [11.1, 17.7] | [9.8, 19.0] | [10.4, 18.2] | 3059/3679 = 83.1 | [81.9, 84.3] | [81.4, 84.8] | [81.5, 84.8] | 0/0 |
| MiniCheck-DeBERTa | v1 | 50/459 = 10.9 | [8.4, 14.1] | [7.3, 14.7] | [7.5, 14.7] | 2388/3654 = 65.4 | [63.8, 66.9] | [63.4, 67.3] | [63.5, 67.3] | 0/0 |
| MiniCheck-DeBERTa | v2 | 44/426 = 10.3 | [7.8, 13.6] | [6.7, 14.5] | [6.8, 14.2] | 2394/3679 = 65.1 | [63.5, 66.6] | [63.1, 67.0] | [63.1, 67.0] | 0/0 |
| AlignScore-base | v1 | 87/459 = 19.0 | [15.6, 22.8] | [14.5, 23.6] | [14.9, 23.1] | 2938/3654 = 80.4 | [79.1, 81.7] | [78.7, 82.1] | [78.8, 82.0] | 0/0 |
| AlignScore-base | v2 | 78/426 = 18.3 | [14.9, 22.3] | [13.7, 23.2] | [14.3, 22.7] | 2947/3679 = 80.1 | [78.8, 81.4] | [78.3, 81.9] | [78.5, 81.8] | 0/0 |
| MiniCheck-Flan-T5-Large | v1 | 83/459 = 18.1 | [14.8, 21.9] | [12.7, 23.6] | [13.3, 23.2] | 2605/3654 = 71.3 | [69.8, 72.7] | [68.9, 73.7] | [69.0, 73.6] | 0/0 |
| MiniCheck-Flan-T5-Large | v2 | 66/426 = 15.5 | [12.4, 19.2] | [10.8, 20.8] | [11.3, 20.0] | 2627/3679 = 71.4 | [69.9, 72.8] | [69.0, 73.8] | [69.1, 73.7] | 0/0 |
| AlignScore-large | v1 | 83/459 = 18.1 | [14.8, 21.9] | [13.2, 23.0] | [13.7, 22.6] | 3199/3654 = 87.5 | [86.4, 88.6] | [86.0, 89.0] | [86.0, 89.0] | 0/0 |
| AlignScore-large | v2 | 70/426 = 16.4 | [13.2, 20.2] | [12.0, 21.2] | [12.3, 20.8] | 3216/3679 = 87.4 | [86.3, 88.4] | [85.9, 89.0] | [85.9, 88.9] | 0/0 |
| Llama-3.3-70B RAGAS-NLI | v1 | 30/459 = 6.5 | [4.6, 9.2] | [3.1, 10.5] | [3.2, 10.5] | 2928/3653 = 80.2 | [78.8, 81.4] | [78.3, 82.0] | [78.1, 82.2] | 0/1 |
| Llama-3.3-70B RAGAS-NLI | v2 | 18/426 = 4.2 | [2.7, 6.6] | [1.9, 6.9] | [2.1, 6.7] | 2941/3678 = 80.0 | [78.6, 81.2] | [78.0, 81.9] | [77.9, 82.0] | 0/1 |
| MedScore (Mistral-Small-24B) | v1 | 39/459 = 8.5 | [6.3, 11.4] | [5.0, 12.5] | [5.0, 12.4] | 2910/3654 = 79.6 | [78.3, 80.9] | [77.6, 81.6] | [77.6, 81.6] | 0/0 |
| MedScore (Mistral-Small-24B) | v2 | 28/426 = 6.6 | [4.6, 9.3] | [4.1, 9.4] | [4.2, 9.2] | 2921/3679 = 79.4 | [78.1, 80.7] | [77.3, 81.5] | [77.4, 81.4] | 0/0 |
| baichuan_m2_32b | v1 | 33/424 = 7.8 | [5.6, 10.7] | [3.9, 12.0] | [4.0, 12.1] | 2671/3393 = 78.7 | [77.3, 80.1] | [76.6, 80.8] | [76.6, 80.8] | 35/261 |
| baichuan_m2_32b | v2 | 21/391 = 5.4 | [3.5, 8.1] | [2.5, 8.8] | [2.6, 8.6] | 2685/3416 = 78.6 | [77.2, 79.9] | [76.5, 80.7] | [76.5, 80.7] | 35/263 |
| llama31_8b | v1 | 82/436 = 18.8 | [15.4, 22.7] | [13.4, 24.4] | [13.7, 23.9] | 3203/3555 = 90.1 | [89.1, 91.0] | [88.5, 91.6] | [88.5, 91.6] | 23/99 |
| llama31_8b | v2 | 64/403 = 15.9 | [12.6, 19.8] | [11.1, 21.2] | [11.7, 20.3] | 3224/3578 = 90.1 | [89.1, 91.0] | [88.5, 91.6] | [88.6, 91.5] | 23/101 |
| medgemma_27b | v1 | 34/459 = 7.4 | [5.3, 10.2] | [3.6, 11.5] | [3.7, 11.6] | 2823/3654 = 77.3 | [75.9, 78.6] | [75.1, 79.4] | [75.1, 79.4] | 0/0 |
| medgemma_27b | v2 | 23/426 = 5.4 | [3.6, 8.0] | [2.6, 8.7] | [2.7, 8.6] | 2838/3679 = 77.1 | [75.8, 78.5] | [74.9, 79.3] | [75.0, 79.3] | 0/0 |
| medgemma_4b | v1 | 171/459 = 37.3 | [33.0, 41.8] | [30.8, 43.2] | [31.8, 42.8] | 3355/3652 = 91.9 | [90.9, 92.7] | [90.4, 93.3] | [90.5, 93.2] | 0/2 |
| medgemma_4b | v2 | 152/426 = 35.7 | [31.3, 40.3] | [29.4, 42.5] | [30.1, 41.4] | 3378/3677 = 91.9 | [90.9, 92.7] | [90.4, 93.2] | [90.5, 93.2] | 0/2 |
| qwen25_0p5b | v1 | 388/429 = 90.4 | [87.3, 92.9] | [87.9, 92.9] | [87.7, 92.9] | 3353/3524 = 95.1 | [94.4, 95.8] | [94.3, 95.9] | [94.4, 95.9] | 30/130 |
| qwen25_0p5b | v2 | 360/397 = 90.7 | [87.4, 93.2] | [88.0, 93.4] | [87.8, 93.3] | 3373/3548 = 95.1 | [94.3, 95.7] | [94.3, 95.9] | [94.3, 95.8] | 29/131 |
| qwen25_14b | v1 | 17/424 = 4.0 | [2.5, 6.3] | [1.1, 7.8] | [1.1, 7.6] | 2295/3472 = 66.1 | [64.5, 67.7] | [63.7, 68.5] | [63.6, 68.5] | 35/182 |
| qwen25_14b | v2 | 8/391 = 2.0 | [1.0, 4.0] | [0.3, 4.4] | [0.3, 4.3] | 2306/3497 = 65.9 | [64.4, 67.5] | [63.5, 68.3] | [63.5, 68.4] | 35/182 |
| qwen25_1p5b | v1 | 100/341 = 29.3 | [24.7, 34.4] | [22.4, 36.7] | [22.7, 36.1] | 2162/2751 = 78.6 | [77.0, 80.1] | [76.1, 81.1] | [76.1, 80.9] | 118/903 |
| qwen25_1p5b | v2 | 82/316 = 25.9 | [21.4, 31.1] | [19.4, 33.2] | [20.0, 32.3] | 2181/2771 = 78.7 | [77.1, 80.2] | [76.2, 81.1] | [76.2, 81.1] | 110/908 |
| qwen25_3b | v1 | 17/342 = 5.0 | [3.1, 7.8] | [1.2, 9.9] | [1.2, 9.8] | 1126/2641 = 42.6 | [40.8, 44.5] | [39.5, 45.7] | [39.6, 45.6] | 117/1013 |
| qwen25_3b | v2 | 8/317 = 2.5 | [1.3, 4.9] | [0.4, 5.3] | [0.3, 5.3] | 1136/2657 = 42.8 | [40.9, 44.6] | [39.6, 45.8] | [39.7, 45.8] | 109/1022 |
| qwen25_7b | v1 | 47/398 = 11.8 | [9.0, 15.4] | [7.1, 16.8] | [7.2, 16.8] | 2566/3270 = 78.5 | [77.0, 79.8] | [76.2, 80.8] | [76.3, 80.6] | 61/384 |
| qwen25_7b | v2 | 36/369 = 9.8 | [7.1, 13.2] | [5.8, 14.1] | [6.0, 14.0] | 2576/3289 = 78.3 | [76.9, 79.7] | [76.0, 80.6] | [76.1, 80.5] | 57/390 |
| FT minicheck_ft5_base | v1 | 83/459 = 18.1 | [14.8, 21.9] | [12.7, 23.6] | [13.3, 23.2] | 2605/3654 = 71.3 | [69.8, 72.7] | [68.9, 73.7] | [69.0, 73.6] | 0/0 |
| FT minicheck_ft5_base | v2 | 66/426 = 15.5 | [12.4, 19.2] | [10.8, 20.8] | [11.3, 20.0] | 2627/3679 = 71.4 | [69.9, 72.8] | [69.0, 73.8] | [69.1, 73.7] | 0/0 |
| FT minicheck_ft5_r0.5 | v1 | 131/459 = 28.5 | [24.6, 32.8] | [22.8, 34.5] | [23.6, 33.7] | 2843/3654 = 77.8 | [76.4, 79.1] | [76.2, 79.4] | [76.2, 79.4] | 0/0 |
| FT minicheck_ft5_r0.5 | v2 | 115/426 = 27.0 | [23.0, 31.4] | [21.2, 33.0] | [21.9, 32.2] | 2865/3679 = 77.9 | [76.5, 79.2] | [76.2, 79.5] | [76.3, 79.4] | 0/0 |
| FT minicheck_ft5_r1 | v1 | 98/459 = 21.4 | [17.8, 25.3] | [16.1, 26.8] | [16.8, 26.1] | 2860/3654 = 78.3 | [76.9, 79.6] | [76.5, 80.0] | [76.7, 79.9] | 0/0 |
| FT minicheck_ft5_r1 | v2 | 82/426 = 19.2 | [15.8, 23.3] | [14.1, 24.6] | [14.9, 23.8] | 2883/3679 = 78.4 | [77.0, 79.7] | [76.5, 80.1] | [76.7, 79.9] | 0/0 |
| FT minicheck_ft5_r2 | v1 | 98/459 = 21.4 | [17.8, 25.3] | [15.8, 27.3] | [16.5, 26.4] | 2747/3654 = 75.2 | [73.8, 76.6] | [73.4, 76.9] | [73.5, 76.8] | 0/0 |
| FT minicheck_ft5_r2 | v2 | 81/426 = 19.0 | [15.6, 23.0] | [13.5, 24.7] | [14.5, 23.8] | 2768/3679 = 75.2 | [73.8, 76.6] | [73.4, 77.0] | [73.6, 76.9] | 0/0 |
| FT alignscore_large_base | v1 | 83/459 = 18.1 | [14.8, 21.9] | [13.2, 23.0] | [13.7, 22.6] | 3199/3654 = 87.5 | [86.4, 88.6] | [86.0, 89.0] | [86.0, 89.0] | 0/0 |
| FT alignscore_large_base | v2 | 70/426 = 16.4 | [13.2, 20.2] | [12.0, 21.2] | [12.3, 20.8] | 3216/3679 = 87.4 | [86.3, 88.4] | [85.9, 89.0] | [85.9, 88.9] | 0/0 |
| FT alignscore_large_r0.5 | v1 | 140/459 = 30.5 | [26.5, 34.9] | [24.1, 37.2] | [25.2, 36.0] | 2953/3654 = 80.8 | [79.5, 82.1] | [79.1, 82.6] | [79.0, 82.6] | 0/0 |
| FT alignscore_large_r0.5 | v2 | 130/426 = 30.5 | [26.3, 35.0] | [23.8, 37.1] | [25.1, 36.2] | 2969/3679 = 80.7 | [79.4, 81.9] | [78.9, 82.5] | [78.9, 82.4] | 0/0 |
| FT alignscore_large_r1 | v1 | 103/459 = 22.4 | [18.9, 26.5] | [17.3, 28.2] | [17.7, 27.4] | 2803/3654 = 76.7 | [75.3, 78.1] | [74.6, 78.9] | [74.7, 78.7] | 0/0 |
| FT alignscore_large_r1 | v2 | 97/426 = 22.8 | [19.0, 27.0] | [17.2, 28.7] | [17.8, 28.1] | 2811/3679 = 76.4 | [75.0, 77.8] | [74.2, 78.6] | [74.4, 78.4] | 0/0 |
| FT alignscore_large_r2 | v1 | 115/459 = 25.1 | [21.3, 29.2] | [20.0, 30.7] | [20.2, 30.0] | 2713/3654 = 74.2 | [72.8, 75.6] | [72.3, 76.3] | [72.3, 76.2] | 0/0 |
| FT alignscore_large_r2 | v2 | 110/426 = 25.8 | [21.9, 30.2] | [20.5, 31.4] | [21.0, 31.0] | 2721/3679 = 74.0 | [72.5, 75.4] | [71.9, 76.0] | [72.0, 76.0] | 0/0 |
| basis_check_full | v1 | 224/459 = 48.8 | [44.3, 53.4] | [39.9, 57.6] | [40.6, 57.0] | 3649/3654 = 99.9 | [99.7, 99.9] | [99.7, 100.0] | [99.7, 100.0] | 0/0 |
| basis_check_full | v2 | 191/426 = 44.8 | [40.2, 49.6] | [36.2, 53.5] | [36.7, 52.7] | 3674/3679 = 99.9 | [99.7, 99.9] | [99.7, 100.0] | [99.7, 100.0] | 0/0 |
| basis_check_strict | v1 | 346/459 = 75.4 | [71.2, 79.1] | [68.3, 82.0] | [69.1, 81.1] | 3649/3654 = 99.9 | [99.7, 99.9] | [99.7, 100.0] | [99.7, 100.0] | 0/0 |
| basis_check_strict | v2 | 313/426 = 73.5 | [69.1, 77.4] | [65.9, 80.5] | [67.2, 79.2] | 3674/3679 = 99.9 | [99.7, 99.9] | [99.7, 100.0] | [99.7, 100.0] | 0/0 |

## Closed-book / grounded (source: analysis/c1_condition_rates.csv, analysis/c1_ft_mcnemar_closed.csv)

Yes, roughly: within closed-book answers the seven paper checkers pass 4.9-18.1% of automatic unit/basis errors under the pre-registered labels (n = 447; all answers 6.5-19.0%) and 4.2-18.4% under the v2 labels (n = 425) — only Llama-3.3-70B RAGAS-NLI and MedScore (Mistral-Small-24B) fall below 7% — because 447 of 459 (v1) / 425 of 426 (v2) automatic errors are closed-book anyway; what changes in closed-book is PASS on correct answers, which drops to 41.8-74.8% (all answers 65.4-87.5%).

See `analysis/rd2_analysis_extra.md` section C1 for every system.

## Paired comparisons (source: analysis/rd2_paired_all.csv; 64 per label set, Holm within label set)

| labels | base | other | set | n | b/c | Δ pp [CI] | p | p Holm |
|---|---|---|---|---|---|---|---|---|
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_r0.5 | error | 459 | 21/69 | 10.5 [5.8, 15.5] | 7.26e-07 | 3.56e-05 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_r0.5 | nonerror | 3654 | 127/365 | 6.5 [4.8, 8.2] | 1.2e-26 | 7.2e-25 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_r1 | error | 459 | 27/42 | 3.3 [-1.1, 7.9] | 0.0919 | 1 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_r1 | nonerror | 3654 | 120/375 | 7.0 [5.3, 8.7] | 3.46e-30 | 2.15e-28 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_r2 | error | 459 | 28/43 | 3.3 [-1.2, 7.9] | 0.0966 | 1 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_r2 | nonerror | 3654 | 188/330 | 3.9 [2.1, 5.6] | 5.82e-10 | 3.09e-08 |
| v1 | FT alignscore_large_base | FT alignscore_large_r0.5 | error | 459 | 31/88 | 12.4 [6.9, 18.1] | 2.84e-07 | 1.42e-05 |
| v1 | FT alignscore_large_base | FT alignscore_large_r0.5 | nonerror | 3654 | 378/132 | -6.7 [-8.4, -5.1] | 2.02e-27 | 1.23e-25 |
| v1 | FT alignscore_large_base | FT alignscore_large_r1 | error | 459 | 40/60 | 4.4 [-0.8, 9.5] | 0.0574 | 1 |
| v1 | FT alignscore_large_base | FT alignscore_large_r1 | nonerror | 3654 | 517/121 | -10.8 [-12.7, -9.0] | 4e-55 | 2.52e-53 |
| v1 | FT alignscore_large_base | FT alignscore_large_r2 | error | 459 | 54/86 | 7.0 [0.6, 13.4] | 0.00879 | 0.387 |
| v1 | FT alignscore_large_base | FT alignscore_large_r2 | nonerror | 3654 | 556/70 | -13.3 [-15.1, -11.6] | 1.04e-83 | 6.68e-82 |
| v1 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v1 | error | 459 | 16/10 | -1.3 [-5.2, 2.4] | 0.327 | 1 |
| v1 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v1 | nonerror | 3654 | 23/33 | 0.3 [-0.3, 0.9] | 0.229 | 1 |
| v1 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v1 | error | 459 | 8/4 | -0.9 [-2.8, 0.9] | 0.388 | 1 |
| v1 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v1 | nonerror | 3654 | 16/91 | 2.1 [1.4, 2.8] | 8.44e-13 | 4.64e-11 |
| v1 | AlignScore-base | t6_alignscore_base unf_v1 | error | 459 | 14/11 | -0.7 [-3.4, 2.1] | 0.689 | 1 |
| v1 | AlignScore-base | t6_alignscore_base unf_v1 | nonerror | 3654 | 32/95 | 1.7 [0.9, 2.6] | 3.76e-08 | 1.92e-06 |
| v1 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v1 | error | 459 | 20/6 | -3.1 [-6.6, -0.2] | 0.0108 | 0.453 |
| v1 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v1 | nonerror | 3654 | 31/22 | -0.2 [-0.7, 0.2] | 0.272 | 1 |
| v1 | AlignScore-large | v3_alignscore unf_v1 | error | 459 | 17/10 | -1.5 [-4.6, 1.1] | 0.248 | 1 |
| v1 | AlignScore-large | v3_alignscore unf_v1 | nonerror | 3654 | 15/27 | 0.3 [-0.1, 0.9] | 0.0896 | 1 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v1 | error | 459 | 20/6 | -3.1 [-6.6, -0.2] | 0.0108 | 0.453 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v1 | nonerror | 3654 | 31/22 | -0.2 [-0.7, 0.2] | 0.272 | 1 |
| v1 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v1 | error | 459 | 34/13 | -4.6 [-8.4, -1.0] | 0.00353 | 0.162 |
| v1 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v1 | nonerror | 3654 | 36/22 | -0.4 [-0.8, 0.1] | 0.0878 | 1 |
| v1 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v1 | error | 459 | 25/20 | -1.1 [-5.0, 2.8] | 0.551 | 1 |
| v1 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v1 | nonerror | 3654 | 29/43 | 0.4 [-0.1, 0.9] | 0.126 | 1 |
| v1 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v1 | error | 459 | 25/18 | -1.5 [-5.2, 2.1] | 0.36 | 1 |
| v1 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v1 | nonerror | 3654 | 32/37 | 0.1 [-0.3, 0.6] | 0.63 | 1 |
| v1 | FT alignscore_large_base | FT alignscore_large_base unf_v1 | error | 459 | 17/10 | -1.5 [-4.6, 1.1] | 0.248 | 1 |
| v1 | FT alignscore_large_base | FT alignscore_large_base unf_v1 | nonerror | 3654 | 15/27 | 0.3 [-0.1, 0.9] | 0.0896 | 1 |
| v1 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v1 | error | 459 | 33/29 | -0.9 [-5.6, 4.0] | 0.703 | 1 |
| v1 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v1 | nonerror | 3654 | 44/78 | 0.9 [0.2, 1.7] | 0.00281 | 0.132 |
| v1 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v1 | error | 459 | 26/29 | 0.7 [-4.1, 5.9] | 0.787 | 1 |
| v1 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v1 | nonerror | 3654 | 49/166 | 3.2 [2.1, 4.3] | 2.55e-15 | 1.45e-13 |
| v1 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v1 | error | 459 | 32/26 | -1.3 [-6.0, 4.3] | 0.511 | 1 |
| v1 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v1 | nonerror | 3654 | 40/191 | 4.1 [3.0, 5.3] | 5.66e-23 | 3.28e-21 |
| v1 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v2 | error | 459 | 16/10 | -1.3 [-5.2, 2.4] | 0.327 | 1 |
| v1 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v2 | nonerror | 3654 | 26/34 | 0.2 [-0.4, 0.9] | 0.366 | 1 |
| v1 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v2 | error | 459 | 8/4 | -0.9 [-2.8, 0.9] | 0.388 | 1 |
| v1 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v2 | nonerror | 3654 | 20/92 | 2.0 [1.3, 2.7] | 1.96e-11 | 1.06e-09 |
| v1 | AlignScore-base | t6_alignscore_base unf_v2 | error | 459 | 14/12 | -0.4 [-3.3, 2.6] | 0.845 | 1 |
| v1 | AlignScore-base | t6_alignscore_base unf_v2 | nonerror | 3654 | 30/97 | 1.8 [1.0, 2.7] | 4.73e-09 | 2.46e-07 |
| v1 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v2 | error | 459 | 20/7 | -2.8 [-6.4, 0.0] | 0.0209 | 0.837 |
| v1 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v2 | nonerror | 3654 | 33/24 | -0.2 [-0.7, 0.3] | 0.289 | 1 |
| v1 | AlignScore-large | v3_alignscore unf_v2 | error | 459 | 17/11 | -1.3 [-4.5, 1.5] | 0.345 | 1 |
| v1 | AlignScore-large | v3_alignscore unf_v2 | nonerror | 3654 | 16/27 | 0.3 [-0.2, 0.8] | 0.127 | 1 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v2 | error | 459 | 20/7 | -2.8 [-6.4, 0.0] | 0.0209 | 0.837 |
| v1 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v2 | nonerror | 3654 | 33/24 | -0.2 [-0.7, 0.3] | 0.289 | 1 |
| v1 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v2 | error | 459 | 34/13 | -4.6 [-8.4, -1.0] | 0.00353 | 0.162 |
| v1 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v2 | nonerror | 3654 | 44/22 | -0.6 [-1.1, -0.1] | 0.00974 | 0.419 |
| v1 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v2 | error | 459 | 25/20 | -1.1 [-5.0, 2.8] | 0.551 | 1 |
| v1 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v2 | nonerror | 3654 | 32/45 | 0.4 [-0.2, 0.9] | 0.171 | 1 |
| v1 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v2 | error | 459 | 25/18 | -1.5 [-5.2, 2.1] | 0.36 | 1 |
| v1 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v2 | nonerror | 3654 | 36/38 | 0.1 [-0.4, 0.5] | 0.907 | 1 |
| v1 | FT alignscore_large_base | FT alignscore_large_base unf_v2 | error | 459 | 17/11 | -1.3 [-4.5, 1.5] | 0.345 | 1 |
| v1 | FT alignscore_large_base | FT alignscore_large_base unf_v2 | nonerror | 3654 | 16/27 | 0.3 [-0.2, 0.8] | 0.127 | 1 |
| v1 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v2 | error | 459 | 34/30 | -0.9 [-5.8, 4.0] | 0.708 | 1 |
| v1 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v2 | nonerror | 3654 | 46/81 | 1.0 [0.2, 1.8] | 0.00255 | 0.123 |
| v1 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v2 | error | 459 | 27/31 | 0.9 [-4.0, 6.1] | 0.694 | 1 |
| v1 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v2 | nonerror | 3654 | 53/171 | 3.2 [2.1, 4.4] | 5.39e-15 | 3.02e-13 |
| v1 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v2 | error | 459 | 34/26 | -1.7 [-6.5, 3.8] | 0.366 | 1 |
| v1 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v2 | nonerror | 3654 | 40/193 | 4.2 [3.1, 5.4] | 2.33e-23 | 1.37e-21 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_r0.5 | error | 426 | 19/68 | 11.5 [6.6, 16.7] | 2.66e-07 | 1.3e-05 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_r0.5 | nonerror | 3679 | 128/366 | 6.5 [4.8, 8.2] | 1.51e-26 | 9.08e-25 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_r1 | error | 426 | 25/41 | 3.8 [-1.0, 8.5] | 0.0648 | 1 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_r1 | nonerror | 3679 | 120/376 | 7.0 [5.3, 8.7] | 2.36e-30 | 1.46e-28 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_r2 | error | 426 | 27/42 | 3.5 [-1.2, 8.3] | 0.0919 | 1 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_r2 | nonerror | 3679 | 190/331 | 3.8 [2.1, 5.6] | 8.6e-10 | 4.47e-08 |
| v2 | FT alignscore_large_base | FT alignscore_large_r0.5 | error | 426 | 27/87 | 14.1 [8.4, 19.8] | 3.28e-08 | 1.64e-06 |
| v2 | FT alignscore_large_base | FT alignscore_large_r0.5 | nonerror | 3679 | 381/134 | -6.7 [-8.3, -5.1] | 2.22e-27 | 1.36e-25 |
| v2 | FT alignscore_large_base | FT alignscore_large_r1 | error | 426 | 30/57 | 6.3 [1.4, 11.4] | 0.00531 | 0.228 |
| v2 | FT alignscore_large_base | FT alignscore_large_r1 | nonerror | 3679 | 527/122 | -11.0 [-12.8, -9.2] | 1.23e-56 | 7.75e-55 |
| v2 | FT alignscore_large_base | FT alignscore_large_r2 | error | 426 | 44/84 | 9.4 [3.2, 15.7] | 0.000567 | 0.0261 |
| v2 | FT alignscore_large_base | FT alignscore_large_r2 | nonerror | 3679 | 566/71 | -13.5 [-15.1, -11.7] | 2.63e-85 | 1.68e-83 |
| v2 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v1 | error | 426 | 7/6 | -0.2 [-2.5, 1.8] | 1 | 1 |
| v2 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v1 | nonerror | 3679 | 30/34 | 0.1 [-0.6, 0.8] | 0.708 | 1 |
| v2 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v1 | error | 426 | 5/2 | -0.7 [-2.0, 0.5] | 0.453 | 1 |
| v2 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v1 | nonerror | 3679 | 17/95 | 2.1 [1.4, 2.9] | 3.44e-13 | 1.89e-11 |
| v2 | AlignScore-base | t6_alignscore_base unf_v1 | error | 426 | 10/5 | -1.2 [-3.2, 0.8] | 0.302 | 1 |
| v2 | AlignScore-base | t6_alignscore_base unf_v1 | nonerror | 3679 | 34/102 | 1.8 [1.0, 2.7] | 9.18e-09 | 4.68e-07 |
| v2 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v1 | error | 426 | 12/4 | -1.9 [-4.3, 0.2] | 0.0768 | 1 |
| v2 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v1 | nonerror | 3679 | 36/23 | -0.4 [-0.9, 0.2] | 0.118 | 1 |
| v2 | AlignScore-large | v3_alignscore unf_v1 | error | 426 | 10/7 | -0.7 [-2.8, 1.4] | 0.629 | 1 |
| v2 | AlignScore-large | v3_alignscore unf_v1 | nonerror | 3679 | 19/27 | 0.2 [-0.3, 0.8] | 0.302 | 1 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v1 | error | 426 | 12/4 | -1.9 [-4.3, 0.2] | 0.0768 | 1 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v1 | nonerror | 3679 | 36/23 | -0.4 [-0.9, 0.2] | 0.118 | 1 |
| v2 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v1 | error | 426 | 34/8 | -6.1 [-9.5, -2.9] | 0.000115 | 0.0055 |
| v2 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v1 | nonerror | 3679 | 37/23 | -0.4 [-0.8, 0.1] | 0.0933 | 1 |
| v2 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v1 | error | 426 | 25/14 | -2.6 [-6.0, 0.7] | 0.109 | 1 |
| v2 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v1 | nonerror | 3679 | 29/44 | 0.4 [-0.1, 0.9] | 0.101 | 1 |
| v2 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v1 | error | 426 | 24/13 | -2.6 [-6.1, 0.9] | 0.1 | 1 |
| v2 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v1 | nonerror | 3679 | 32/38 | 0.2 [-0.3, 0.6] | 0.55 | 1 |
| v2 | FT alignscore_large_base | FT alignscore_large_base unf_v1 | error | 426 | 10/7 | -0.7 [-2.8, 1.4] | 0.629 | 1 |
| v2 | FT alignscore_large_base | FT alignscore_large_base unf_v1 | nonerror | 3679 | 19/27 | 0.2 [-0.3, 0.8] | 0.302 | 1 |
| v2 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v1 | error | 426 | 33/22 | -2.6 [-7.1, 1.8] | 0.178 | 1 |
| v2 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v1 | nonerror | 3679 | 44/80 | 1.0 [0.2, 1.7] | 0.00167 | 0.0736 |
| v2 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v1 | error | 426 | 25/18 | -1.6 [-5.5, 2.1] | 0.36 | 1 |
| v2 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v1 | nonerror | 3679 | 50/174 | 3.4 [2.2, 4.5] | 2.06e-16 | 1.16e-14 |
| v2 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v1 | error | 426 | 31/16 | -3.5 [-7.1, 0.2] | 0.0411 | 1 |
| v2 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v1 | nonerror | 3679 | 40/196 | 4.2 [3.1, 5.5] | 6.14e-24 | 3.56e-22 |
| v2 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v2 | error | 426 | 7/6 | -0.2 [-2.5, 1.8] | 1 | 1 |
| v2 | MiniCheck-RoBERTa | t6_minicheck_roberta unf_v2 | nonerror | 3679 | 33/36 | 0.1 [-0.6, 0.8] | 0.81 | 1 |
| v2 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v2 | error | 426 | 5/2 | -0.7 [-2.0, 0.5] | 0.453 | 1 |
| v2 | MiniCheck-DeBERTa | t6_minicheck_deberta unf_v2 | nonerror | 3679 | 21/96 | 2.0 [1.3, 2.8] | 7.85e-12 | 4.24e-10 |
| v2 | AlignScore-base | t6_alignscore_base unf_v2 | error | 426 | 10/5 | -1.2 [-3.2, 0.8] | 0.302 | 1 |
| v2 | AlignScore-base | t6_alignscore_base unf_v2 | nonerror | 3679 | 32/105 | 2.0 [1.1, 2.9] | 7.68e-10 | 4.07e-08 |
| v2 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v2 | error | 426 | 12/5 | -1.6 [-4.1, 0.5] | 0.143 | 1 |
| v2 | MiniCheck-Flan-T5-Large | v2a_minicheck unf_v2 | nonerror | 3679 | 38/25 | -0.4 [-0.9, 0.2] | 0.131 | 1 |
| v2 | AlignScore-large | v3_alignscore unf_v2 | error | 426 | 10/7 | -0.7 [-2.8, 1.4] | 0.629 | 1 |
| v2 | AlignScore-large | v3_alignscore unf_v2 | nonerror | 3679 | 20/27 | 0.2 [-0.3, 0.8] | 0.381 | 1 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v2 | error | 426 | 12/5 | -1.6 [-4.1, 0.5] | 0.143 | 1 |
| v2 | FT minicheck_ft5_base | FT minicheck_ft5_base unf_v2 | nonerror | 3679 | 38/25 | -0.4 [-0.9, 0.2] | 0.131 | 1 |
| v2 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v2 | error | 426 | 34/8 | -6.1 [-9.5, -2.9] | 0.000115 | 0.0055 |
| v2 | FT minicheck_ft5_r0.5 | FT minicheck_ft5_r0.5 unf_v2 | nonerror | 3679 | 45/23 | -0.6 [-1.1, -0.1] | 0.0109 | 0.457 |
| v2 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v2 | error | 426 | 25/14 | -2.6 [-6.0, 0.7] | 0.109 | 1 |
| v2 | FT minicheck_ft5_r1 | FT minicheck_ft5_r1 unf_v2 | nonerror | 3679 | 32/46 | 0.4 [-0.1, 0.9] | 0.141 | 1 |
| v2 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v2 | error | 426 | 24/13 | -2.6 [-6.1, 0.9] | 0.1 | 1 |
| v2 | FT minicheck_ft5_r2 | FT minicheck_ft5_r2 unf_v2 | nonerror | 3679 | 36/39 | 0.1 [-0.4, 0.6] | 0.817 | 1 |
| v2 | FT alignscore_large_base | FT alignscore_large_base unf_v2 | error | 426 | 10/7 | -0.7 [-2.8, 1.4] | 0.629 | 1 |
| v2 | FT alignscore_large_base | FT alignscore_large_base unf_v2 | nonerror | 3679 | 20/27 | 0.2 [-0.3, 0.8] | 0.381 | 1 |
| v2 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v2 | error | 426 | 33/23 | -2.3 [-6.8, 2.1] | 0.229 | 1 |
| v2 | FT alignscore_large_r0.5 | FT alignscore_large_r0.5 unf_v2 | nonerror | 3679 | 46/83 | 1.0 [0.2, 1.8] | 0.00153 | 0.0687 |
| v2 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v2 | error | 426 | 26/20 | -1.4 [-5.3, 2.5] | 0.461 | 1 |
| v2 | FT alignscore_large_r1 | FT alignscore_large_r1 unf_v2 | nonerror | 3679 | 53/180 | 3.5 [2.3, 4.7] | 1.52e-16 | 8.69e-15 |
| v2 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v2 | error | 426 | 33/16 | -4.0 [-7.6, -0.2] | 0.0223 | 0.913 |
| v2 | FT alignscore_large_r2 | FT alignscore_large_r2 unf_v2 | nonerror | 3679 | 40/201 | 4.4 [3.2, 5.6] | 6.59e-25 | 3.89e-23 |

## Basis check (source: basis_check/per_item.jsonl)

| variant | labels | flagged / scored | recall on auto errors | false alarms on auto correct | flagged that are auto errors | abstentions |
|---|---|---|---|---|---|---|
| full | v1 | 271/5688 = 4.8% | 235/459 | 5/3654 | 235/271 | 193 |
| full | v2 | 271/5688 = 4.8% | 235/426 | 5/3679 | 235/271 | 193 |
| strict | v1 | 134/5688 = 2.4% | 113/459 | 5/3654 | 113/134 | 327 |
| strict | v2 | 134/5688 = 2.4% | 113/426 | 5/3679 | 113/134 | 327 |

## Subtypes (source: analysis/c2_subtypes_per_item.csv)

| subtype | v1 | v2 |
|---|---|---|
| per_kg | 265 | 265 |
| per_m2 | 159 | 126 |
| rest | 33 | 33 |
| unit_swap | 2 | 2 |

Direction, committed rule A: absolute for relative v1 259 / v2 259; relative for absolute v1 131 / v2 98.

Reconciliation: rule A reproduces the audit's 259/131 exactly under v1; rule B gives 255/129 and rule C 253/124, so the ad hoc 255/123 is not reproduced exactly by any committed rule (its first number equals rule B, its second is closest to rule C; the ad hoc rule was never committed, so it cannot be checked further). Under v2, rule A gives 259/98: the 33 fewer 'relative for absolute' items are exactly the m² superscript artefacts (answer per m², label per-m² unit unreadable). The paper should use rule A because it is the comparison that produced the error class itself, and should report the v2 figure alongside (and the adjudicated figure once available).

## No-dose (source: amend1/nodose_rescan.md, analysis/c4_nodose_sensitivity.json)

The 72 no-dose answers were never scored by any checker (scored set = 5,688 = 5,760 - 72), and the 4 parseable ones fall in unverifiable (3) / time_ambiguous (1), which are in neither the error nor the correct set; the main-table PASS rates with the parseable no-dose answers included under their v2 class are therefore identical to the v2 rates (rd2_rates_all.csv, label_set v2). A sensitivity with human labels is defined in prereg/rd2_amendment_1.md section 2.

## Adjudication sheet (source: amend1/sheet_manifest.json, amend1/sheet_strata.md)

Sheet v2 2473 rows (v1 sheet 1845 + 628 added: match_other_context under v1, not drawn as v1 control 556, no_dose_v1 (excluded from the v1 sheet) 72); P1 200 rows (unit_basis 120, correct 40, other 20, value 20); overlap 50 rows.

sha256: sheet v2 `f573bfd617685fd066fc1e6e6a28c7821a9c293e644b9fc2a8927e87af041891`; key v2 `7fe7cc1e99a2cfa10541c8f99613d81b9d7948a6a1bdd778150e7df711539c00` (not committed).
