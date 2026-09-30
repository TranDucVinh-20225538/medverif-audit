# Needs human

## Closed (2026-09-30) — Decision **M**

SummaC-Conv and HHEM legacy calibration remain &lt;97% vs node30. **Excluded from all new Lane B pack scoring**; paper main-card uses **node30** scores only. See `notes/decision-log.md` (M). Downstream routing: `t6a_summac_zs`, `t6a_granite_guardian` only.

## main_ext vs stage1 counts

- **892 bases** in stage1 continue logs = expand funnel artifact, **not** main_ext scoring cohort.
- **main_ext** = **60** whitelist INV bases / **60** INV review rows — see `notes/main_ext_cohort_report.md`.

## Held until PI review (2026-09-30)

- **main_ext** and **T18** instance scoring — do not run verifiers until review CSV returned.

## T19 8B weights

- Resolved: weights cached; **61485** completed **1703/1703**.
