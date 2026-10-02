# Journal chain 3 — status

Generated 2026-10-02 09:37 UTC+7. Slurm jobs: {"JG": "62143", "FINAL": "62144", "FT": "62142", "submitted": "2026-10-01T19:46:23+07:00"}

## FT scoring (rows scored / expected)

| run | marker | rd_raw | ho_raw | ho_unf | ho_unf_v2 | rdunf_raw | rdunf_unf | rdunf_unf_v2 |
|---|---|---|---|---|---|---|---|---|
| minicheck_ft5_r1 | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |
| alignscore_large_r1 | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |
| minicheck_ft5_base | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |
| alignscore_large_base | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |
| minicheck_ft5_r0.5 | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |
| minicheck_ft5_r2 | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |
| alignscore_large_r0.5 | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |
| alignscore_large_r2 | done | 1451/1451 | 450/450 | 450/450 | 450/450 | 705/705 | 705/705 | 705/705 |

## LLM judges

| slug | HF id | download | marker | card | rag | rd |
|---|---|---|---|---|---|---|
| qwen25_7b | Qwen/Qwen2.5-7B-Instruct | ok | done | 958/958 | 1622/1622 | 1451/1451 |
| llama31_8b | meta-llama/Llama-3.1-8B-Instruct | ok | done | 958/958 | 1622/1622 | 1451/1451 |
| medgemma_4b | google/medgemma-4b-it | ok | done | 958/958 | 1622/1622 | 1451/1451 |
| qwen25_0p5b | Qwen/Qwen2.5-0.5B-Instruct | ok | done | 958/958 | 1622/1622 | 1451/1451 |
| qwen25_1p5b | Qwen/Qwen2.5-1.5B-Instruct | ok | done | 958/958 | 1622/1622 | 1451/1451 |
| qwen25_3b | Qwen/Qwen2.5-3B-Instruct | ok | done | 958/958 | 1622/1622 | 1451/1451 |
| qwen25_14b | Qwen/Qwen2.5-14B-Instruct | ok | done | 958/958 | 1622/1622 | 1451/1451 |
| qwen25_32b | Qwen/Qwen2.5-32B-Instruct | - | - | 0/958 | 0/1622 | 0/1451 |
| medgemma_27b | google/medgemma-27b-text-it | ok | done | 958/958 | 0/1622 | 1451/1451 |
| baichuan_m2_32b | baichuan-inc/Baichuan-M2-32B | ok | done | 958/958 | 0/1622 | 1451/1451 |

Rerun a failed task: `sbatch --array=<i> jobs/journal3/jr3_FT.sbatch` or `jobs/journal3/jr3_JG.sbatch` (resumes by instance_id), then `sbatch jobs/journal3/jr3_final.sbatch`. `MEDVERIF_J3_FORCE=<stage>|all` ignores a marker.
