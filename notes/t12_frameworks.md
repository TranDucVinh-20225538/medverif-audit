# T12 — external eval frameworks (default configs)

Pinned OpenRouter models in `notes/openrouter_verifiers.json`.

| Framework | Metric | Default (upstream) | Our pin (OpenRouter) | Threshold / notes |
| --- | --- | --- | --- | --- |
| RAGAS | Faithfulness | statement split + NLI; judge often `gpt-4o-mini` | `openai/gpt-4o-mini` @ OpenAI | full default pipeline |
| DeepEval | FaithfulnessMetric | model `gpt-4o` | `openai/gpt-4o` @ OpenAI | threshold **0.5** (DeepEval default) |
| TruLens | Groundedness | GPT feedback provider | `openai/gpt-4o-mini` @ OpenAI | deviation logged if API differs |

Scope: C0, E1-claim x2, INV-unit (± natural), T7 E1-unit claim/evid, INV frequency/route (PI_ok=Y).

Pilot: **20** items per slice → full. Budget cap **$12**; stop on HTTP 402 or credit **< $2**.

Run: `jobs/run_t12_frameworks.sh` → `results/raw/t12/` + `notes/t12_qvc_cards.json`.
