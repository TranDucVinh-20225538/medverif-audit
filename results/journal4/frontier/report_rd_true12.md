# Journal 4 — frontier API LLM judges on real-dose answers (subset `true12`, 12 rows)

Generated 2026-10-02 09:37 UTC+7 by `scripts/journal4/frontier_judges_rd.py`. Prompt: ragas_nli@298b682 via j3_ragas_prompt.nli_prompt; raw single user message, no system prompt (API path = v5/v6) (identical to `src/verifiers/ragas_nli_prompt.py`: True). STRICT verdict = the paper parser (`v4_ragas_nli.parse_verdict`, vendored in `scripts/journal3/j3_ragas_prompt.py`); LENIENT = strict, else first regex match `"verdict"\s*:\s*"?([01])\b` in the raw output (recomputed from `raw_output` for every judge, incl. the existing ones).

RD labels are AUTOMATIC (`rd_extract.py`); precheck-true = AI pre-check `true_unit_error` (n=12, AI-made, not human). Metrics = `scripts/journal3/j3_report.py` section 1 (imported `rd_block`): group cells = % of the group with the wanted verdict among scored rows (PASS on correct, FAIL on errors), slips/1000 = error answers that PASS per 1000 scored, drug-clustered bootstrap 95% CI. Reference rows are recomputed on exactly the same rows.

## Runs

| model | provider | api model | effort | temperature sent | max out | rows | parse fail strict | parse fail lenient | truncated | mean in / out (reasoning) tokens | cost subset USD | USD/row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-5.5 | openrouter | anthropic/claude-opus-5.5 | low | 0.0 | 2048 | 12 | 0 | 0 | 0 | 1564 / 216 (n/a) | 0.1269 | 0.01058 |
| google/gemini-3.1-pro-preview | openrouter | google/gemini-3.1-pro-preview | low | 0.0 | 2048 | 12 | 0 | 0 | 0 | 1056 / 595 (464) | 0.1111 | 0.00926 |

## RD metrics — STRICT (paper parser; comparable to all existing rows)

Coverage = scored (PASS/FAIL) / subset rows; PARSE_FAIL and unscored rows are excluded from the cells (as in j3_report).

