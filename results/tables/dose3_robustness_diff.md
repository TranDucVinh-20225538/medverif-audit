# DOSE robustness (dose3 audit) — all headline verifiers

Subsets: **(a)** all valid DOSE main; **(b)** drop `weak_e1_contrast` E1 rows; **(c)** drop `c0_underspecified` bases. Conditional rates use **C0 PASS** per verifier.

Scores merged from `results/raw/**` (+ t2_full, t6b/full, t7, raw_m1). V4 audit: see `notes/openrouter_model_audit.md`.

## Weak-contrast flags (main DOSE, rule-based)

- Instances flagged: **318** (60 bases).
- By reason tag (non-exclusive): **threshold_context** 266, **pk_descriptive** 8, **within_evidence_range** 86.
- Sole reason only: threshold 224, PK-descriptive 6, within-range 46.
- Top combos: `threshold_context` 224, `within_evidence_range` 46, `threshold_context+within_evidence_range` 40, `pk_descriptive` 6, `pk_descriptive+threshold_context` 2 (full list `notes/dose3_weak_contrast_breakdown.json`).

## (a) all valid

| Verifier | INV-unit PASS | E1-claim x2 FAIL | E1-claim x10 FAIL | T7 unit-claim FAIL | T7 unit-evid FAIL | n(inv) |
| --- | --- | --- | --- | --- | --- | ---: |
| V1 | 98.8% | 97.0% | 99.3% | 100.0% | 89.5% | 81 |
| V4 | 98.8% | 97.1% | 95.6% | 98.1% | 84.8% | 82 |
| V1b | 97.0% | 92.7% | 100.0% | 98.1% | 13.1% | 66 |
| V5 | 97.0% | 100.0% | 100.0% | 98.1% | 68.2% | 66 |
| V2a | 100.0% | 97.0% | 91.0% | 52.4% | 21.4% | 80 |
| V3 | 100.0% | 97.7% | 90.9% | 52.9% | 40.2% | 78 |
| Bespoke | 78.8% | 96.3% | 95.5% | 67.3% | 36.4% | 66 |
| T6B gpt4o-mini | 74.2% | 99.0% | 99.1% | 92.2% | 73.8% | 62 |
| T6B haiku4.5 | 96.8% | 98.1% | 100.0% | 98.1% | 88.5% | 63 |
| T6B llama3.1-8b | 27.4% | 99.0% | 98.1% | 83.5% | 47.6% | 62 |
| T6B mistral3.2-24b | 97.0% | 98.2% | 100.0% | 91.6% | 46.7% | 66 |
| T6A MiniCheck-RoBERTa | — | — | — | 15.0% | 15.0% | 0 |
| T6A MiniCheck-DeBERTa | — | — | — | 94.7% | 78.9% | 0 |
| T6A AlignScore-base | — | — | — | 9.5% | 14.3% | 0 |
| T6A SummaC-ZS | — | — | — | 38.9% | 22.2% | 0 |
| T6A SummaC-Conv | — | — | — | 64.3% | 57.1% | 0 |
| T6A HHEM | — | — | — | 0.0% | 0.0% | 0 |
| T6A Granite Guardian | — | — | — | 27.3% | 9.1% | 0 |

## (b) excl weak E1

| Verifier | INV-unit PASS | E1-claim x2 FAIL | E1-claim x10 FAIL | T7 unit-claim FAIL | T7 unit-evid FAIL | n(inv) |
| --- | --- | --- | --- | --- | --- | ---: |
| V1 | 98.8% | 96.6% | 98.9% | 100.0% | 89.5% | 81 |
| V4 | 98.8% | 96.6% | 94.4% | 98.1% | 84.8% | 82 |
| V1b | 97.0% | 95.0% | 100.0% | 98.1% | 13.1% | 66 |
| V5 | 97.0% | 100.0% | 100.0% | 98.1% | 68.2% | 66 |
| V2a | 100.0% | 96.5% | 87.6% | 52.4% | 21.4% | 80 |
| V3 | 100.0% | 96.4% | 88.5% | 52.9% | 40.2% | 78 |
| Bespoke | 78.8% | 95.0% | 93.7% | 67.3% | 36.4% | 66 |
| T6B gpt4o-mini | 74.2% | 100.0% | 98.3% | 92.2% | 73.8% | 62 |
| T6B haiku4.5 | 96.8% | 98.3% | 100.0% | 98.1% | 88.5% | 63 |
| T6B llama3.1-8b | 27.4% | 100.0% | 100.0% | 83.5% | 47.6% | 62 |
| T6B mistral3.2-24b | 97.0% | 98.3% | 100.0% | 91.6% | 46.7% | 66 |
| T6A MiniCheck-RoBERTa | — | — | — | 15.0% | 15.0% | 0 |
| T6A MiniCheck-DeBERTa | — | — | — | 94.7% | 78.9% | 0 |
| T6A AlignScore-base | — | — | — | 9.5% | 14.3% | 0 |
| T6A SummaC-ZS | — | — | — | 38.9% | 22.2% | 0 |
| T6A SummaC-Conv | — | — | — | 64.3% | 57.1% | 0 |
| T6A HHEM | — | — | — | 0.0% | 0.0% | 0 |
| T6A Granite Guardian | — | — | — | 27.3% | 9.1% | 0 |

