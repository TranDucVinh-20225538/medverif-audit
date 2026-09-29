# V4 (Llama-3.3-70B) headline numbers

Provenance: `results/raw/v4_ragas_nli.llama.jsonl` (+ E2 overlay from `e2_main/`).
DOSE main+threshold, `analysis_keep_row`, conditional on **C0 PASS** unless noted.

| Metric | Llama |
|---|---|
| INV-unit PASS (all valid) | 48/62 |
| INV-unit PASS (natural=Y) | — |
| E1-evid x2 FAIL | 97/101 |
| E1-evid x10 FAIL | 91/101 |
| E1-claim x2 FAIL | 96/102 |
| E1-claim x10 FAIL | 103/104 |
| C0 PASS (magnitude none) | 110/110 |
| E2 PASS (|C0; main×2 cohort scores) | 234/241 |
| T7 E1-unit-claim FAIL (|C0) | — |
| T7 E1-unit-evid FAIL (|C0) | — |
| T9 V4 scores | none |

## T7 (115 bases): legacy vs Llama (|C0)

Pack agreement (legacy↔Llama): see `notes/v4_legacy_llama_agreement.md` (**78.8%** on t7).

| Source | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---|---|
| legacy | 0 | — | — |
| llama | 0 | — | — |

