# RD2 dose-focused frontier judges — report

**Exploratory.** Prompt `dose_focused_v1@2026-10-26`. Not HTML RAGAS (RAGAS artefacts untouched).

## Models & cost

| slug | api_model | n | verdicts | cost USD |
|---|---|---:|---|---:|
| `claude_sonnet` | `anthropic/claude-sonnet-4.6` | 5688 | {'PASS': 3811, 'FAIL': 1850, 'PARSE_FAIL': 27} | **14.70** |
| `gpt4o` | `openai/gpt-4o` | 5688 | {'FAIL': 1974, 'PASS': 3714} | **9.37** |
| `deepseek_chat` | `deepseek/deepseek-chat` | 5688 | {'FAIL': 1758, 'PASS': 3930} | **1.07** |
| **total** | | | | **25.14** |

## v3 in-scope (exclude non-dose; hold out correct_suspect) — closed / grounded / all

Miss = PASS on unit+basis errors; false-reject = FAIL on v3 correct.

### Condition: `closed`

| model | miss dose-focused | miss RAGAS | FR dose-focused | FR RAGAS |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | 0.6 (2/345; 0.2–2.1) | 1.7 (6/346; 0.8–3.7) | 4.2 (28/665; 2.9–6.0) | 22.0 (147/667; 19.1–25.3) |
| `openai/gpt-4o` | 2.3 (8/347; 1.2–4.5) | 2.3 (8/347; 1.2–4.5) | 7.8 (52/667; 6.0–10.1) | 23.1 (154/667; 20.1–26.4) |
| `deepseek/deepseek-chat` | 2.6 (9/347; 1.4–4.9) | 4.0 (14/347; 2.4–6.7) | 4.2 (28/667; 2.9–6.0) | 22.2 (148/667; 19.2–25.5) |

### Condition: `grounded`

| model | miss dose-focused | miss RAGAS | FR dose-focused | FR RAGAS |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | — (0) | — (0) | 0.5 (11/2113; 0.3–0.9) | 10.4 (219/2113; 9.1–11.7) |
| `openai/gpt-4o` | — (0) | — (0) | 3.8 (80/2113; 3.1–4.7) | 18.4 (388/2113; 16.8–20.1) |
| `deepseek/deepseek-chat` | — (0) | — (0) | 1.0 (22/2113; 0.7–1.6) | 15.7 (331/2113; 14.2–17.3) |

### Condition: `all`

| model | miss dose-focused | miss RAGAS | FR dose-focused | FR RAGAS |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | 0.6 (2/345; 0.2–2.1) | 1.7 (6/346; 0.8–3.7) | 1.4 (39/2778; 1.0–1.9) | 13.2 (366/2780; 12.0–14.5) |
| `openai/gpt-4o` | 2.3 (8/347; 1.2–4.5) | 2.3 (8/347; 1.2–4.5) | 4.7 (132/2780; 4.0–5.6) | 19.5 (542/2780; 18.1–21.0) |
| `deepseek/deepseek-chat` | 2.6 (9/347; 1.4–4.9) | 4.0 (14/347; 2.4–6.7) | 1.8 (50/2780; 1.4–2.4) | 17.2 (479/2780; 15.9–18.7) |

## Full 5,688 continuity (class_v2 error / correct; includes non-dose & correct_suspect-as-correct)

### Condition: `closed` (full5688)

| model | miss dose | miss RAGAS | FR dose | FR RAGAS |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | 0.7 (3/423; 0.2–2.1) | 2.1 (9/424; 1.1–4.0) | 13.8 (138/998; 11.8–16.1) | 31.4 (315/1002; 28.6–34.4) |
| `openai/gpt-4o` | 2.6 (11/425; 1.5–4.6) | 3.5 (15/425; 2.2–5.7) | 15.4 (154/1002; 13.3–17.7) | 31.4 (315/1002; 28.6–34.4) |
| `deepseek/deepseek-chat` | 2.6 (11/425; 1.5–4.6) | 4.9 (21/425; 3.3–7.4) | 10.4 (104/1002; 8.6–12.4) | 30.4 (305/1002; 27.7–33.4) |

### Condition: `grounded` (full5688)

| model | miss dose | miss RAGAS | FR dose | FR RAGAS |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | 0.0 (0/1; 0.0–79.3) | 0.0 (0/1; 0.0–79.3) | 0.7 (18/2674; 0.4–1.1) | 14.1 (377/2677; 12.8–15.5) |
| `openai/gpt-4o` | 0.0 (0/1; 0.0–79.3) | 0.0 (0/1; 0.0–79.3) | 5.0 (134/2677; 4.2–5.9) | 21.6 (579/2677; 20.1–23.2) |
| `deepseek/deepseek-chat` | 0.0 (0/1; 0.0–79.3) | 0.0 (0/1; 0.0–79.3) | 1.3 (34/2677; 0.9–1.8) | 18.7 (500/2677; 17.2–20.2) |

### Condition: `all` (full5688)

| model | miss dose | miss RAGAS | FR dose | FR RAGAS |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | 0.7 (3/424; 0.2–2.1) | 2.1 (9/425; 1.1–4.0) | 4.2 (156/3672; 3.6–4.9) | 18.8 (692/3679; 17.6–20.1) |
| `openai/gpt-4o` | 2.6 (11/426; 1.4–4.6) | 3.5 (15/426; 2.1–5.7) | 7.8 (288/3679; 7.0–8.7) | 24.3 (894/3679; 22.9–25.7) |
| `deepseek/deepseek-chat` | 2.6 (11/426; 1.4–4.6) | 4.9 (21/426; 3.2–7.4) | 3.8 (138/3679; 3.2–4.4) | 21.9 (805/3679; 20.6–23.2) |

## Headline (v3 closed)

- `anthropic/claude-sonnet-4.6`: FR 22.0% → 4.2% (Δ -17.8 pp); miss 1.7% → 0.6%
- `openai/gpt-4o`: FR 23.1% → 7.8% (Δ -15.3 pp); miss 2.3% → 2.3%
- `deepseek/deepseek-chat`: FR 22.2% → 4.2% (Δ -18.0 pp); miss 4.0% → 2.6%

## Files

- `claude_sonnet.jsonl`, `gpt4o.jsonl`, `deepseek_chat.jsonl`
- `rates_dose_focused.csv`, `report_dose_focused.json`
- `SMOKE.md`, `smoke_decision.json`

RAGAS paths under `frontier_judges/` were not modified.