| checker | scored | correct PASS | any err FAIL | unit-type FAIL | same-numeral FAIL | value FAIL | precheck-true FAIL | slips/1000 any | slips/1000 unit-type | slips/1000 precheck-true |
|---|---|---|---|---|---|---|---|---|---|---|
| **anthropic/claude-opus-5.5** | 12/12 | NA | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | NA | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| **google/gemini-3.1-pro-preview** | 12/12 | NA | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | NA | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| ref: Llama-3.3-70B RAGAS (paper) | 12/12 | NA | 91.7 [72.7, 100.0] | 91.7 [72.7, 100.0] | 83.3 [50.0, 100.0] | NA | 91.7 [72.7, 100.0] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] |
| ref: Mistral-Small-24B MedScore (paper) | 12/12 | NA | 91.7 [72.7, 100.0] | 91.7 [72.7, 100.0] | 83.3 [50.0, 100.0] | NA | 91.7 [72.7, 100.0] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] |
| ref: MiniCheck-DeBERTa (paper) | 12/12 | NA | 91.7 [72.7, 100.0] | 91.7 [72.7, 100.0] | 83.3 [50.0, 100.0] | NA | 91.7 [72.7, 100.0] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] |
| ref: MiniCheck-Flan-T5-Large (paper) | 12/12 | NA | 83.3 [58.3, 100.0] | 83.3 [58.3, 100.0] | 83.3 [50.0, 100.0] | NA | 83.3 [58.3, 100.0] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] |
| ref: AlignScore-large (paper) | 12/12 | NA | 75.0 [45.5, 100.0] | 75.0 [45.5, 100.0] | 50.0 [0.0, 100.0] | NA | 75.0 [45.5, 100.0] | 250.0 [0.0, 545.5] | 250.0 [0.0, 545.5] | 250.0 [0.0, 545.5] |
| ref: judge baichuan_m2_32b (chain 3, vLLM) | 11/12 | NA | 81.8 [54.5, 100.0] | 81.8 [54.5, 100.0] | 60.0 [11.6, 100.0] | NA | 81.8 [54.5, 100.0] | 181.8 [0.0, 454.5] | 181.8 [0.0, 454.5] | 181.8 [0.0, 454.5] |
| ref: judge llama31_8b (chain 3, vLLM) | 11/12 | NA | 72.7 [44.4, 100.0] | 72.7 [44.4, 100.0] | 50.0 [0.0, 100.0] | NA | 72.7 [44.4, 100.0] | 272.7 [0.0, 555.6] | 272.7 [0.0, 555.6] | 272.7 [0.0, 555.6] |
| ref: judge medgemma_27b (chain 3, vLLM) | 12/12 | NA | 75.0 [53.3, 91.7] | 75.0 [53.3, 91.7] | 66.7 [25.0, 100.0] | NA | 75.0 [53.3, 91.7] | 250.0 [83.3, 467.5] | 250.0 [83.3, 467.5] | 250.0 [83.3, 467.5] |
| ref: judge medgemma_4b (chain 3, vLLM) | 12/12 | NA | 58.3 [33.3, 81.8] | 58.3 [33.3, 81.8] | 50.0 [0.0, 100.0] | NA | 58.3 [33.3, 81.8] | 416.7 [181.8, 666.7] | 416.7 [181.8, 666.7] | 416.7 [181.8, 666.7] |
| ref: judge qwen25_0p5b (chain 3, vLLM) | 12/12 | NA | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | NA | 0.0 [0.0, 0.0] | 1000.0 [1000.0, 1000.0] | 1000.0 [1000.0, 1000.0] | 1000.0 [1000.0, 1000.0] |
| ref: judge qwen25_14b (chain 3, vLLM) | 12/12 | NA | 83.3 [58.3, 100.0] | 83.3 [58.3, 100.0] | 66.7 [25.0, 100.0] | NA | 83.3 [58.3, 100.0] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] |
| ref: judge qwen25_1p5b (chain 3, vLLM) | 6/12 | NA | 66.7 [25.0, 100.0] | 66.7 [25.0, 100.0] | 50.0 [0.0, 100.0] | NA | 66.7 [25.0, 100.0] | 333.3 [0.0, 750.0] | 333.3 [0.0, 750.0] | 333.3 [0.0, 750.0] |
| ref: judge qwen25_3b (chain 3, vLLM) | 7/12 | NA | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | NA | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| ref: judge qwen25_7b (chain 3, vLLM) | 11/12 | NA | 72.7 [45.5, 100.0] | 72.7 [45.5, 100.0] | 50.0 [0.0, 100.0] | NA | 72.7 [45.5, 100.0] | 272.7 [0.0, 545.5] | 272.7 [0.0, 545.5] | 272.7 [0.0, 545.5] |

## RD metrics — LENIENT (regex fallback)

Coverage = scored (PASS/FAIL) / subset rows; PARSE_FAIL and unscored rows are excluded from the cells (as in j3_report).