## (c) excl C0 underspec

| Verifier | INV-unit PASS | E1-claim x2 FAIL | E1-claim x10 FAIL | T7 unit-claim FAIL | T7 unit-evid FAIL | n(inv) |
| --- | --- | --- | --- | --- | --- | ---: |
| V1 | 98.6% | 96.7% | 99.2% | 100.0% | 89.9% | 73 |
| V4 | 98.6% | 96.7% | 95.9% | 97.8% | 84.3% | 74 |
| V1b | 96.6% | 92.6% | 100.0% | 97.8% | 13.2% | 58 |
| V5 | 96.6% | 100.0% | 100.0% | 97.8% | 65.9% | 58 |
| V2a | 100.0% | 96.6% | 90.1% | 52.3% | 22.7% | 73 |
| V3 | 100.0% | 97.5% | 90.8% | 50.6% | 39.1% | 71 |
| Bespoke | 81.0% | 96.8% | 96.9% | 67.0% | 39.6% | 58 |
| T6B gpt4o-mini | 75.9% | 98.9% | 98.9% | 90.8% | 70.1% | 54 |
| T6B haiku4.5 | 96.4% | 97.8% | 100.0% | 97.8% | 87.6% | 56 |
| T6B llama3.1-8b | 30.9% | 98.9% | 97.9% | 81.8% | 44.3% | 55 |
| T6B mistral3.2-24b | 96.6% | 97.9% | 100.0% | 91.2% | 44.0% | 58 |
| T6A MiniCheck-RoBERTa | — | — | — | 11.8% | 11.8% | 0 |
| T6A MiniCheck-DeBERTa | — | — | — | 93.8% | 75.0% | 0 |
| T6A AlignScore-base | — | — | — | 5.6% | 11.1% | 0 |
| T6A SummaC-ZS | — | — | — | 31.2% | 25.0% | 0 |
| T6A SummaC-Conv | — | — | — | 58.3% | 58.3% | 0 |
| T6A HHEM | — | — | — | 0.0% | 0.0% | 0 |
| T6A Granite Guardian | — | — | — | 26.3% | 10.5% | 0 |

**T6-A (7 encoders):** main-pack INV / E1 cells use `results/raw/t4_eco/t6_*.jsonl` (0 overlap with main); T7 unit columns merge `results/raw/t7/t6_*.jsonl` when present.

## Shifts > 3 pp vs (a)

| Verifier | Metric | Subset | (a) | subset | Δ pp |
| --- | --- | --- | ---: | ---: | ---: |
| t6a_summac_zs | t7_unit_claim_fail | excl_c0_underspec | 38.89% | 31.25% | -7.64 |
| t6a_summac_conv | t7_unit_claim_fail | excl_c0_underspec | 64.29% | 58.33% | -5.95 |
| t6a_alignscore_base | t7_unit_claim_fail | excl_c0_underspec | 9.52% | 5.56% | -3.97 |
| t6a_minicheck_deberta | t7_unit_evid_fail | excl_c0_underspec | 78.95% | 75.0% | -3.95 |
| v6_ragas_gpt4o_mini | t7_unit_evid_fail | excl_c0_underspec | 73.79% | 70.11% | -3.67 |
| v6_ragas_llama31_8b | inv_unit_pass | excl_c0_underspec | 27.42% | 30.91% | +3.49 |
| v2a_minicheck | e1_x10_fail | excl_weak_e1 | 90.98% | 87.64% | -3.34 |
| v6_ragas_llama31_8b | t7_unit_evid_fail | excl_c0_underspec | 47.57% | 44.32% | -3.25 |
| t6a_minicheck_roberta | t7_unit_claim_fail | excl_c0_underspec | 15.0% | 11.76% | -3.24 |
| t6a_minicheck_roberta | t7_unit_evid_fail | excl_c0_underspec | 15.0% | 11.76% | -3.24 |
| t6a_alignscore_base | t7_unit_evid_fail | excl_c0_underspec | 14.29% | 11.11% | -3.17 |
| v2b_bespoke | t7_unit_evid_fail | excl_c0_underspec | 36.45% | 39.56% | +3.11 |
