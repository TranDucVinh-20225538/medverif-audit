# Batch Oct status (HPC)

Updated: 2026-09-30 01:16 (UTC+7)

## Fix round (7 items)

| Item | Status | Notes |
|------|--------|-------|
| Lane C v6 | **RUNNING** | v1–v5 **854/854**; `v6_ragas_gpt4o_mini` in progress (~776/854 @ 01:16). |
| main_ext count | **DONE** | Cohort **60** INV bases — `notes/main_ext_cohort_report.md`; stage1 **892** = expand only. |
| T15 eval | **RUNNING** | Packs scored; AggreFact failed on empty evidence → **fix pushed**; re-run in flight. |
| T18 pack | **DONE** | 100 bases / 736 instances (`scripts/build_t18_wikipedia_pack.py`). |
| Legacy cal | **DONE (partial)** | SummaC-ZS + Granite **100%** downstream OK; Conv/HHEM **&lt;97%** → human hold. |
| T19 3B POL + 8B | **3B DONE** | `llama32_3b_instruct.jsonl` **1703** lines; **8B Slurm 61485** loading weights (online HF). |
| Lane B T17 V2a/V3 | **DONE** | **588/588** valid; 24 invalid `non_dose_target`. |

**Git:** `7d8e919` autonomous batch; `fix(t15/t19)` on HEAD after push.

## Queued / overnight

| Task | Status |
|------|--------|
| Bespoke-7B GPU | **61484 PENDING** (node001/004 unavailable); resubmit after GPU frees. |
| H7 prompt×model | **STARTED** (`run_prompt_x_model_hpc.sh`, ≤$2). |
| H8 agreement | **DONE** — `notes/v4_legacy_llama_agreement.{json,md}`. |
| T16 base-model IG | **BLOCKED** — no job/scripts in repo (see `needs_human.md`). |

## OpenRouter night

- `notes/lane_or_night_spend.json`: **~$5.36 / $10** (~$4.64 left).
- Lane C cap **$3** — watch during v6 completion.

## Slurm (toandq)

| JobID | Name | State |
|------:|------|-------|
| 61480 | tmlr-e1 | RUNNING (node002) |
| 61485 | t19-llama31_8b_local | RUNNING (node002, fetching shards) |
| 61484 | lane_b_bespoke | PENDING |

## Lanes

- **Lane C:** `nohup jobs/run_lane_c_m1_h2.sh` — log `jobs/logs/lane_c_m1_h2_*.log`.
- **Lane B CPU:** largely complete; bespoke GPU deferred.

<!-- job-elapsed-table -->