| checker | scored | correct PASS | any err FAIL | unit-type FAIL | same-numeral FAIL | value FAIL | precheck-true FAIL | slips/1000 any | slips/1000 unit-type | slips/1000 precheck-true |
|---|---|---|---|---|---|---|---|---|---|---|
| **anthropic/claude-opus-5.5** | 12/12 | NA | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | NA | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| **google/gemini-3.1-pro-preview** | 12/12 | NA | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | NA | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| ref: Llama-3.3-70B RAGAS (paper) | 12/12 | NA | 91.7 [72.7, 100.0] | 91.7 [72.7, 100.0] | 83.3 [50.0, 100.0] | NA | 91.7 [72.7, 100.0] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] |
| ref: Mistral-Small-24B MedScore (paper) | 12/12 | NA | 91.7 [72.7, 100.0] | 91.7 [72.7, 100.0] | 83.3 [50.0, 100.0] | NA | 91.7 [72.7, 100.0] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] |
| ref: MiniCheck-DeBERTa (paper) | 12/12 | NA | 91.7 [72.7, 100.0] | 91.7 [72.7, 100.0] | 83.3 [50.0, 100.0] | NA | 91.7 [72.7, 100.0] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] | 83.3 [0.0, 272.7] |
| ref: MiniCheck-Flan-T5-Large (paper) | 12/12 | NA | 83.3 [58.3, 100.0] | 83.3 [58.3, 100.0] | 83.3 [50.0, 100.0] | NA | 83.3 [58.3, 100.0] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] |
| ref: AlignScore-large (paper) | 12/12 | NA | 75.0 [45.5, 100.0] | 75.0 [45.5, 100.0] | 50.0 [0.0, 100.0] | NA | 75.0 [45.5, 100.0] | 250.0 [0.0, 545.5] | 250.0 [0.0, 545.5] | 250.0 [0.0, 545.5] |
| ref: judge baichuan_m2_32b (chain 3, vLLM) | 12/12 | NA | 83.3 [58.3, 100.0] | 83.3 [58.3, 100.0] | 66.7 [25.0, 100.0] | NA | 83.3 [58.3, 100.0] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] |
| ref: judge llama31_8b (chain 3, vLLM) | 12/12 | NA | 75.0 [45.5, 100.0] | 75.0 [45.5, 100.0] | 50.0 [0.0, 100.0] | NA | 75.0 [45.5, 100.0] | 250.0 [0.0, 545.5] | 250.0 [0.0, 545.5] | 250.0 [0.0, 545.5] |
| ref: judge medgemma_27b (chain 3, vLLM) | 12/12 | NA | 75.0 [53.3, 91.7] | 75.0 [53.3, 91.7] | 66.7 [25.0, 100.0] | NA | 75.0 [53.3, 91.7] | 250.0 [83.3, 467.5] | 250.0 [83.3, 467.5] | 250.0 [83.3, 467.5] |
| ref: judge medgemma_4b (chain 3, vLLM) | 12/12 | NA | 58.3 [33.3, 81.8] | 58.3 [33.3, 81.8] | 50.0 [0.0, 100.0] | NA | 58.3 [33.3, 81.8] | 416.7 [181.8, 666.7] | 416.7 [181.8, 666.7] | 416.7 [181.8, 666.7] |
| ref: judge qwen25_0p5b (chain 3, vLLM) | 12/12 | NA | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | NA | 0.0 [0.0, 0.0] | 1000.0 [1000.0, 1000.0] | 1000.0 [1000.0, 1000.0] | 1000.0 [1000.0, 1000.0] |
| ref: judge qwen25_14b (chain 3, vLLM) | 12/12 | NA | 83.3 [58.3, 100.0] | 83.3 [58.3, 100.0] | 66.7 [25.0, 100.0] | NA | 83.3 [58.3, 100.0] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] | 166.7 [0.0, 416.7] |
| ref: judge qwen25_1p5b (chain 3, vLLM) | 10/12 | NA | 70.0 [37.5, 100.0] | 70.0 [37.5, 100.0] | 60.0 [11.6, 100.0] | NA | 70.0 [37.5, 100.0] | 300.0 [0.0, 625.0] | 300.0 [0.0, 625.0] | 300.0 [0.0, 625.0] |
| ref: judge qwen25_3b (chain 3, vLLM) | 12/12 | NA | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | NA | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| ref: judge qwen25_7b (chain 3, vLLM) | 11/12 | NA | 72.7 [45.5, 100.0] | 72.7 [45.5, 100.0] | 50.0 [0.0, 100.0] | NA | 72.7 [45.5, 100.0] | 272.7 [0.0, 545.5] | 272.7 [0.0, 545.5] | 272.7 [0.0, 545.5] |

## The 12 AI-precheck true unit errors (per case)

