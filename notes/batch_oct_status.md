# Batch Oct status (HPC)

Updated: 2026-09-30 14:22 (UTC+7)

## PI review → scoring (GO 30/9 PM)

| Item | Status |
|------|--------|
| `qc/main_ext_labels.csv` + `qc/t17_labels.csv` | **IN REPO** |
| PI filters | **APPLIED** — main_ext **380/480** valid; T17 **516/612**; **44** INV natural Y (`notes/pi_review_filter_manifest.json`) |
| `qc/t18_sample.csv` | **FINAL** re-export (92 INV rows, claim_c0 + spans) |
| main_ext OR score | **RUNNING** — v1 on **380** valid rows, cap **$2** (`jobs/logs/main_ext_or_*.log`) |
| T15 GPU | **61549** ft AggreFact **node002**; **base** + **pack ft** queued (61554); node001 **drained** |
| T20 steps 1–2 | **DONE** — `data/t20/drug_list.jsonl` (20 drugs this pass; expand matching); openFDA cache in `data/t20/labels/` |

## T15 AggreFact (library GPU)

- Base file restored **19 460/29 320** (CPU partial); ft reset for clean library run.
- `t15_eval.py`: AggreFact only on full eval or `--aggrefact-only`; packs include **main_ext** + **t17**.
- Cal **61541**: 100% verdict agreement (MiniCheck library GPU).

## Still open

- T15 base+ft finish → `t15_aggrefact_report.py`
- T20 steps 3–4 (M1 match + BM25 + wild CSV)
- T22/T23
- Audit zip refresh if needed

**OR:** user topped up; main_ext scoring uses OpenRouter with **$2** cap.

<!-- job-elapsed-table -->
