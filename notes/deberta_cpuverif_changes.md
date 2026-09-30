# MiniCheck-DeBERTa → cpuverif: changed table cells (baseline = same code, pre-swap DeBERTa files)

Snapshot: `/tmp/base_now` vs working tree. Script: `scripts/table_change_list.py`.

## `results/tables/t13_pairwise_preference.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| Other pairs (supplementary) / MiniCheck-DeBERTa / 0.000 [0.000, 0.000] (n=107) | (3) E1×2 vs INV | 0.550 [0.350, 0.750] (n=20) | 0.600 [0.400, 0.800] (n=20) |

## `results/tables/t14_c0_conditional_pass.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| T14 — pass rates conditional on C0 PASS / MiniCheck-DeBERTa / small fine-tuned checkers | C0 pass rate | 0.900 (n=110) | 0.891 (n=110) |
| T14 — pass rates conditional on C0 PASS / MiniCheck-DeBERTa / small fine-tuned checkers | C0) | 0.969 (n=98) | 0.969 (n=97) |
| T14 — pass rates conditional on C0 PASS / MiniCheck-DeBERTa / small fine-tuned checkers | n C0 | 99 | 98 |
| T14 — pass rates conditional on C0 PASS / MiniCheck-DeBERTa / small fine-tuned checkers | unit spell | 1.000 (n=98) | 1.000 (n=97) |

## `results/tables/t17_ns.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| T17 — NS on value ÷2 / ÷10 (FAIL | C0 PASS) / MiniCheck-DeBERTa / small fine-tuned checkers | C0 PASS bases | 99/110 | 98/110 |
| T17 — NS on value ÷2 / ÷10 (FAIL | C0 PASS) / MiniCheck-DeBERTa / small fine-tuned checkers | ÷10 claim | 98.9% [96.7%, 100.0%] (n=90, q=90) | 98.9% [96.6%, 100.0%] (n=89, q=89) |
| T17 — NS on value ÷2 / ÷10 (FAIL | C0 PASS) / MiniCheck-DeBERTa / small fine-tuned checkers | ÷10 evid | 94.4% [90.0%, 98.9%] (n=90, q=90) | 94.4% [89.9%, 98.9%] (n=89, q=89) |
| T17 — NS on value ÷2 / ÷10 (FAIL | C0 PASS) / MiniCheck-DeBERTa / small fine-tuned checkers | ÷2 claim | 98.9% [95.5%, 100.0%] (n=89, q=89) | 98.9% [95.5%, 100.0%] (n=88, q=88) |
| T17 — NS on value ÷2 / ÷10 (FAIL | C0 PASS) / MiniCheck-DeBERTa / small fine-tuned checkers | ÷2 evid | 98.9% [96.6%, 100.0%] (n=89, q=89) | 98.9% [96.6%, 100.0%] (n=88, q=88) |

## `notes/t4c_eco_report.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| Summary table (all verifiers) / t6a_minicheck_deberta / frequency_rephrased | 95% CI | [0.333, 0.750] | [0.375, 0.792] |
| Summary table (all verifiers) / t6a_minicheck_deberta / frequency_rephrased | FAIL rate | 0.542 | 0.583 |
| t6a_minicheck_deberta / frequency_rephrased / 24 | 95% CI | [0.333, 0.750] | [0.375, 0.792] |
| t6a_minicheck_deberta / frequency_rephrased / 24 | FAIL rate | 0.542 | 0.583 |

## `notes/t7_e1_unit_report.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_minicheck_deberta / 0.804 | (row) | present | — |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_minicheck_deberta / 0.809 | (row) | — | present |

