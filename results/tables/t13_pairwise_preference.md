<!-- LEGACY — not for paper. Use results/tables/card_main.md and qvc/paper_numbers.json from scripts/compute_paper_numbers.py. -->

# T13 — pairwise preference (selection harm)

- **Cohort:** all **valid main DOSE** bases (`instances_main.jsonl`).
- **E1-unit ×1000:** **all** valid `E1-unit-claim` / `E1-unit-evid` rows in `data/t7/instances_e1_unit.jsonl` (**110** claim on main DOSE); generator validated by **30/30** PI sample (`qc/t7_PI_ok_labels.csv`).
- **INV-unit natural:** `rule_natural_unit_conversion_label` + `effective_unit_natural_y` (same gate as T9).
- **Metric:** per base pair, contribute **P(wrong ≥ correct)** — 1 if score(wrong)>score(correct), **0.5 on ties**, 0 if lower. **Cluster bootstrap** over bases (95% CI).
- **Scores:** continuous where logged; else LLM **verdict** (PASS=1, FAIL=0) and **logprob** when present.

- Main DOSE bases: **115**. Structural pair counts (both slices exist): (E1-unit-claim×1000 vs INV-unit natural) **54**, (E1-unit-claim×1000 vs INV-unit (all)) **65**, (E1-unit-claim×1000 vs C0) **110**, (E1-unit-evid×1000 vs C0) **110**, (E1-claim×2 vs INV-unit natural) **52**.

## Pairwise table (19 verifiers; pairs 1, 1′, 2′)

Cells: **P(wrong ≥ correct)** [95% cluster-bootstrap CI] **(n=…)**; **ties counted as 0.5**.

| model | family | mode | (1) ×1000 vs INV nat | (1′) ×1000 vs INV all | (2′) evid×1000 vs C0 |
|---|---|---|---|---|---|
| MiniCheck-Flan-T5-Large | small fine-tuned checkers | continuous | 0.796 [0.685, 0.907] (n=54) | 0.723 [0.615, 0.831] (n=65) | 0.091 [0.036, 0.145] (n=110) |
| AlignScore-large | small fine-tuned checkers | continuous | 0.759 [0.648, 0.870] (n=54) | 0.677 [0.569, 0.785] (n=65) | 0.064 [0.018, 0.109] (n=110) |
| MiniCheck-RoBERTa | small fine-tuned checkers | continuous | — | — | 0.045 [0.000, 0.136] (n=22) |
| MiniCheck-DeBERTa | small fine-tuned checkers | continuous | — | — | 0.045 [0.000, 0.136] (n=22) |
| AlignScore-base | small fine-tuned checkers | continuous | — | — | 0.182 [0.045, 0.364] (n=22) |
| SummaC-ZS | small fine-tuned checkers | continuous | — | — | 0.159 [0.045, 0.318] (n=22) |
| SummaC-Conv | small fine-tuned checkers | continuous | — | — | 0.182 [0.068, 0.295] (n=22) |
| HHEM | small fine-tuned checkers | continuous | — | — | 0.364 [0.182, 0.591] (n=22) |
| Granite Guardian | small fine-tuned checkers | continuous | — | — | 0.045 [0.000, 0.136] (n=22) |
| Bespoke-MiniCheck-7B | 7B fine-tuned checker | continuous | 0.204 [0.111, 0.315] (n=54) | 0.231 [0.138, 0.338] (n=65) | 0.027 [0.000, 0.064] (n=110) |
| Llama-3.1-8B (RAGAS) | LLM judges | continuous | 0.509 [0.435, 0.583] (n=54) | 0.477 [0.408, 0.546] (n=65) | 0.266 [0.220, 0.317] (n=109) |
| GPT-4o-mini (MedScore) | LLM judges | continuous | 0.343 [0.259, 0.417] (n=54) | 0.338 [0.269, 0.408] (n=65) | 0.286 [0.241, 0.332] (n=110) |
| Mistral-Small-24B (MedScore) | LLM judges | continuous | 0.185 [0.120, 0.250] (n=54) | 0.177 [0.123, 0.238] (n=65) | 0.055 [0.027, 0.086] (n=110) |
| GPT-4o-mini (RAGAS) | LLM judges | continuous | 0.176 [0.111, 0.241] (n=54) | 0.192 [0.131, 0.254] (n=65) | 0.141 [0.100, 0.182] (n=110) |
| Llama-3.3-70B (RAGAS NLI) | LLM judges | continuous | 0.135 [0.077, 0.202] (n=52) | 0.135 [0.079, 0.198] (n=63) | 0.086 [0.052, 0.124] (n=105) |
| Mistral-Small-3.2-24B (RAGAS) | LLM judges | continuous | 0.093 [0.046, 0.148] (n=54) | 0.077 [0.038, 0.123] (n=65) | 0.259 [0.214, 0.305] (n=110) |
| Claude Haiku 4.5 (RAGAS) | LLM judges | continuous | 0.046 [0.009, 0.093] (n=54) | 0.038 [0.008, 0.069] (n=65) | 0.068 [0.036, 0.100] (n=110) |
| GPT-4o (MedScore) | LLM judges | continuous | 0.037 [0.009, 0.074] (n=54) | 0.031 [0.008, 0.062] (n=65) | 0.427 [0.391, 0.459] (n=110) |
| Claude Sonnet 4.6 (RAGAS NLI) | LLM judges | continuous | 0.037 [0.009, 0.074] (n=54) | 0.031 [0.008, 0.062] (n=65) | 0.155 [0.114, 0.200] (n=110) |