Wanted verdict = FAIL. Existing columns from `qc/ai_precheck_real_dose_unit_errors.csv` (P = PASS = error slipped through): MC-R=minicheck_roberta, MC-D=minicheck_deberta, AS-b=alignscore_base, MC-T5=minicheck_flant5, AS-L=alignscore_large, L70B=ragas_llama70b, MedS=medscore_mistral24b. Chain-3 local judges: strict verdicts, P/F/? (? = parse fail) in the order baichuan_m2_32b, llama31_8b, medgemma_27b, medgemma_4b, qwen25_0p5b, qwen25_14b, qwen25_1p5b, qwen25_3b, qwen25_7b. Frontier: strict verdict (lenient in brackets if different; – = not scored).

| check | drug | mode/gen | mechanism | label dose | answer dose | MC-R | MC-D | AS-b | MC-T5 | AS-L | L70B | MedS | chain-3 judges | anthropic/claude-opus-5.5 | google/gemini-3.1-pro-preview |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RDQ0050 | ivermectin | closed/gpt4o_mini | dropped_basis | 150 mcg/kg | 15 mg | F | F | F | F | F | F | F | FFPFPF?F? | FAIL | FAIL |
| RDQ0109 | glyburide | closed/gpt4o_mini | unit_kind | 20 units | 20 mg | F | F | F | F | F | F | F | FFFFPFFFF | FAIL | FAIL |
| RDQ0126 | buspirone | closed/gpt4o_mini | dropped_basis | 1 mg per kg | 1 mg | P | F | F | P | F | F | F | FFFFPFFFF | FAIL | FAIL |
| RDQ0137 | ethambutol | closed/gemma3_27b | lb_vs_kg | 15 mg/kg | 15 mg | F | F | P | F | P | P | F | PPPPPPPFP | FAIL | FAIL |
| RDQ0145 | losartan | grounded/gemma3_27b | dropped_basis | 0.7 mg per kg | 0.7 mg | P | P | P | F | P | F | P | PPPPPPP?P | FAIL | FAIL |
| RDQ0165 | filgrastim | closed/gemma3_27b | dropped_basis | 5 mcg/kg/day | 300 mcg | F | F | F | F | F | F | F | FFFFPF??F | FAIL | FAIL |
| RDQ0210 | tacrolimus | closed/gemma3_27b | dropped_basis | 0.2 mg/kg/day | 0.2 mg | P | F | P | F | P | F | F | ?PFPPF??P | FAIL | FAIL |
| RDQ0222 | cyclophosphamide | closed/gpt4o_mini | dropped_basis | 10 mg per kg | 500 mg | F | F | F | F | F | F | F | F?FFPF?FF | FAIL | FAIL |
| RDQ0228 | clonidine | closed/gpt4o_mini | time_basis | 0.1 mg/day | 0.1 mg/week | F | F | F | F | F | F | F | FFFFPF?FF | FAIL | FAIL |
| RDQ0247 | ivermectin | closed/gemma3_27b | dropped_basis | 150 mcg/kg | 15 mg | F | F | F | F | F | F | F | FFFPPFFFF | FAIL | FAIL |
| RDQ0258 | epinephrine | closed/gemma3_27b | dropped_basis | 0.05 mcg/kg/min | 1-4 micrograms per minute | F | F | F | P | F | F | F | FFFPPFF?F | FAIL | FAIL |
| RDQ0263 | ceftriaxone | closed/gemma3_27b | dropped_basis | 50 to 75 mg/kg | 500 mg | F | F | F | F | F | F | F | FFFFPF??F | FAIL | FAIL |

## Caveats

- Frontier models are reasoning models: temperature 0 is sent where accepted; if the API rejects it the run continues with the provider default (column 'temperature sent'). Hidden reasoning/thinking tokens are billed as output and count against the max-output cap; 'truncated' = cap hit (verdict usually PARSE_FAIL).
- Model IDs are aliases/snapshots as served on the run date (`api model` column); provider-side changes can alter results.
- RD error labels are automatic; the 12 precheck-true cases are AI-checked, not human-verified.
