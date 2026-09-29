# T14 / T3 filter view (#3 — existing scores only)

At each verifier’s **default threshold** (see `configs/verifiers.yaml`):
- **keep rate ×1000** = P(PASS | E1-unit-claim ×1000 wrong) — bad if high (= **1−US**).
- **drop rate INV natural** = P(FAIL | INV-unit natural correct) — bad if high (= **1−QI**).
- **T13 pair (1)** = P(score(×1000) ≥ score(INV natural)) with tie=0.5.

- ×1000 claim instances (main DOSE): **112**; INV natural: **55**.

| model | family | keep ×1000 | drop INV | T13 pair(1) | n ×1000 | n INV |
|---|---|---:|---:|---:|---:|---:|
| AlignScore-base | small fine-tuned checkers | 0.795 | — | — | 112 | 0 |
| Granite Guardian | small fine-tuned checkers | 0.527 | — | — | 112 | 0 |
| HHEM | small fine-tuned checkers | 0.964 | — | — | 112 | 0 |
| MiniCheck-DeBERTa | small fine-tuned checkers | 0.125 | — | — | 112 | 0 |
| MiniCheck-RoBERTa | small fine-tuned checkers | 0.598 | — | — | 112 | 0 |
| SummaC-Conv | small fine-tuned checkers | 0.330 | — | — | 112 | 0 |
| SummaC-ZS | small fine-tuned checkers | 0.607 | — | — | 112 | 0 |
| MiniCheck-Flan-T5-Large | small fine-tuned checkers | 0.482 | 0.909 | 0.800 | 112 | 55 |
| AlignScore-large | small fine-tuned checkers | 0.446 | 0.764 | 0.764 | 112 | 55 |
| Bespoke-MiniCheck-7B | 7B fine-tuned checker | 0.321 | 0.200 | 0.200 | 112 | 55 |
| Mistral-Small-24B (MedScore) | LLM judges | 0.009 | 0.345 | 0.182 | 112 | 55 |
| GPT-4o (MedScore) | LLM judges | 0.018 | 0.036 | 0.036 | 112 | 55 |
| GPT-4o-mini (MedScore) | LLM judges | 0.107 | 0.509 | 0.336 | 112 | 55 |
| Llama-3.3-70B (RAGAS NLI) | LLM judges | 0.027 | 0.226 | 0.132 | 112 | 53 |
| Claude Sonnet 4.6 (RAGAS NLI) | LLM judges | 0.018 | 0.036 | 0.036 | 112 | 55 |
| GPT-4o-mini (RAGAS) | LLM judges | 0.071 | 0.236 | 0.173 | 112 | 55 |
| Claude Haiku 4.5 (RAGAS) | LLM judges | 0.018 | 0.055 | 0.045 | 112 | 55 |
| Llama-3.1-8B (RAGAS) | LLM judges | 0.152 | 0.764 | 0.509 | 112 | 55 |
| Mistral-Small-3.2-24B (RAGAS) | LLM judges | 0.080 | 0.036 | 0.091 | 112 | 55 |

Figure: `results/figures/t14_t3_filter_reward.png`

