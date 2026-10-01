# Journal 4 — frontier API LLM judges on real-dose answers (subset `flagged47`, 47 rows)

Generated 2026-10-01 23:45 UTC+7 by `scripts/journal4/frontier_judges_rd.py`. Prompt: ragas_nli@298b682 via j3_ragas_prompt.nli_prompt; raw single user message, no system prompt (API path = v5/v6) (identical to `src/verifiers/ragas_nli_prompt.py`: True). STRICT verdict = the paper parser (`v4_ragas_nli.parse_verdict`, vendored in `scripts/journal3/j3_ragas_prompt.py`); LENIENT = strict, else first regex match `"verdict"\s*:\s*"?([01])\b` in the raw output (recomputed from `raw_output` for every judge, incl. the existing ones).

RD labels are AUTOMATIC (`rd_extract.py`); precheck-true = AI pre-check `true_unit_error` (n=12, AI-made, not human). Metrics = `scripts/journal3/j3_report.py` section 1 (imported `rd_block`): group cells = % of the group with the wanted verdict among scored rows (PASS on correct, FAIL on errors), slips/1000 = error answers that PASS per 1000 scored, drug-clustered bootstrap 95% CI. Reference rows are recomputed on exactly the same rows.

## Runs

| model | provider | api model | effort | temperature sent | max out | rows | parse fail strict | parse fail lenient | truncated | mean in / out (reasoning) tokens | cost subset USD | USD/row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-5.5 | openrouter | anthropic/claude-opus-5.5 | low | 0.0 | 2048 | 47 | 0 | 0 | 0 | 1576 / 208 (5) | 0.4920 | 0.01047 |
| google/gemini-3.1-pro-preview | openrouter | google/gemini-3.1-pro-preview | low | 0.0 | 2048 | 47 | 0 | 0 | 0 | 1067 / 598 (467) | 0.4375 | 0.00931 |

## RD metrics — STRICT (paper parser; comparable to all existing rows)

Coverage = scored (PASS/FAIL) / subset rows; PARSE_FAIL and unscored rows are excluded from the cells (as in j3_report).

