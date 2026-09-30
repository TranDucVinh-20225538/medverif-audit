# T14 / T3 filter view (#3 — existing scores only)

At each verifier’s **default threshold** (see `configs/verifiers.yaml`):
- **keep rate ×1000** = P(PASS | E1-unit-claim ×1000 wrong) — bad if high (= **1−US**).
- **drop rate INV natural** = P(FAIL | INV-unit natural correct) — bad if high (= **1−QI**).
- **T13 pair (1)** = P(score(×1000) ≥ score(INV natural)) with tie=0.5.

- ×1000 claim instances (main DOSE): **107**; INV natural: **22**.

| model | family | keep ×1000 | drop INV | T13 pair(1) | n ×1000 | n INV |
|---|---|---:|---:|---:|---:|---:|
| AlignScore-base | small fine-tuned checkers | 0.822 | 0.773 | 0.909 | 107 | 22 |
| Granite Guardian 2B | small fine-tuned checkers | 0.533 | 0.818 | 0.864 | 107 | 22 |
| HHEM | small fine-tuned checkers | 0.963 | 0.864 | 1.000 | 107 | 22 |
| MiniCheck-DeBERTa | small fine-tuned checkers | 0.121 | 0.955 | 0.909 | 107 | 22 |
| MiniCheck-RoBERTa | small fine-tuned checkers | 0.598 | 1.000 | 1.000 | 107 | 22 |
| SummaC-Conv | small fine-tuned checkers | 0.336 | 1.000 | 0.955 | 107 | 22 |
| SummaC-ZS | small fine-tuned checkers | 0.589 | 0.955 | 1.000 | 107 | 22 |
| MiniCheck-Flan-T5-Large | small fine-tuned checkers | 0.458 | 0.955 | 0.955 | 107 | 22 |
| AlignScore-large | small fine-tuned checkers | 0.449 | 0.818 | 0.773 | 107 | 22 |
| Bespoke-MiniCheck-7B | 7B fine-tuned checker | 0.327 | 0.182 | 0.227 | 107 | 22 |
| Mistral-Small-24B (MedScore) | LLM judges | 0.009 | 0.364 | 0.182 | 107 | 22 |
| GPT-4o (MedScore) | LLM judges | 0.019 | 0.000 | 0.000 | 107 | 22 |
| GPT-4o-mini (MedScore) | LLM judges | 0.112 | 0.500 | 0.318 | 107 | 22 |
| Llama-3.3-70B (RAGAS NLI) | LLM judges | 0.075 | 0.273 | 0.262 | 106 | 22 |
| Claude Sonnet 4.6 (RAGAS NLI) | LLM judges | 0.019 | 0.000 | 0.000 | 107 | 22 |
| GPT-4o-mini (RAGAS) | LLM judges | 0.075 | 0.136 | 0.114 | 107 | 22 |
| Claude Haiku 4.5 (RAGAS) | LLM judges | 0.019 | 0.000 | 0.000 | 107 | 22 |
| Llama-3.1-8B (RAGAS) | LLM judges | 0.159 | 0.727 | 0.500 | 107 | 22 |
| Mistral-Small-3.2-24B (RAGAS) | LLM judges | 0.084 | 0.000 | 0.091 | 107 | 22 |

Figure: `results/figures/t14_t3_filter_reward.png`

