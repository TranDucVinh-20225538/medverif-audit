# Second fine-tune: AlignScore-large and MiniCheck-Flan-T5 (journal revision)

Same recipe as the published MiniCheck-RoBERTa fine-tune (`scripts/t15_train.py`: 3 epochs, lr 2e-5, batch 8, max_len 512, seed 42, best dev loss, threshold 0.5) on the T15 dose pairs mixed with ANLI at n_ANLI/n_dose = 0.5 / 1 / 2 (`results/journal/ft/data_manifest.json`). Library inference paths as in the paper.

## Main DOSE card (C0-conditional; 95% base-clustered bootstrap CI)

| model | c0_pass_rate | qi_all | qi_nat | ns | us_claim_up | us_evid_up |
|---|---|---|---|---|---|---|
| alignscore_large_base | 94.5 [90.0, 98.2] | 24.6 [14.0, 35.1] | 19.0 [4.8, 38.1] | 94.0 [89.9, 97.5] | 53.5 [43.6, 63.4] | 40.6 [31.7, 50.5] |
| alignscore_large_r0.5 | 86.4 [80.0, 92.7] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 96.7 [93.9, 98.9] | 100.0 [100.0, 100.0] | 98.9 [95.7, 100.0] |
| alignscore_large_r1 | 90.0 [84.5, 94.5] | 94.5 [89.1, 100.0] | 95.0 [85.0, 100.0] | 99.5 [98.4, 100.0] | 93.8 [88.5, 97.9] | 96.9 [92.7, 100.0] |
| alignscore_large_r2 | 86.4 [80.0, 92.7] | 98.1 [94.2, 100.0] | 94.7 [84.2, 100.0] | 98.3 [96.1, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| minicheck_ft5_base | 96.4 [92.7, 99.1] | 8.3 [1.7, 15.0] | 4.5 [0.0, 13.6] | 88.7 [83.4, 93.7] | 52.4 [42.7, 61.2] | 21.4 [14.6, 29.1] |
| minicheck_ft5_r0.5 | 98.2 [95.5, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 96.1 [92.4, 99.0] | 100.0 [100.0, 100.0] | 99.0 [97.1, 100.0] |
| minicheck_ft5_r1 | 96.4 [92.7, 99.1] | 98.3 [94.9, 100.0] | 95.5 [86.4, 100.0] | 96.6 [93.1, 99.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| minicheck_ft5_r2 | 96.4 [92.7, 99.1] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 97.5 [94.6, 99.5] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |

Reference (published MiniCheck-RoBERTa base vs ft): see `notes/t15_report.md` / `notes/t15_card.json`.

## LLM-AggreFact (macro BAcc over datasets; stratified n=3000, seed 42; item bootstrap CI)

| model | macro BAcc [95% CI] | n |
|---|---|---|
| alignscore_large_base | 0.7116 [0.6849, 0.7590] | 3000 |
| alignscore_large_r0.5 | 0.7116 [0.6846, 0.7578] | 3000 |
| alignscore_large_r1 | 0.7144 [0.6891, 0.7582] | 3000 |
| alignscore_large_r2 | 0.7170 [0.6909, 0.7605] | 3000 |
| minicheck_ft5_base | 0.7836 [0.7429, 0.8077] | 3000 |
| minicheck_ft5_r0.5 | 0.7687 [0.7264, 0.7926] | 3000 |
| minicheck_ft5_r1 | 0.7824 [0.7405, 0.8071] | 3000 |
| minicheck_ft5_r2 | 0.7286 [0.7046, 0.7780] | 3000 |

## Out-of-template real RAG: T24b (C0-conditional; bootstrap over questions)

| model | T24b C0 PASS | unit-up FAIL given C0 | unit-down FAIL given C0 | value×10 FAIL given C0 |
|---|---|---|---|---|
| alignscore_large_base | 94.3% (n=53) | 70.5% (n=44) | 17.9% (n=39) | 98.0% (n=50) |
| alignscore_large_r0.5 | 75.5% (n=53) | 100.0% (n=35) | 100.0% (n=30) | 97.5% (n=40) |
| alignscore_large_r1 | 81.1% (n=53) | 91.9% (n=37) | 100.0% (n=33) | 97.7% (n=43) |
| alignscore_large_r2 | 79.2% (n=53) | 97.3% (n=37) | 100.0% (n=33) | 95.2% (n=42) |
| minicheck_ft5_base | 92.5% (n=53) | 55.8% (n=43) | 10.5% (n=38) | 93.9% (n=49) |
| minicheck_ft5_r0.5 | 100.0% (n=53) | 100.0% (n=47) | 100.0% (n=41) | 100.0% (n=53) |
| minicheck_ft5_r1 | 98.1% (n=53) | 100.0% (n=46) | 100.0% (n=40) | 100.0% (n=52) |
| minicheck_ft5_r2 | 98.1% (n=53) | 100.0% (n=46) | 100.0% (n=40) | 96.2% (n=52) |

## Out-of-template real RAG: journal RAG pack (C0-conditional; bootstrap over questions)

| model | RAG C0 PASS | conv PASS given C0 | value×2 FAIL given C0 | unit-up FAIL given C0 |
|---|---|---|---|---|
| alignscore_large_base | 93.2% (n=340) | 26.8% (n=138) | 75.7% (n=317) | 54.8% (n=230) |
| alignscore_large_r0.5 | 88.2% (n=340) | 100.0% (n=130) | 59.3% (n=300) | 52.7% (n=220) |
| alignscore_large_r1 | 87.9% (n=340) | 98.4% (n=129) | 61.9% (n=299) | 50.2% (n=215) |
| alignscore_large_r2 | 89.1% (n=340) | 99.2% (n=131) | 58.1% (n=303) | 51.4% (n=220) |
| minicheck_ft5_base | 91.8% (n=340) | 39.0% (n=136) | 74.0% (n=312) | 21.8% (n=234) |
| minicheck_ft5_r0.5 | 97.1% (n=340) | 99.3% (n=142) | 89.1% (n=330) | 95.1% (n=244) |
| minicheck_ft5_r1 | 94.1% (n=340) | 97.1% (n=136) | 95.3% (n=320) | 97.5% (n=237) |
| minicheck_ft5_r2 | 95.3% (n=340) | 97.9% (n=141) | 93.5% (n=324) | 94.6% (n=240) |

## Training runs

| run | best dev loss | epochs (dev loss) | n_train |
|---|---|---|---|
| train_alignscore_large_r0.5 | 0.0443 | 0.0556, 0.0513, 0.0443 | 15762 |
| train_alignscore_large_r1 | 0.0385 | 0.0385, 0.0397, 0.0415 | 21023 |
| train_alignscore_large_r2 | 0.0473 | 0.0564, 0.0500, 0.0473 | 31524 |
| train_minicheck_ft5_r0.5 | 0.0845 | 0.0899, 0.0845, 0.0914 | 15762 |
| train_minicheck_ft5_r1 | 0.0749 | 0.0749, 0.0853, 0.0901 | 21023 |
| train_minicheck_ft5_r2 | 0.0716 | 0.0787, 0.0716, 0.0816 | 31524 |
