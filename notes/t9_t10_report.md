# T9 / T10 report

NeMo Guardrails **0.24.1** rail (`FACT_CHECK_THRESHOLD=0.5`, block if score < 0.5).
Scored manifest: **`data/t9/instances_all.jsonl`** (n=457).

## Manifest: legacy scores → current inputs

Current manifest applies effective_unit_natural_y: human qc/unit_naturalness.csv (Y/N) overrides rule_natural_unit_conversion_label on INV-claim unit_conversion spans. Legacy 536-line batch included inv_unit_natural rows that fail this gate.

| metric | value |
|---|---:|
| Legacy scored lines | 536 |
| Legacy unique instance_ids | 524 |
| Legacy duplicate extra lines | 12 |
| **Current manifest (scored)** | **457** |
| Unique instance_ids dropped | 69 |

**Removal reasons (unique instance_ids):**

- `rule_natural_unit_conversion_false`: **69**

**Group-b stratum (current manifest):**

- `eco_reexpressed`: 27
- `inv_unit_natural`: 22

## T9 — AlignScore-base

Endpoint: `http://127.0.0.1:5000/alignscore_base` · n=457

### Groups a–d

| group | n | block_rate | 95% CI |
|---|---:|---:|---|
| a | 59 | 0.169 | [0.085, 0.271] |
| b | 49 | 0.429 | [0.306, 0.571] |
| c | 119 | 0.983 | [0.958, 1.000] |
| d | 230 | 0.230 | [0.178, 0.287] |

### Group b strata

| slice | n | block_rate | 95% CI |
|---|---:|---:|---|
| a:eco_verbatim | 59 | 0.169 | [0.085, 0.271] |
| b:eco_reexpressed | 27 | 0.148 | [0.037, 0.296] |
| b:inv_unit_natural | 22 | 0.773 | [0.591, 0.955] |

## T9 — AlignScore-large

Endpoint: `http://127.0.0.1:5001/alignscore_large` · n=457

### Groups a–d

| group | n | block_rate | 95% CI |
|---|---:|---:|---|
| a | 59 | 0.169 | [0.085, 0.271] |
| b | 49 | 0.429 | [0.306, 0.571] |
| c | 119 | 0.983 | [0.958, 1.000] |
| d | 230 | 0.504 | [0.439, 0.570] |

### Group b strata

| slice | n | block_rate | 95% CI |
|---|---:|---:|---|
| a:eco_verbatim | 59 | 0.169 | [0.085, 0.271] |
| b:eco_reexpressed | 27 | 0.111 | [0.000, 0.222] |
| b:inv_unit_natural | 22 | 0.818 | [0.636, 0.955] |

## Eco source comparison (group a vs group b)

Group **a** = T4 eco exact verbatim only. Group **b** = eco re-expressions + natural INV unit conversions.

| checkpoint | slice | n | block_rate | 95% CI |
|---|---|---:|---:|---|
| AlignScore-base | group a | 59 | 0.169 | [0.085, 0.271] |
| AlignScore-base | group b | 49 | 0.429 | [0.306, 0.571] |
| AlignScore-base | b:eco_reexpressed | 27 | 0.148 | [0.037, 0.296] |
| AlignScore-base | b:inv_unit_natural | 22 | 0.773 | [0.591, 0.955] |
| AlignScore-large | group a | 59 | 0.169 | [0.085, 0.271] |
| AlignScore-large | group b | 49 | 0.429 | [0.306, 0.571] |
| AlignScore-large | b:eco_reexpressed | 27 | 0.111 | [0.000, 0.222] |
| AlignScore-large | b:inv_unit_natural | 22 | 0.818 | [0.636, 0.955] |