| checker | scored | correct PASS | any err FAIL | unit-type FAIL | same-numeral FAIL | value FAIL | precheck-true FAIL | slips/1000 any | slips/1000 unit-type | slips/1000 precheck-true |
|---|---|---|---|---|---|---|---|---|---|---|
| **anthropic/claude-opus-5.5** | 47/47 | NA | 78.7 [66.0, 90.2] | 78.7 [66.0, 90.2] | 53.3 [25.0, 84.6] | NA | 100.0 [100.0, 100.0] | 212.8 [97.5, 340.4] | 212.8 [97.5, 340.4] | 0.0 [0.0, 0.0] |
| **google/gemini-3.1-pro-preview** | 47/47 | NA | 78.7 [66.0, 90.2] | 78.7 [66.0, 90.2] | 53.3 [25.0, 84.6] | NA | 100.0 [100.0, 100.0] | 212.8 [97.5, 340.4] | 212.8 [97.5, 340.4] | 0.0 [0.0, 0.0] |
| ref: Llama-3.3-70B RAGAS (paper) | 47/47 | NA | 72.3 [58.9, 86.0] | 72.3 [58.9, 86.0] | 46.7 [18.8, 76.9] | NA | 91.7 [71.4, 100.0] | 276.6 [140.0, 410.7] | 276.6 [140.0, 410.7] | 21.3 [0.0, 75.0] |
| ref: Mistral-Small-24B MedScore (paper) | 47/47 | NA | 70.2 [54.5, 85.7] | 70.2 [54.5, 85.7] | 40.0 [15.0, 75.0] | NA | 91.7 [72.7, 100.0] | 297.9 [142.9, 454.5] | 297.9 [142.9, 454.5] | 21.3 [0.0, 70.2] |
| ref: MiniCheck-DeBERTa (paper) | 47/47 | NA | 85.1 [72.7, 94.7] | 85.1 [72.7, 94.7] | 66.7 [40.0, 91.7] | NA | 91.7 [72.7, 100.0] | 148.9 [52.6, 272.7] | 148.9 [52.6, 272.7] | 21.3 [0.0, 70.2] |
| ref: MiniCheck-Flan-T5-Large (paper) | 47/47 | NA | 72.3 [57.1, 87.2] | 72.3 [57.1, 87.2] | 40.0 [15.0, 75.0] | NA | 83.3 [58.3, 100.0] | 276.6 [128.2, 428.6] | 276.6 [128.2, 428.6] | 42.6 [0.0, 111.1] |
| ref: AlignScore-large (paper) | 47/47 | NA | 68.1 [52.9, 83.0] | 68.1 [52.9, 83.0] | 20.0 [0.0, 50.0] | NA | 75.0 [44.4, 100.0] | 319.1 [170.2, 470.6] | 319.1 [170.2, 470.6] | 63.8 [0.0, 152.2] |
| ref: judge llama31_8b (chain 3, vLLM) | 44/47 | NA | 59.1 [43.7, 75.0] | 59.1 [43.7, 75.0] | 20.0 [0.0, 50.0] | NA | 72.7 [40.0, 100.0] | 409.1 [250.0, 562.5] | 409.1 [250.0, 562.5] | 68.2 [0.0, 159.2] |
| ref: judge medgemma_4b (chain 3, vLLM) | 47/47 | NA | 46.8 [30.0, 64.4] | 46.8 [30.0, 64.4] | 20.0 [0.0, 50.0] | NA | 58.3 [30.0, 84.6] | 531.9 [355.6, 700.1] | 531.9 [355.6, 700.1] | 106.4 [25.0, 205.2] |
| ref: judge qwen25_0p5b (chain 3, vLLM) | 43/47 | NA | 4.7 [0.0, 11.9] | 4.7 [0.0, 11.9] | 7.1 [0.0, 21.4] | NA | 0.0 [0.0, 0.0] | 953.5 [881.0, 1000.0] | 953.5 [881.0, 1000.0] | 279.1 [153.8, 432.4] |
| ref: judge qwen25_14b (chain 3, vLLM) | 45/47 | NA | 73.3 [60.4, 86.7] | 73.3 [60.4, 86.7] | 46.7 [21.4, 75.0] | NA | 83.3 [57.1, 100.0] | 266.7 [133.3, 396.3] | 266.7 [133.3, 396.3] | 44.4 [0.0, 120.0] |
| ref: judge qwen25_1p5b (chain 3, vLLM) | 29/47 | NA | 65.5 [41.2, 87.5] | 65.5 [41.2, 87.5] | 44.4 [0.0, 100.0] | NA | 66.7 [25.0, 100.0] | 344.8 [124.9, 588.2] | 344.8 [124.9, 588.2] | 69.0 [0.0, 190.5] |
| ref: judge qwen25_3b (chain 3, vLLM) | 30/47 | NA | 90.0 [77.8, 100.0] | 90.0 [77.8, 100.0] | 88.9 [57.1, 100.0] | NA | 100.0 [100.0, 100.0] | 100.0 [0.0, 222.2] | 100.0 [0.0, 222.2] | 0.0 [0.0, 0.0] |
| ref: judge qwen25_7b (chain 3, vLLM) | 38/47 | NA | 65.8 [48.9, 81.3] | 65.8 [48.9, 81.3] | 35.7 [7.7, 62.5] | NA | 72.7 [42.9, 100.0] | 342.1 [187.4, 511.1] | 342.1 [187.4, 511.1] | 78.9 [0.0, 181.9] |

## RD metrics — LENIENT (regex fallback)

Coverage = scored (PASS/FAIL) / subset rows; PARSE_FAIL and unscored rows are excluded from the cells (as in j3_report).

