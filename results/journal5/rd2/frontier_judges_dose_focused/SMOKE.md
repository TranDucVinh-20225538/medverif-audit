# Dose-focused frontier judges — SMOKE

Prompt: `dose_focused_v1@2026-10-26`. Date: 2026-10-26.

## Smoke composition (n=30)

- 10 v3-correct closed that RAGAS false-rejected
- 10 v3 unit/basis errors closed
- 10 other closed (not error/correct/correct_suspect)

## Per-model smoke

| model | new | PASS | FAIL | PARSE_FAIL | PF%% | spent$ |
|---|---:|---:|---:|---:|---:|---:|
| `anthropic/claude-sonnet-4.6` | 30 | 11 | 19 | 0 | 0.0 | 0.0827 |
| `openai/gpt-4o` | 30 | 11 | 19 | 0 | 0.0 | 0.1332 |
| `deepseek/deepseek-chat` | 30 | 11 | 19 | 0 | 0.0 | 0.1391 |

## GO/NO-GO

**Decision: GO**

- GO: ≥1 model lowered FR on 10 correct smoke rows vs RAGAS without missing all 10 errors

| model | FR dose/10 | FR RAGAS/10 | miss dose/10 | better FR |
|---|---:|---:|---:|:---:|
| `anthropic/claude-sonnet-4.6` | 1 | 6 | 0 | Y |
| `openai/gpt-4o` | 3 | 9 | 1 | Y |
| `deepseek/deepseek-chat` | 2 | 7 | 0 | Y |

Spent total smoke: **$0.1391**
