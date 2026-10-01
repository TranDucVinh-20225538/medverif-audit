# API re-run agreement (LLM judges)

Generated 2026-10-01T05:43:44.171557+00:00 by `scripts/rerun_agreement.py` (seed 20261001). Sample per judge: 20 C0 + 20 INV-claim unit_conversion + 20 E1-unit-claim x1000 (main DOSE bases), same prompt/parser/model pin/provider, temperature 0. Stored verdicts = the main-card loader (`t13_best_of_n_report.merged_score_rows`).

| Judge | identical verdicts | C0 | INV-unit | E1-unit-claim x1000 | PARSE_FAIL (new) | api models seen | spend (USD) |
|---|---:|---:|---:|---:|---:|---|---:|
| Mistral-Small-24B (MedScore) | 58/60 (of 60) | 20/20 | 18/20 | 20/20 | 0 | mistralai/mistral-small-24b-instruct-2501@DeepInfra | 0.0016 |
| GPT-4o-mini (MedScore) | 57/60 (of 60) | 20/20 | 17/20 | 20/20 | 0 | openai/gpt-4o-mini@OpenAI | 0.0034 |
| GPT-4o (MedScore) | 60/60 (of 60) | 20/20 | 20/20 | 20/20 | 0 | openai/gpt-4o@OpenAI | 0.0619 |
| Llama-3.1-8B (RAGAS) | 52/60 (of 60) | 19/20 | 16/20 | 17/20 | 0 | meta-llama/llama-3.1-8b-instruct@DeepInfra | 0.0013 |
| Llama-3.3-70B (RAGAS NLI) | 56/60 (of 60) | 20/20 | 18/20 | 18/20 | 0 | meta-llama/llama-3.3-70b-instruct@DeepInfra | 0.0075 |
| Mistral-Small-3.2-24B (RAGAS) | 56/60 (of 60) | 20/20 | 19/20 | 17/20 | 0 | mistralai/mistral-small-3.2-24b-instruct@DeepInfra | 0.0054 |
| GPT-4o-mini (RAGAS) | 53/60 (of 60) | 19/20 | 15/20 | 19/20 | 0 | openai/gpt-4o-mini@OpenAI | 0.0118 |
| Claude Haiku 4.5 (RAGAS) | 59/60 (of 60) | 20/20 | 19/20 | 20/20 | 0 | anthropic/claude-haiku-4.5@Anthropic | 0.1036 |
| Claude Sonnet 4.6 (RAGAS NLI) | 60/60 (of 60) | 20/20 | 20/20 | 20/20 | 0 | anthropic/claude-sonnet-4.6@Anthropic | 0.2985 |

Total spend (sum of api_cost_usd in outputs): **0.4951 USD**; this run: 0.4935 USD; cap 3.00 USD.

