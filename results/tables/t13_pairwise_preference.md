# T13 — pairwise preference (selection harm)

- **Cohort:** all **valid main DOSE** bases (`instances_main.jsonl`).
- **E1-unit ×1000:** **all** valid `E1-unit-claim` / `E1-unit-evid` rows in `data/t7/instances_e1_unit.jsonl` (**107** claim on main DOSE); generator validated by **30/30** PI sample (`qc/t7_PI_ok_labels.csv`).
- **INV-unit natural:** `rule_natural_unit_conversion_label` + `effective_unit_natural_y` (same gate as T9).
- **Metric:** per base pair, contribute **P(wrong ≥ correct)** — 1 if score(wrong)>score(correct), **0.5 on ties**, 0 if lower. **Cluster bootstrap** over bases (95% CI).
- **Scores:** continuous where logged; else LLM **verdict** (PASS=1, FAIL=0) and **logprob** when present.

- Main DOSE bases: **110**. Structural pair counts (both slices exist): (E1-unit-claim×1000 vs INV-unit natural) **22**, (E1-unit-claim×1000 vs INV-unit (all)) **62**, (E1-unit-claim×1000 vs C0) **107**, (E1-unit-evid×1000 vs C0) **107**, (E1-claim×2 vs INV-unit natural) **20**.

## Pairwise table (19 verifiers; pairs 1, 1′, 2′)

Cells: **P(wrong ≥ correct)** [95% cluster-bootstrap CI] **(n=…)**; **ties counted as 0.5**.

| model | family | mode | (1) ×1000 vs INV nat | (1′) ×1000 vs INV all | (2′) evid×1000 vs C0 |
|---|---|---|---|---|---|
| MiniCheck-RoBERTa | small fine-tuned checkers | continuous | 1.000 [1.000, 1.000] (n=22) | 0.984 [0.952, 1.000] (n=62) | 0.047 [0.009, 0.093] (n=107) |
| SummaC-ZS | small fine-tuned checkers | continuous | 1.000 [1.000, 1.000] (n=22) | 0.984 [0.952, 1.000] (n=62) | 0.117 [0.061, 0.182] (n=107) |
| HHEM | small fine-tuned checkers | continuous | 1.000 [1.000, 1.000] (n=22) | 1.000 [1.000, 1.000] (n=62) | 0.374 [0.290, 0.467] (n=107) |
| MiniCheck-Flan-T5-Large | small fine-tuned checkers | continuous | 0.955 [0.864, 1.000] (n=22) | 0.806 [0.694, 0.903] (n=62) | 0.093 [0.047, 0.159] (n=107) |
| SummaC-Conv | small fine-tuned checkers | continuous | 0.955 [0.886, 1.000] (n=22) | 0.927 [0.871, 0.976] (n=62) | 0.131 [0.084, 0.187] (n=107) |
| MiniCheck-DeBERTa | small fine-tuned checkers | continuous | 0.909 [0.773, 1.000] (n=22) | 0.903 [0.823, 0.968] (n=62) | 0.056 [0.019, 0.103] (n=107) |
| AlignScore-base | small fine-tuned checkers | continuous | 0.909 [0.773, 1.000] (n=22) | 0.952 [0.887, 1.000] (n=62) | 0.159 [0.093, 0.224] (n=107) |
| Granite Guardian 2B | small fine-tuned checkers | continuous | 0.864 [0.682, 1.000] (n=22) | 0.919 [0.839, 0.984] (n=62) | 0.051 [0.014, 0.098] (n=107) |
| AlignScore-large | small fine-tuned checkers | continuous | 0.773 [0.591, 0.909] (n=22) | 0.774 [0.661, 0.871] (n=62) | 0.065 [0.019, 0.112] (n=107) |
| Bespoke-MiniCheck-7B | 7B fine-tuned checker | continuous | 0.227 [0.045, 0.409] (n=22) | 0.226 [0.129, 0.339] (n=62) | 0.028 [0.000, 0.065] (n=107) |
| Llama-3.1-8B (RAGAS) | LLM judges | continuous | 0.500 [0.364, 0.636] (n=22) | 0.484 [0.411, 0.556] (n=62) | 0.274 [0.226, 0.321] (n=106) |
| GPT-4o-mini (MedScore) | LLM judges | continuous | 0.318 [0.227, 0.409] (n=22) | 0.347 [0.274, 0.419] (n=62) | 0.290 [0.238, 0.336] (n=107) |
| Llama-3.3-70B (RAGAS NLI) | LLM judges | continuous | 0.262 [0.167, 0.381] (n=21) | 0.180 [0.123, 0.246] (n=61) | 0.229 [0.182, 0.276] (n=107) |
| Mistral-Small-24B (MedScore) | LLM judges | continuous | 0.182 [0.091, 0.273] (n=22) | 0.169 [0.113, 0.234] (n=62) | 0.201 [0.154, 0.248] (n=107) |
| GPT-4o-mini (RAGAS) | LLM judges | continuous | 0.114 [0.045, 0.205] (n=22) | 0.194 [0.137, 0.258] (n=62) | 0.145 [0.103, 0.187] (n=107) |
| Mistral-Small-3.2-24B (RAGAS) | LLM judges | continuous | 0.091 [0.023, 0.182] (n=22) | 0.081 [0.040, 0.129] (n=62) | 0.266 [0.220, 0.313] (n=107) |
| GPT-4o (MedScore) | LLM judges | continuous | 0.000 [0.000, 0.000] (n=22) | 0.032 [0.008, 0.065] (n=62) | 0.435 [0.402, 0.463] (n=107) |
| Claude Sonnet 4.6 (RAGAS NLI) | LLM judges | continuous | 0.000 [0.000, 0.000] (n=22) | 0.032 [0.008, 0.065] (n=62) | 0.159 [0.117, 0.206] (n=107) |
| Claude Haiku 4.5 (RAGAS) | LLM judges | continuous | 0.000 [0.000, 0.000] (n=22) | 0.040 [0.008, 0.081] (n=62) | 0.070 [0.037, 0.103] (n=107) |