| checker | scored | correct PASS | any err FAIL | unit-type FAIL | same-numeral FAIL | value FAIL | precheck-true FAIL | slips/1000 any | slips/1000 unit-type | slips/1000 precheck-true |
|---|---|---|---|---|---|---|---|---|---|---|
| **anthropic/claude-opus-5.5** | 47/47 | NA | 78.7 [66.0, 90.2] | 78.7 [66.0, 90.2] | 53.3 [25.0, 84.6] | NA | 100.0 [100.0, 100.0] | 212.8 [97.5, 340.4] | 212.8 [97.5, 340.4] | 0.0 [0.0, 0.0] |
| **google/gemini-3.1-pro-preview** | 47/47 | NA | 78.7 [66.0, 90.2] | 78.7 [66.0, 90.2] | 53.3 [25.0, 84.6] | NA | 100.0 [100.0, 100.0] | 212.8 [97.5, 340.4] | 212.8 [97.5, 340.4] | 0.0 [0.0, 0.0] |
| ref: Llama-3.3-70B RAGAS (paper) | 47/47 | NA | 72.3 [58.9, 86.0] | 72.3 [58.9, 86.0] | 46.7 [18.8, 76.9] | NA | 91.7 [71.4, 100.0] | 276.6 [140.0, 410.7] | 276.6 [140.0, 410.7] | 21.3 [0.0, 75.0] |
| ref: Mistral-Small-24B MedScore (paper) | 47/47 | NA | 70.2 [54.5, 85.7] | 70.2 [54.5, 85.7] | 40.0 [15.0, 75.0] | NA | 91.7 [72.7, 100.0] | 297.9 [142.9, 454.5] | 297.9 [142.9, 454.5] | 21.3 [0.0, 70.2] |
| ref: MiniCheck-DeBERTa (paper) | 47/47 | NA | 85.1 [72.7, 94.7] | 85.1 [72.7, 94.7] | 66.7 [40.0, 91.7] | NA | 91.7 [72.7, 100.0] | 148.9 [52.6, 272.7] | 148.9 [52.6, 272.7] | 21.3 [0.0, 70.2] |
| ref: MiniCheck-Flan-T5-Large (paper) | 47/47 | NA | 72.3 [57.1, 87.2] | 72.3 [57.1, 87.2] | 40.0 [15.0, 75.0] | NA | 83.3 [58.3, 100.0] | 276.6 [128.2, 428.6] | 276.6 [128.2, 428.6] | 42.6 [0.0, 111.1] |
| ref: AlignScore-large (paper) | 47/47 | NA | 68.1 [52.9, 83.0] | 68.1 [52.9, 83.0] | 20.0 [0.0, 50.0] | NA | 75.0 [44.4, 100.0] | 319.1 [170.2, 470.6] | 319.1 [170.2, 470.6] | 63.8 [0.0, 152.2] |
| ref: judge llama31_8b (chain 3, vLLM) | 47/47 | NA | 61.7 [46.0, 77.1] | 61.7 [46.0, 77.1] | 20.0 [0.0, 50.0] | NA | 75.0 [44.4, 100.0] | 383.0 [229.1, 540.0] | 383.0 [229.1, 540.0] | 63.8 [0.0, 152.2] |
| ref: judge medgemma_4b (chain 3, vLLM) | 47/47 | NA | 46.8 [30.0, 64.4] | 46.8 [30.0, 64.4] | 20.0 [0.0, 50.0] | NA | 58.3 [30.0, 84.6] | 531.9 [355.6, 700.1] | 531.9 [355.6, 700.1] | 106.4 [25.0, 205.2] |
| ref: judge qwen25_0p5b (chain 3, vLLM) | 46/47 | NA | 4.3 [0.0, 11.4] | 4.3 [0.0, 11.4] | 7.1 [0.0, 21.4] | NA | 0.0 [0.0, 0.0] | 956.5 [886.4, 1000.0] | 956.5 [886.4, 1000.0] | 260.9 [142.9, 405.5] |
| ref: judge qwen25_14b (chain 3, vLLM) | 47/47 | NA | 74.5 [61.2, 87.2] | 74.5 [61.2, 87.2] | 46.7 [21.4, 75.0] | NA | 83.3 [57.1, 100.0] | 255.3 [127.7, 387.8] | 255.3 [127.7, 387.8] | 42.6 [0.0, 114.3] |
| ref: judge qwen25_1p5b (chain 3, vLLM) | 40/47 | NA | 65.0 [45.7, 83.3] | 65.0 [45.7, 83.3] | 50.0 [16.7, 88.9] | NA | 70.0 [33.3, 100.0] | 350.0 [166.7, 542.9] | 350.0 [166.7, 542.9] | 75.0 [0.0, 166.7] |
| ref: judge qwen25_3b (chain 3, vLLM) | 43/47 | NA | 88.4 [76.7, 97.6] | 88.4 [76.7, 97.6] | 78.6 [50.0, 100.0] | NA | 100.0 [100.0, 100.0] | 116.3 [23.8, 232.6] | 116.3 [23.8, 232.6] | 0.0 [0.0, 0.0] |
| ref: judge qwen25_7b (chain 3, vLLM) | 43/47 | NA | 67.4 [50.0, 82.6] | 67.4 [50.0, 82.6] | 33.3 [7.1, 60.9] | NA | 72.7 [42.9, 100.0] | 325.6 [173.8, 500.0] | 325.6 [173.8, 500.0] | 69.8 [0.0, 162.9] |

