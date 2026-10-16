# RD2 frontier judges — aggregate report

**Exploratory / supplementary** (not pre-registered). HTML RAGAS-NLI on the RD2 scored set (5,688 answers).

## Run metadata

| field | value |
|---|---|
| Slurm job | `68548` (COMPLETED) |
| Start–end (cluster local) | `2026-10-16T12:47:03` → `2026-10-16T18:07:52` |
| Elapsed | 05:20:49 |
| Run date (ICT) | **2026-10-16** |
| Window (ICT) | 2026-10-16 ~12:47–18:08 ICT (Slurm job 68548 on node004) |
| Total API spend | **$31.32** |

### Exact model versions (OpenRouter `api_model` as returned)

| judge | display | `api_model` (exact) | providers seen | cost |
|---|---|---|---|---|
| `v6_ragas_html_claude` | Claude Sonnet (HTML RAGAS) | `anthropic/claude-sonnet-4.6` | Anthropic×5688 | $19.22 |
| `v6_ragas_html_gpt4o` | GPT-4o (HTML RAGAS) | `openai/gpt-4o` | OpenAI×5688 | $10.95 |
| `v6_ragas_html_deepseek` | DeepSeek Chat (HTML RAGAS) | `deepseek/deepseek-chat` | DeepInfra×3698, StreamLake×1990 | $1.14 |

## Format errors (`PARSE_FAIL`) — not counted as FAIL

These rows had an unparseable judge output. They are **reported here** and **excluded** from all PASS-rate
denominators below (they are not treated as “trượt” / FAIL).

| judge | PARSE_FAIL | / rows | instance_id(s) |
|---|---:|---:|---|
| Claude Sonnet (HTML RAGAS) (`v6_ragas_html_claude`) | **2** | 5688 | `RD2_somatropin_0__medgemma_27b__closed`, `RD2_procainamide_0__qwen25_14b__closed` |
| GPT-4o (HTML RAGAS) (`v6_ragas_html_gpt4o`) | **0** | 5688 | — |
| DeepSeek Chat (HTML RAGAS) (`v6_ragas_html_deepseek`) | **0** | 5688 | — |

## PASS rates (PARSE_FAIL excluded from denominator)

Reference: **error** = `unit_error` + `basis_error`; **correct** = `correct`.
Label sets **v1** (pre-registered extractor) and **v2** (amendment-1 m² pre-pass), split by **closed** / **grounded**.

Cells: PASS%% (PASS / (PASS+FAIL); Wilson 95%% CI). PF = PARSE_FAIL count inside that reference set (excluded from n).

### Condition: `closed`

| judge | model | PASS on errors v1 | PASS on errors v2 | PASS on correct v1 | PASS on correct v2 |
|---|---|---|---|---|---|
| Claude Sonnet (HTML RAGAS) | `anthropic/claude-sonnet-4.6` | 3.1 (14/446; Wilson 1.9–5.2) · PF=1 | 2.1 (9/424; Wilson 1.1–4.0) · PF=1 | 68.7 (684/996; Wilson 65.7–71.5) | 68.6 (687/1002; Wilson 65.6–71.4) |
| GPT-4o (HTML RAGAS) | `openai/gpt-4o` | 3.8 (17/447; Wilson 2.4–6.0) | 3.5 (15/425; Wilson 2.2–5.7) | 68.9 (686/996; Wilson 65.9–71.7) | 68.6 (687/1002; Wilson 65.6–71.4) |
| DeepSeek Chat (HTML RAGAS) | `deepseek/deepseek-chat` | 5.1 (23/447; Wilson 3.5–7.6) | 4.9 (21/425; Wilson 3.3–7.4) | 69.9 (696/996; Wilson 67.0–72.6) | 69.6 (697/1002; Wilson 66.6–72.3) |

### Condition: `grounded`

| judge | model | PASS on errors v1 | PASS on errors v2 | PASS on correct v1 | PASS on correct v2 |
|---|---|---|---|---|---|
| Claude Sonnet (HTML RAGAS) | `anthropic/claude-sonnet-4.6` | 75.0 (9/12; Wilson 46.8–91.1) | 0.0 (0/1; Wilson 0.0–79.3) | 86.0 (2286/2658; Wilson 84.6–87.3) | 85.9 (2300/2677; Wilson 84.5–87.2) |
| GPT-4o (HTML RAGAS) | `openai/gpt-4o` | 58.3 (7/12; Wilson 32.0–80.7) | 0.0 (0/1; Wilson 0.0–79.3) | 78.6 (2088/2658; Wilson 77.0–80.1) | 78.4 (2098/2677; Wilson 76.8–79.9) |
| DeepSeek Chat (HTML RAGAS) | `deepseek/deepseek-chat` | 66.7 (8/12; Wilson 39.1–86.2) | 0.0 (0/1; Wilson 0.0–79.3) | 81.5 (2167/2658; Wilson 80.0–83.0) | 81.3 (2177/2677; Wilson 79.8–82.8) |

### Condition: `all`

| judge | model | PASS on errors v1 | PASS on errors v2 | PASS on correct v1 | PASS on correct v2 |
|---|---|---|---|---|---|
| Claude Sonnet (HTML RAGAS) | `anthropic/claude-sonnet-4.6` | 5.0 (23/458; Wilson 3.4–7.4) · PF=1 | 2.1 (9/425; Wilson 1.1–4.0) · PF=1 | 81.3 (2970/3654; Wilson 80.0–82.5) | 81.2 (2987/3679; Wilson 79.9–82.4) |
| GPT-4o (HTML RAGAS) | `openai/gpt-4o` | 5.2 (24/459; Wilson 3.5–7.7) | 3.5 (15/426; Wilson 2.1–5.7) | 75.9 (2774/3654; Wilson 74.5–77.3) | 75.7 (2785/3679; Wilson 74.3–77.1) |
| DeepSeek Chat (HTML RAGAS) | `deepseek/deepseek-chat` | 6.8 (31/459; Wilson 4.8–9.4) | 4.9 (21/426; Wilson 3.2–7.4) | 78.4 (2863/3654; Wilson 77.0–79.7) | 78.1 (2874/3679; Wilson 76.8–79.4) |

## Files

- `results/journal5/rd2/frontier_judges/rates_frontier_judges.csv`
- `results/journal5/rd2/frontier_judges/report_frontier_judges.json`
- Per-judge jsonl under `results/journal5/rd2/frontier_judges/`

## Caveats

- Exploratory HTML prompt (not the frozen JSON RAGAS used in the main RD2 table).
- DeepSeek had no provider pin (OpenRouter routed DeepInfra / StreamLake); model id is still `deepseek/deepseek-chat`.
- Gemini 2.5 Pro was planned then dropped (OpenRouter Google ToS 403).
