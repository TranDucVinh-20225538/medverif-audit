# M1-strong gate: M1 (spec) vs independent M1-lib (quantulum3 + pint)

Script: `scripts/m1_gate_independent.py`; parser: `src/m1_lib_indep.py` (no repo imports).

| Pack | instances | gate pass old → new | spans | same | differs | M1-lib fails | M1 fails |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| us_up_x1000 | 214 | 214 → 214 | 430 | 430 | 0 | 0 | 0 |
| us_down_unit | 150 | 150 → 150 | 300 | 300 | 0 | 0 | 0 |
| ns_x10_claim | 106 | 106 → 106 | 212 | 212 | 0 | 0 | 0 |
| ns_x10_evid | 106 | 106 → 106 | 212 | 212 | 0 | 0 | 0 |
| ns_div10_claim | 98 | 98 → 98 | 196 | 196 | 0 | 0 | 0 |
| ns_div10_evid | 98 | 98 → 98 | 196 | 196 | 0 | 0 | 0 |

Bases in cohort: 110 → 110; dropped: none

