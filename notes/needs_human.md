# Needs human

## Closed (2026-09-30) — Decision **M**

SummaC-Conv and HHEM legacy calibration remain &lt;97% vs node30. **Excluded from all new Lane B pack scoring**; paper main-card uses **node30** scores only. See `notes/decision-log.md` (M). Downstream routing: `t6a_summac_zs`, `t6a_granite_guardian` only.

## main_ext vs stage1 counts

- **892 bases** in stage1 continue logs = expand funnel artifact, **not** main_ext scoring cohort.
- **main_ext** = **60** whitelist INV bases / **60** INV review rows — see `notes/main_ext_cohort_report.md`.

## Bespoke Lane B gate (job **61523**, 2026-09-30)

- Cal **200** scored → `results/raw/lane_b/calibration_200/v2b_bespoke.jsonl` (**bf16**, `quantized=false`; log: `Using bfloat16`, vLLM `quantization=None`).
- vs node30 `t6_bespoke_minicheck`: **n=93** overlap, **98.9%** verdict agreement, mean **|Δscore|=0.014** → **≥97% → Lane B packs proceeding**. Report: `notes/lane_b_bespoke_calibration.{json,md}`.

## Held until PI review (2026-09-30)

- **main_ext** and **T18** instance scoring — do not run verifiers until review CSV returned. Pending CSV index: `notes/pending_review_csvs.md`.

## T19 8B weights

- Resolved: weights cached; **61485** completed **1703/1703**.