## Other pairs (supplementary)

| model | (2) ×1000 vs C0 | (3) E1×2 vs INV |
|---|---|---|
| AlignScore-base | 0.140 [0.075, 0.206] (n=107) | 0.200 [0.050, 0.400] (n=20) |
| Granite Guardian 2B | 0.000 [0.000, 0.000] (n=107) | 0.400 [0.200, 0.600] (n=20) |
| HHEM | 0.327 [0.243, 0.421] (n=107) | 1.000 [1.000, 1.000] (n=20) |
| MiniCheck-DeBERTa | 0.000 [0.000, 0.000] (n=107) | 0.600 [0.400, 0.800] (n=20) |
| MiniCheck-RoBERTa | 0.056 [0.019, 0.103] (n=107) | 0.250 [0.100, 0.450] (n=20) |
| SummaC-Conv | 0.136 [0.089, 0.187] (n=107) | 0.300 [0.150, 0.475] (n=20) |
| SummaC-ZS | 0.243 [0.159, 0.327] (n=107) | 0.300 [0.100, 0.500] (n=20) |
| MiniCheck-Flan-T5-Large | 0.093 [0.037, 0.150] (n=107) | 0.450 [0.250, 0.650] (n=20) |
| AlignScore-large | 0.028 [0.000, 0.065] (n=107) | 0.100 [0.000, 0.250] (n=20) |
| Bespoke-MiniCheck-7B | 0.000 [0.000, 0.000] (n=107) | 0.100 [0.000, 0.250] (n=20) |
| Mistral-Small-24B (MedScore) | 0.005 [0.000, 0.014] (n=107) | 0.175 [0.075, 0.275] (n=20) |
| GPT-4o (MedScore) | 0.009 [0.000, 0.023] (n=107) | 0.075 [0.000, 0.150] (n=20) |
| GPT-4o-mini (MedScore) | 0.061 [0.028, 0.098] (n=107) | 0.275 [0.175, 0.375] (n=20) |
| Llama-3.3-70B (RAGAS NLI) | 0.038 [0.014, 0.066] (n=106) | 0.200 [0.100, 0.300] (n=20) |
| Claude Sonnet 4.6 (RAGAS NLI) | 0.009 [0.000, 0.023] (n=107) | 0.000 [0.000, 0.000] (n=20) |
| GPT-4o-mini (RAGAS) | 0.056 [0.028, 0.089] (n=107) | 0.075 [0.000, 0.175] (n=20) |
| Claude Haiku 4.5 (RAGAS) | 0.023 [0.005, 0.047] (n=107) | 0.000 [0.000, 0.000] (n=20) |
| Llama-3.1-8B (RAGAS) | 0.094 [0.057, 0.132] (n=106) | 0.375 [0.275, 0.450] (n=20) |
| Mistral-Small-3.2-24B (RAGAS) | 0.042 [0.019, 0.070] (n=107) | 0.025 [0.000, 0.075] (n=20) |

**Figure (pair 1):** `results/figures/t13_pairwise_x1000_vs_inv.png`

## Appendix — superseded best-of-N (footnote only)

The prior **18-base** `PI_ok=Y` best-of-N argmax design was underpowered (×1000 in only 3 bases) and its **tie → lower rank** rule biased **binary** LLM judges. See commit `97d0b79` / `notes/t13_best_of_n.json` for that exploratory table; **do not use for inference.** Primary T13 estimand is pairwise above.

- Legacy example: v1_medscore P(select wrong) ≈ 0.05555555555555555 on n=18 bases.
