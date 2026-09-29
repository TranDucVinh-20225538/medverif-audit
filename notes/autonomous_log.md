# Autonomous run log

| Time (+07) | Job | Cause | Fix | Commit |
|------------|-----|-------|-----|--------|
| 01:00 | lane_c | Missing `verifiers.v6_ragas_*` modules | Thin v6 wrappers + resume script skips complete rows | (see HEAD) |
| 01:00 | main_ext | 892 vs ~60 confusion | `main_ext_cohort_report.md` + INV review CSV (60 rows) | (see HEAD) |
| 01:00 | t15_eval | AggreFact rows lack `instance_id` | `_row_id()` + eval-only job | (see HEAD) |
| 01:00 | t18 | `max_shards` AttributeError | Use `parquet_shards`; built 100 bases / 736 inst | (see HEAD) |
| 01:00 | legacy_cal | HHEM tokenizer/model mismatch on tf 4.30.2 | `predict()` + cpuverif load; Granite via cpuverif | (see HEAD) |
| 01:00 | t19 | 3B POL + 8B not queued | `run_t19_submit_8b_pol.sh` → Slurm 61482/61483 | (see HEAD) |
| 01:00 | lane_b_t17 | “24 gap” | 588/588 valid done; 24 invalid `non_dose_target` | (see HEAD) |
| 01:00 | bespoke_gpu | deferred | Slurm 61484 (exclude node002) | (see HEAD) |
| 01:00 | H8 | — | `v4_legacy_agreement_report.py` | (see HEAD) |
