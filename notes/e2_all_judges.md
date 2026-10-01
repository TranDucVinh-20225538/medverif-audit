# E2 (faithful-but-wrong) PASS, all 9 LLM judges, main DOSE card cohort

Generated 2026-10-01T05:50:21.863430+00:00 by `scripts/e2_remaining_judges.py`. Cohort: 220 E2 rows (110 bases x {x2, x10}) from `load_main_dose_instances()`; PASS rate over PASS/FAIL rows, conditional on the base's C0 verdict = PASS for that judge (card loader). Higher = worse (the evidence was edited consistently, so PASS is 'faithful but wrong').

| Judge | E2 PASS given C0 PASS | % | E2 PASS (all) | PARSE_FAIL | coverage | source(s) | api model@provider |
|---|---:|---:|---:|---:|---:|---|---|
| Mistral-Small-24B (MedScore) | 204/218 | 93.6% | 204/219 | 0 | 219/220 | card_loader | mistralai/mistral-small-24b-instruct-2501@DeepInfra |
| GPT-4o-mini (MedScore) | 207/218 | 95.0% | 209/220 | 0 | 220/220 | t23 | openai/gpt-4o-mini@OpenAI |
| GPT-4o (MedScore) | 184/220 | 83.6% | 184/220 | 0 | 220/220 | e2_remaining | openai/gpt-4o@OpenAI |
| Llama-3.1-8B (RAGAS) | 203/212 | 95.8% | 209/220 | 0 | 220/220 | t23 | meta-llama/llama-3.1-8b-instruct@DeepInfra |
| Llama-3.3-70B (RAGAS NLI) | 210/218 | 96.3% | 210/218 | 0 | 218/220 | card_loader | meta-llama/llama-3.3-70b-instruct@DeepInfra |
| Mistral-Small-3.2-24B (RAGAS) | 218/220 | 99.1% | 218/220 | 0 | 220/220 | t23 | mistralai/mistral-small-3.2-24b-instruct@DeepInfra |
| GPT-4o-mini (RAGAS) | 207/212 | 97.6% | 207/220 | 0 | 220/220 | t23 | openai/gpt-4o-mini@OpenAI |
| Claude Haiku 4.5 (RAGAS) | 210/214 | 98.1% | 213/220 | 0 | 220/220 | t23 | anthropic/claude-haiku-4.5@Anthropic |
| Claude Sonnet 4.6 (RAGAS NLI) | 217/220 | 98.6% | 217/220 | 0 | 220/220 | e2_remaining | anthropic/claude-sonnet-4.6@Anthropic |

Spend this run: 1.2813 USD.
