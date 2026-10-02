# RD2 expected natural errors (ESTIMATE, not a result)

RD error rates per pre-registered dosing stratum (same tagger) x RD2 questions per stratum x 6 generators x 2 conditions = 5760 answers.  `auto unit-type` = rd_extract unit_error+basis_error; `AI-true` = AI pre-check true_unit_error (AI-assisted, not human-verified; 12/47 in RD).  Strata with < 20 RD answers per condition use the pooled error-prone (or fixed) rate.

| stratum | RD q | RD2 q | cond | RD answers | RD auto unit-type | RD AI-true | RD value err | exp. auto unit-type | exp. AI-true | exp. value err |
|---|---|---|---|---|---|---|---|---|---|---|
| bsa | 3 | 108 | grounded | 6 | 4 | 0 | 0 | 15.8 | 2.0 | 0.0 | rate borrowed from pooled ERROR_PRONE
| bsa | 3 | 108 | closed | 6 | 3 | 0 | 0 | 61.2 | 17.8 | 86.9 | rate borrowed from pooled ERROR_PRONE
| weight_based | 54 | 138 | grounded | 108 | 1 (0.9%) | 1 (0.9%) | 0 (0.0%) | 7.7 | 7.7 | 0.0 |
| weight_based | 54 | 138 | closed | 108 | 24 (22.2%) | 9 (8.3%) | 15 (13.9%) | 184.0 | 69.0 | 115.0 |
| loading_maintenance | 14 | 28 | grounded | 28 | 1 (3.6%) | 0 (0.0%) | 0 (0.0%) | 6.0 | 0.0 | 0.0 |
| loading_maintenance | 14 | 28 | closed | 28 | 1 (3.6%) | 0 (0.0%) | 6 (21.4%) | 6.0 | 0.0 | 36.0 |
| renal | 35 | 43 | grounded | 70 | 2 (2.9%) | 0 (0.0%) | 0 (0.0%) | 7.4 | 0.0 | 0.0 |
| renal | 35 | 43 | closed | 70 | 2 (2.9%) | 0 (0.0%) | 12 (17.1%) | 7.4 | 0.0 | 44.2 |
| pediatric | 47 | 68 | grounded | 94 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0.0 | 0.0 | 0.0 |
| pediatric | 47 | 68 | closed | 94 | 1 (1.1%) | 0 (0.0%) | 9 (9.6%) | 4.3 | 0.0 | 39.1 |
| divided_daily | 11 | 23 | grounded | 22 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0.0 | 0.0 | 0.0 |
| divided_daily | 11 | 23 | closed | 22 | 0 (0.0%) | 0 (0.0%) | 2 (9.1%) | 0.0 | 0.0 | 12.5 |
| fixed | 200 | 72 | grounded | 400 | 1 (0.2%) | 0 (0.0%) | 1 (0.2%) | 1.1 | 0.0 | 1.1 |
| fixed | 200 | 72 | closed | 400 | 7 (1.8%) | 2 (0.5%) | 48 (12.0%) | 7.6 | 2.2 | 51.8 |

**Expected totals (estimate):** auto-flagged unit/basis errors ≈ 308 (range 192-626), AI-pre-check-true unit/basis errors ≈ 99 (range 48-363), value errors ≈ 387 (range 244-719); RD had 47 / 12 / 93 in 1456 answers.  Ranges = sums of per-cell Wilson 95% bounds (not a joint interval).  Caveats: RD's BSA cells are 4/6 parser artifacts (`mg/m 2`), which RD2 repairs in the label text, so the auto unit-type estimate for BSA is inflated; RD's generators were API models; the AI pre-check is not human-verified.

