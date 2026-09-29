# Lane B instance files restored (2026-09-30)

## `data/v3/instances_t14_pending_node30.jsonl`

- **Was non-empty:** 233 rows through commit `71d5389` (T14 post-PI regen).
- **Emptied:** `cca292b` ("Refresh batch status…") deleted 233 lines from this file and `data/t14/instances_t14_pending_openrouter.jsonl` (plain `git` write, not `safe_jsonl`).
- **Restore:** copied from `71d5389` (233 rows). `build_t14_score_pending.py` reports `pending=0` because all 233 ids already appear under `results/raw/t14/`; Lane B still scores this cohort into `results/raw/lane_b/t14_pending/`.

## `data/lane_b/m1_t7_e1_unit.jsonl`

- **Never populated** in git (always 0 bytes). `lane_b_build_m1_packs.py` wrongly used `qc/t7_e1_unit_sample.csv` ∩ `instances_main` → 0 rows.
- **Rebuild:** valid `E1-unit-claim` / `E1-unit-evid` from `data/t7/instances_e1_unit.jsonl` with frozen `apply_m1_pair` + `m1_preapplied=true` (214 valid / 230 total in source).
