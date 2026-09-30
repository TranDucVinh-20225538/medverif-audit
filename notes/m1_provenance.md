# M1 text provenance and amendment-4 spec check

Texts behind `m1_strong_final` (`8939e6c`). Script: `scripts/m1_provenance_check.py`.

| Pack | used by | node30 repro | head_8939e6c repro | M1 rows scored | off-spec rows (bases) |
| --- | --- | ---: | ---: | ---: | ---: |
| us_up_local | all local checkers + Bespoke/Granite | 204/214 | 214/214 | 214 | 46 (23) |
| us_up_api | v1_medscore, v4/v5_ragas_nli | 313/345 | 290/345 | 230 | 38 (19) |
| us_down | all checkers | 150/150 | 150/150 | 150 | 0 (0) |

NS packs (no M1 by design): 92/408 rows would change under spec M1.
