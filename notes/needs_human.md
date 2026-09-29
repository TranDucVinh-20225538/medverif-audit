# Needs human

## Legacy calibration <97% (do not enable downstream)

From `notes/lane_b_calibration_agreement_legacy.json` (93-id overlap with node30):

| Checker | Agreement | Action |
|---------|----------:|--------|
| SummaC-ZS | **100%** | OK for downstream |
| Granite Guardian | **100%** | OK for downstream |
| SummaC-Conv | **34.4%** | **Hold** — do not change threshold/filter; investigate node30 vs legacy env |
| HHEM 2.1 | **43.0%** | **Hold** — scores run (200 rows) but cal vs node30 fails; missing embed weights warning on load |

`legacy_downstream_allowed` currently: **t6a_summac_zs**, **t6a_granite_guardian** only.

## main_ext vs stage1 counts

- **892 bases** in stage1 continue logs = expand funnel artifact, **not** main_ext scoring cohort.
- **main_ext** = **60** whitelist INV bases / **60** INV review rows — see `notes/main_ext_cohort_report.md`.

## Queued work

- **T16 base-model IG** — no `t16` job/scripts in repo; need spec or path before running.
- **H7 prompt×model** — scripts exist (`jobs/run_prompt_x_model_hpc.sh`); autonomous run started 2026-09-30 ~01:16.

## T19 8B weights

- First 61482 failed: **HF offline** with incomplete cache (0/4 shards).
- 61485 uses **online fetch** + `HF_TOKEN`; background `huggingface-cli download` also running on login node.
