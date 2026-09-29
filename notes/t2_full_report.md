# T2 full report

- Instances: **533**
- Scored rows: **1066** (target 1066)
- Spend: **$3.1563**
- Approx $/instance/verifier: **$0.00592**
- OpenRouter limit_remaining: **44.62516605**

Conditional rates below use **C0 PASS** on the same verifier unless noted.

## Summary (main T2 scope)

| Verifier | C0 pass | E1-claim FAIL x2 | E1-claim FAIL x10 | INV-unit PASS (all) | INV-unit PASS (natural) | INV-unit PASS (PI-reviewed) | POL E1 FAIL (26 flip_ok) | POL INV PASS (template) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1b (gpt-4o) | 119/119 (1.000) | 109/119 (0.916) | 118/119 (0.992) | 68/70 (0.971) | 35/35 (1.000) | — | 25/26 (0.962) | 34/34 (1.000) |
| V5 (Claude Sonnet) | 119/119 (1.000) | 119/119 (1.000) | 119/119 (1.000) | 67/70 (0.957) | 34/35 (0.971) | — | 26/26 (1.000) | 34/34 (1.000) |

**DOSE macro (bootstrap by base, same filters):**

| Verifier | Invariance (INV) | Sensitivity (E1-evid FAIL) |
| --- | ---: | ---: |
| V1b (gpt-4o) | — | — |
| V5 (Claude Sonnet) | — | — |

## T3 slice (freq + route, PI_ok=Y, n=36 scored in raw/t3_t2)

| Verifier | INV frequency PASS | INV route PASS |
| --- | --- | --- |
| V1b (gpt-4o) | 14/14 (1.000) | 22/22 (1.000) |
| V5 (Claude Sonnet) | 14/14 (1.000) | 22/22 (1.000) |