## The 12 AI-precheck true unit errors (per case)

Wanted verdict = FAIL. Existing columns from `qc/ai_precheck_real_dose_unit_errors.csv` (P = PASS = error slipped through): MC-R=minicheck_roberta, MC-D=minicheck_deberta, AS-b=alignscore_base, MC-T5=minicheck_flant5, AS-L=alignscore_large, L70B=ragas_llama70b, MedS=medscore_mistral24b. Chain-3 local judges: strict verdicts, P/F/? (? = parse fail) in the order llama31_8b, medgemma_4b, qwen25_0p5b, qwen25_14b, qwen25_1p5b, qwen25_3b, qwen25_7b. Frontier: strict verdict (lenient in brackets if different; – = not scored).

| check | drug | mode/gen | mechanism | label dose | answer dose | MC-R | MC-D | AS-b | MC-T5 | AS-L | L70B | MedS | chain-3 judges | anthropic/claude-opus-5.5 | google/gemini-3.1-pro-preview |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RDQ0050 | ivermectin | closed/gpt4o_mini | dropped_basis | 150 mcg/kg | 15 mg | F | F | F | F | F | F | F | FFPF?F? | FAIL | FAIL |
| RDQ0109 | glyburide | closed/gpt4o_mini | unit_kind | 20 units | 20 mg | F | F | F | F | F | F | F | FFPFFFF | FAIL | FAIL |
| RDQ0126 | buspirone | closed/gpt4o_mini | dropped_basis | 1 mg per kg | 1 mg | P | F | F | P | F | F | F | FFPFFFF | FAIL | FAIL |
| RDQ0137 | ethambutol | closed/gemma3_27b | lb_vs_kg | 15 mg/kg | 15 mg | F | F | P | F | P | P | F | PPPPPFP | FAIL | FAIL |
| RDQ0145 | losartan | grounded/gemma3_27b | dropped_basis | 0.7 mg per kg | 0.7 mg | P | P | P | F | P | F | P | PPPPP?P | FAIL | FAIL |
| RDQ0165 | filgrastim | closed/gemma3_27b | dropped_basis | 5 mcg/kg/day | 300 mcg | F | F | F | F | F | F | F | FFPF??F | FAIL | FAIL |
| RDQ0210 | tacrolimus | closed/gemma3_27b | dropped_basis | 0.2 mg/kg/day | 0.2 mg | P | F | P | F | P | F | F | PPPF??P | FAIL | FAIL |
| RDQ0222 | cyclophosphamide | closed/gpt4o_mini | dropped_basis | 10 mg per kg | 500 mg | F | F | F | F | F | F | F | ?FPF?FF | FAIL | FAIL |
| RDQ0228 | clonidine | closed/gpt4o_mini | time_basis | 0.1 mg/day | 0.1 mg/week | F | F | F | F | F | F | F | FFPF?FF | FAIL | FAIL |
| RDQ0247 | ivermectin | closed/gemma3_27b | dropped_basis | 150 mcg/kg | 15 mg | F | F | F | F | F | F | F | FPPFFFF | FAIL | FAIL |
| RDQ0258 | epinephrine | closed/gemma3_27b | dropped_basis | 0.05 mcg/kg/min | 1-4 micrograms per minute | F | F | F | P | F | F | F | FPPFF?F | FAIL | FAIL |
| RDQ0263 | ceftriaxone | closed/gemma3_27b | dropped_basis | 50 to 75 mg/kg | 500 mg | F | F | F | F | F | F | F | FFPF??F | FAIL | FAIL |

## Caveats

- Frontier models are reasoning models: temperature 0 is sent where accepted; if the API rejects it the run continues with the provider default (column 'temperature sent'). Hidden reasoning/thinking tokens are billed as output and count against the max-output cap; 'truncated' = cap hit (verdict usually PARSE_FAIL).
- Model IDs are aliases/snapshots as served on the run date (`api model` column); provider-side changes can alter results.
- RD error labels are automatic; the 12 precheck-true cases are AI-checked, not human-verified.
