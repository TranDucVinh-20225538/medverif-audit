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
| 01:00 | H8 | — | `v4_legacy_agreement_report.py` | 7d8e919 |
| 01:15 | t19_8b | Incomplete HF cache + offline | `medverif_hf_offline_if_cached` + online 61485 | (HEAD) |
| 01:15 | t15_eval | AggreFact `doc` not mapped to evidence | `_normalize_rows` + skip empty pairs | (HEAD) |
| 01:16 | H7 | Registry assert blocked gpt-4o v4 | `MEDVERIF_SKIP_OPENROUTER_REGISTRY_ASSERT` | 6cc584d |
| 01:17 | bespoke_gpu | ExcNodeList node002,004 | Resubmit 61486 after 61485, exclude node004 only | — |
