# Batch Oct status (HPC)

Updated: 2026-09-29 17:55 (UTC+7)

## Gates

| Item | Status |
|------|--------|
| Git `origin/master` | `8d7ad8e` (integrity `5ff57d5` + shrink `71d5389` + T17 `b80917e` + OR lock fix). |
| **medverif-v3** | **HOLD** (`notes/HOLD_medverif_v3`) — do not resubmit. |
| **T19** | **Blocked** until user says **HF approved** (`notes/t19_llama_hf_gate.md`). |
| H2 (M1 OR) | `jobs/run_t1_m1_rescore_openrouter.sh` queued after T17 (`/tmp/t1_m1_h2.log`). |
| Data integrity | `notes/integrity_check_2026-09-29.md`; shrink allow-list in `notes/allow_data_shrink.json`. |

## T14 OpenRouter (budget ≤ $3)

- **Pack:** n=233 (`data/t14/manifest_t14.json`).
- **Progress (rows / 233):** v1 **233**, v4 **233**, v1b **216**, v5 **128**, v6 judges **0** (resume after T17).
- **Spend:** **$0.85** / $3.00 (`scripts/t14_openrouter_budget.py`).
- **Report:** `results/tables/t14_c0_conditional_pass.md` (refreshed; partial until v1b/v5/v6 complete).
- **Runner:** `jobs/run_t14_score_openrouter.sh` (chain `/tmp/t14_h2_chain.log` after T17).
- **Fix:** `MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0` so OR jobs are not blocked by `gpu0_scoring.lock`.

## T17 down-dose (A1 done, A2 scoring)

- **Pack:** `data/v3/t17_downdose.jsonl` **n=612**; QC **`qc/t17_sample.csv`** (40 rows).
- **Scoring:** `jobs/run_t17_score_hpc.sh` → `results/raw/t17/` (budget ≤ **$5**).
- **Log:** `/tmp/t17_hpc_score.log`, `jobs/logs/t17_hpc_*.log`.

## T15 (fine-tune MiniCheck-RoBERTa-L)

- **Data:** commit **153429c** — `data/t15/` (2000 bases, train/dev), `disjointness_check.json` **overlap_total=0**.
- **Slurm:** job **61445** (`t15-train`, 1×GPU `defq`) — `jobs/run_t15_train.sbatch` → `scripts/t15_train.py` + `scripts/t15_eval.py`.
- **Submit:** `bash jobs/run_t15_submit.sh` (dedupes `t15-*` in squeue).
- **Outputs (when done):** `notes/t15_config.json`, checkpoint under `.cache/checkpoints/t15_roberta/best`, scores `results/raw/t15/`, draft `notes/t15_report.md`.
- **T18 eval:** runs when `data/t18/instances_t18.jsonl` exists; otherwise skipped in eval script.

## 70B QI (paper)

- **Use:** **76.5% QI, n_inv=51** (natural INV-unit | C0, non-dose, Llama-3.3-70B V4).
- **Not paper QI:** ~91% is **NS** (E1×10), not QI; see `notes/reconcile_llama70b_qi.md`.

## GPU

- Partition: `defq`; tmlr GPU yielded — reserve for **T19** after HF approval only.

<!-- job-elapsed-table -->

## Job wall times (auto)

| JobID | Name | Pack / task | Verifier | Rows | Wall | GPU | State |
|------:|------|-------------|----------|-----:|------|-----|-------|
| 61411 | t3rep-U2-A2 | — | — |  | 00:00:00 | — | CANCELLED |
| 61412 | t3rep-U3-A2 | — | — |  | 00:00:00 | — | CANCELLED |
| 61413 | t3rep-U2-A3 | — | — |  | 00:00:00 | — | CANCELLED |
| 61414 | t3rep-U3-A4 | — | — |  | 00:00:00 | — | CANCELLED |
| 61415 | t3rep-U2-A4 | — | — |  | 00:00:00 | — | CANCELLED |
| 61416 | t3rep-U3-A4 | — | — |  | 00:00:00 | — | CANCELLED |
| 61417 | t3rep-U2-A5 | — | — |  | 00:00:00 | — | CANCELLED |
| 61418 | t3rep-U3-A5 | — | — |  | 00:00:00 | — | CANCELLED |
| 61419 | t3rep-U2-A6 | — | — |  | 00:00:00 | — | CANCELLED |
| 61420 | t3rep-U3-A6 | — | — |  | 00:00:00 | — | CANCELLED |
| 61421 | t3rep-U1-A5 | — | — |  | 00:00:00 | — | CANCELLED |
| 61422 | t3rep-U1-A2 | — | — |  | 00:00:00 | — | CANCELLED |