## Other pairs (supplementary)

| model | (2) ×1000 vs C0 | (3) E1×2 vs INV |
|---|---|---|
| AlignScore-base | 0.136 [0.000, 0.273] (n=22) | — |
| Granite Guardian | 0.000 [0.000, 0.000] (n=22) | — |
| HHEM | 0.364 [0.182, 0.591] (n=22) | — |
| MiniCheck-DeBERTa | 0.000 [0.000, 0.000] (n=22) | — |
| MiniCheck-RoBERTa | 0.000 [0.000, 0.000] (n=22) | — |
| SummaC-Conv | 0.205 [0.091, 0.318] (n=22) | — |
| SummaC-ZS | 0.364 [0.182, 0.591] (n=22) | — |
| MiniCheck-Flan-T5-Large | 0.091 [0.036, 0.145] (n=110) | 0.288 [0.173, 0.404] (n=52) |
| AlignScore-large | 0.027 [0.000, 0.064] (n=110) | 0.038 [0.000, 0.096] (n=52) |
| Bespoke-MiniCheck-7B | 0.000 [0.000, 0.000] (n=110) | 0.038 [0.000, 0.096] (n=52) |
| Mistral-Small-24B (MedScore) | 0.005 [0.000, 0.014] (n=110) | 0.173 [0.115, 0.240] (n=52) |
| GPT-4o (MedScore) | 0.009 [0.000, 0.023] (n=110) | 0.058 [0.019, 0.106] (n=52) |
| GPT-4o-mini (MedScore) | 0.059 [0.027, 0.091] (n=110) | 0.269 [0.202, 0.337] (n=52) |
| Llama-3.3-70B (RAGAS NLI) | 0.014 [0.000, 0.033] (n=106) | 0.160 [0.090, 0.230] (n=50) |
| Claude Sonnet 4.6 (RAGAS NLI) | 0.009 [0.000, 0.023] (n=110) | 0.019 [0.000, 0.048] (n=52) |
| GPT-4o-mini (RAGAS) | 0.055 [0.027, 0.086] (n=110) | 0.125 [0.067, 0.192] (n=52) |
| Claude Haiku 4.5 (RAGAS) | 0.023 [0.005, 0.045] (n=110) | 0.038 [0.010, 0.077] (n=52) |
| Llama-3.1-8B (RAGAS) | 0.092 [0.055, 0.128] (n=109) | 0.375 [0.308, 0.433] (n=52) |
| Mistral-Small-3.2-24B (RAGAS) | 0.041 [0.018, 0.068] (n=110) | 0.029 [0.000, 0.067] (n=52) |

**Figure (pair 1):** `results/figures/t13_pairwise_x1000_vs_inv.png`

## Appendix — superseded best-of-N (footnote only)

The prior **18-base** `PI_ok=Y` best-of-N argmax design was underpowered (×1000 in only 3 bases) and its **tie → lower rank** rule biased **binary** LLM judges. See commit `97d0b79` / `notes/t13_best_of_n.json` for that exploratory table; **do not use for inference.** Primary T13 estimand is pairwise above.

- Legacy example: v1_medscore P(select wrong) ≈ 0.05555555555555555 on n=18 bases.
