# E2 | C0 vs T7 E1-unit (per verifier)

- E2 cohort: **main x2** (`instances_main_x2.jsonl`); conditional on each verifier's C0 PASS.
- T7 E1-unit: **115** claim + **115** evid instances (115 bases).

| verifier | E2 PASS (|C0) | E1-unit-claim FAIL | E1-unit-evid FAIL |
|---|---:|---:|---:|
| t6_alignscore_base | — | 0.217 (115/115) | 0.243 (115/115) |
| t6_granite_guardian | — | 0.452 (115/115) | 0.235 (115/115) |
| t6_hhem | — | 0.035 (115/115) | 0.078 (115/115) |
| t6_minicheck_deberta | — | 0.870 (115/115) | 0.739 (115/115) |
| t6_minicheck_roberta | — | 0.391 (115/115) | 0.304 (115/115) |
| t6_summac_conv | — | 0.661 (115/115) | 0.722 (115/115) |
| t6_summac_zs | — | 0.383 (115/115) | 0.357 (115/115) |
| v1_medscore | 0.881 (726/824) | — (0/115) | — (0/115) |
| v2a_minicheck | 0.983 (283/288) | — (0/115) | — (0/115) |
| v3_alignscore | 0.990 (283/286) | — (0/115) | — (0/115) |
| v4_ragas_nli | 0.975 (432/443) | — (0/115) | — (0/115) |

