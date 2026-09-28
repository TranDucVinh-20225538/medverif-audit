# T8b supported-pair false-alarm report

Expected verdict: **PASS** (original label = supported). False alarm = verifier **FAIL**.

## T8b per group (FAIL rate = false alarm)

| verifier | group | n | FAIL rate | 95% CI |
|---|---|---:|---:|---|
| v1b_medscore | format_mismatch | 0 | — | — |
| v1b_medscore | qty_match | 0 | — | — |
| v2a_minicheck | format_mismatch | 0 | — | — |
| v2a_minicheck | qty_match | 0 | — | — |
| v3_alignscore | format_mismatch | 0 | — | — |
| v3_alignscore | qty_match | 0 | — | — |
| t6a_minicheck_roberta | format_mismatch | 0 | — | — |
| t6a_minicheck_roberta | qty_match | 0 | — | — |
| t6a_minicheck_deberta | format_mismatch | 0 | — | — |
| t6a_minicheck_deberta | qty_match | 0 | — | — |
| t6a_alignscore_base | format_mismatch | 0 | — | — |
| t6a_alignscore_base | qty_match | 0 | — | — |
| t6a_summac_zs | format_mismatch | 0 | — | — |
| t6a_summac_zs | qty_match | 0 | — | — |
| t6a_summac_conv | format_mismatch | 0 | — | — |
| t6a_summac_conv | qty_match | 0 | — | — |
| t6a_hhem | format_mismatch | 0 | — | — |
| t6a_hhem | qty_match | 0 | — | — |
| t6a_granite_guardian | format_mismatch | 0 | — | — |
| t6a_granite_guardian | qty_match | 0 | — | — |

## BAcc reference (supported sample = groups i+ii, expected PASS)

| verifier | BAcc |
|---|---:|
| v1b_medscore | — |
| v2a_minicheck | — |
| v3_alignscore | — |
| t6a_minicheck_roberta | — |
| t6a_minicheck_deberta | — |
| t6a_alignscore_base | — |
| t6a_summac_zs | — |
| t6a_summac_conv | — |
| t6a_hhem | — |
| t6a_granite_guardian | — |

## T8 unit sample split

| verifier | INV pass rate | E1-unit fail rate |
|---|---:|---:|
| v1b_medscore | 0.390 (n=100) | 0.170 (n=100) |
| v2a_minicheck | — | — |
| v3_alignscore | — | — |
| t6a_minicheck_roberta | — | — |
| t6a_minicheck_deberta | — | — |
| t6a_alignscore_base | — | — |
| t6a_summac_zs | — | — |
| t6a_summac_conv | — | — |
| t6a_hhem | — | — |
| t6a_granite_guardian | — | — |
