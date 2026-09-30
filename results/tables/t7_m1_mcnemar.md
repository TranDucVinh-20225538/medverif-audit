<!-- LEGACY — not for paper. Use results/tables/card_main.md and qvc/paper_numbers.json from scripts/compute_paper_numbers.py. -->

# T7 M1: E1-unit FAIL |C0 PASS| (before vs after M1)

- Cohort: **115** E1-unit-claim + **115** E1-unit-evid (115 bases)
- **Before:** merged scores (`results/raw/t7` + main for V1/V4)
- **After:** `results/raw_m1/t7`

| Verifier | Dir | n | FAIL before | FAIL after | McNemar b/c | p≈ |
|---|---|---:|---:|---:|---:|---:|
| v2a_minicheck | E1-unit-claim | 0 | — | — | 0/0 | — |
| v2a_minicheck | E1-unit-evid | 0 | — | — | 0/0 | — |
| v3_alignscore | E1-unit-claim | 0 | — | — | 0/0 | — |
| v3_alignscore | E1-unit-evid | 0 | — | — | 0/0 | — |
| v1_medscore | E1-unit-claim | 0 | — | — | 0/0 | — |
| v1_medscore | E1-unit-evid | 0 | — | — | 0/0 | — |
| v4_ragas_nli | E1-unit-claim | 0 | — | — | 0/0 | — |
| v4_ragas_nli | E1-unit-evid | 0 | — | — | 0/0 | — |

### LLM judges (V1, V4)

| Verifier | Dir | n | FAIL before | FAIL after | b/c | p≈ |
|---|---|---:|---:|---:|---:|---:|
| v1_medscore | E1-unit-claim | 0 | — | — | 0/0 | — |
| v1_medscore | E1-unit-evid | 0 | — | — | 0/0 | — |
| v4_ragas_nli | E1-unit-claim | 0 | — | — | 0/0 | — |
| v4_ragas_nli | E1-unit-evid | 0 | — | — | 0/0 | — |
