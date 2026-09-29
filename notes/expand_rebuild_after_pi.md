# Expanded set rebuild after PI (2026-09-29)

## Pipeline
1. `scripts/merge_all_pi_labels.py` → merged labels into QC CSVs
2. `MEDVERIF_QC_V3_EXPAND=1` → `src/apply_qc_v3_decisions.py` (main-parity G/H/I/J, range subset, flip blocks, non_dose_target)
3. `scripts/expand/rebuild_after_pi.py` → dose PI overrides (80 labeled bases; six no-drug-in-evidence → **Y**)
4. Fresh spot-check sample: `qc/expand_dose_sample.csv` (**56** DOSE bases, seed **20260929**, empty `PI_ok`)

## Yield (valid, post-fix)
| Slice | Bases (main) | Valid main instances |
|---|---:|---:|
| DOSE | 222 | (see json) |
| POLARITY | 138 | |
| **Total main bases** | **360** | **2173** |
| threshold instances | — | 290 |
| range instances | — | 481 |
| cpu_early (main+thr, no paraphrase) | — | 2463 |

Full counts: `notes/expand_rebuild_after_pi.json`.

## Unit natural (rule + PI)
- Expanded INV-unit: **219** instances / **219** bases; **35** effective natural (**Y**) under tightened rule + `qc/expand_unit_natural.csv` PI (14/40 sample **Y**).
- Main set (unchanged cohort): **88** unit INV bases; **42** effective natural (**Y**) — `notes/unit_inv_counts.json`.

## Analysis gate
Headline tables = **main set only** until spot-check **≥85% Y** on the new `expand_dose_sample.csv`.

## Not in this run
- LLM **C0 claim regen** (drug name / qualifier drop): bases rejected via dose PI **N** on the 80-row review; automated regen remains TODO (`stage12` + validator).
