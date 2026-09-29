# OpenRouter model audit (V1 / V4 / V1b / V5)

Registry: `notes/openrouter_verifiers.json`. Pins: **v1_medscore** → `mistralai/mistral-small-24b-instruct-2501` @ DeepInfra, **v4_ragas_nli** → `meta-llama/llama-3.3-70b-instruct` @ DeepInfra, **v1b_medscore** → `openai/gpt-4o` @ OpenAI, **v5_ragas_nli** → `anthropic/claude-sonnet-4.6` @ Anthropic.
Quarantine dir: `results/raw/_quarantine`.

**#re-scored** = rows with `api_model` matching registry (post-assert scoring). **#quarantined** = cumulative rows in `.quarantined.jsonl` sidecars (removed from live file).

**T6-B / T12:** not in this registry yet — audit extension pending.

| File | Verifier | Rows | Model @ provider (counts) | #re-scored | #wrong | #unlogged | #quarantined |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `results/raw/e2_main/v1b_medscore.jsonl` | v1b_medscore | 117 | openai/gpt-4o @ OpenAI: 117 | 117 | 0 | 0 | 0 |
| `results/raw/e2_main/v5_ragas_nli.jsonl` | v5_ragas_nli | 117 | anthropic/claude-sonnet-4.6 @ Anthropic: 117 | 117 | 0 | 0 | 0 |
| `results/raw/t2_full/v1b_medscore.jsonl` | v1b_medscore | 533 | openai/gpt-4o @ OpenAI: 533 | 533 | 0 | 0 | 0 |
| `results/raw/t2_full/v5_ragas_nli.jsonl` | v5_ragas_nli | 533 | anthropic/claude-sonnet-4.6 @ Anthropic: 533 | 533 | 0 | 0 | 0 |
| `results/raw/t2_pilot/v1b_medscore.jsonl` | v1b_medscore | 100 | openai/gpt-4o @ OpenAI: 100 | 100 | 0 | 0 | 0 |
| `results/raw/t2_pilot/v5_ragas_nli.jsonl` | v5_ragas_nli | 100 | anthropic/claude-sonnet-4.6 @ Anthropic: 100 | 100 | 0 | 0 | 0 |
| `results/raw/t3_smoke/v1b_medscore.jsonl` | v1b_medscore | 1 | openai/gpt-4o @ OpenAI: 1 | 1 | 0 | 0 | 0 |
| `results/raw/t3_smoke/v5_ragas_nli.jsonl` | v5_ragas_nli | 1 | anthropic/claude-sonnet-4.6 @ Anthropic: 1 | 1 | 0 | 0 | 0 |
| `results/raw/t3_t2/v1b_medscore.jsonl` | v1b_medscore | 497 | openai/gpt-4o @ OpenAI: 497 | 497 | 0 | 0 | 0 |
| `results/raw/t3_t2/v5_ragas_nli.jsonl` | v5_ragas_nli | 497 | anthropic/claude-sonnet-4.6 @ Anthropic: 497 | 497 | 0 | 0 | 0 |
| `results/raw/t4_eco/v1_medscore.jsonl` | v1_medscore | 438 | mistralai/mistral-small-24b-instruct-2501 @ DeepInfra: 438 | 438 | 0 | 0 | 0 |
| `results/raw/t4_eco/v1b_medscore.jsonl` | v1b_medscore | 438 | openai/gpt-4o @ OpenAI: 437; (no api_model) @ -: 1 | 437 | 0 | 1 | 0 |
| `results/raw/t4_eco/v4_ragas_nli.jsonl` | v4_ragas_nli | 438 | (no api_model) @ -: 438 | 0 | 0 | 438 | 0 |
| `results/raw/t4_eco/v5_ragas_nli.jsonl` | v5_ragas_nli | 444 | anthropic/claude-sonnet-4.6 @ Anthropic: 444 | 444 | 0 | 0 | 0 |
| `results/raw/t4c_eco/v1b_medscore.jsonl` | v1b_medscore | 139 | openai/gpt-4o @ OpenAI: 139 | 139 | 0 | 0 | 0 |
| `results/raw/t4c_eco/v4_ragas_nli.jsonl` | v4_ragas_nli | 139 | (no api_model) @ -: 139 | 0 | 0 | 139 | 0 |
| `results/raw/t4c_eco/v5_ragas_nli.jsonl` | v5_ragas_nli | 139 | anthropic/claude-sonnet-4.6 @ Anthropic: 139 | 139 | 0 | 0 | 0 |
| `results/raw/t7/v1_medscore.jsonl` | v1_medscore | 230 | mistralai/mistral-small-24b-instruct-2501 @ DeepInfra: 230 | 230 | 0 | 0 | 0 |
| `results/raw/t7/v1b_medscore.jsonl` | v1b_medscore | 230 | openai/gpt-4o @ OpenAI: 230 | 230 | 0 | 0 | 0 |
| `results/raw/t7/v4_ragas_nli.jsonl` | v4_ragas_nli | 230 | (no api_model) @ -: 230 | 0 | 0 | 230 | 0 |
| `results/raw/t7/v5_ragas_nli.jsonl` | v5_ragas_nli | 230 | anthropic/claude-sonnet-4.6 @ Anthropic: 230 | 230 | 0 | 0 | 0 |
| `results/raw/t8/v1b_medscore.jsonl` | v1b_medscore | 200 | openai/gpt-4o @ OpenAI: 200 | 200 | 0 | 0 | 0 |
| `results/raw/v1_medscore.jsonl` | v1_medscore | 3541 | mistralai/mistral-small-24b-instruct-2501 @ DeepInfra: 3536; (no api_model) @ -: 5 | 3536 | 0 | 5 | 0 |
| `results/raw/v4_ragas_nli.jsonl` | v4_ragas_nli | 1085 | (no api_model) @ -: 1085 | 0 | 0 | 1085 | 0 |
| `results/raw_m1/t7/v1_medscore.jsonl` | v1_medscore | 345 | mistralai/mistral-small-24b-instruct-2501 @ DeepInfra: 345 | 345 | 0 | 0 | 0 |
| `results/raw_m1/t7/v4_ragas_nli.jsonl` | v4_ragas_nli | 18 | meta-llama/llama-3.3-70b-instruct @ DeepInfra: 18 | 18 | 0 | 0 | 24 |
| `results/raw_m1/v1_medscore.jsonl` | v1_medscore | 1306 | mistralai/mistral-small-24b-instruct-2501 @ DeepInfra: 1306 | 1306 | 0 | 0 | 0 |
| `results/raw_m1/v4_ragas_nli.jsonl` | v4_ragas_nli | 436 | (no api_model) @ -: 436 | 0 | 0 | 436 | 0 |
| `results/raw_threshold/v1_medscore.jsonl` | v1_medscore | 221 | mistralai/mistral-small-24b-instruct-2501 @ DeepInfra: 221 | 221 | 0 | 0 | 0 |
| `results/raw_threshold/v4_ragas_nli.jsonl` | v4_ragas_nli | 221 | (no api_model) @ -: 221 | 0 | 0 | 221 | 0 |
