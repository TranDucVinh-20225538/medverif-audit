# Batch Oct status (HPC)

Updated: 2026-09-29 22:10 (UTC+7)

## Parallel lanes (kicked off)

| Lane | Flock | Log | Cap | Status |
|------|-------|-----|-----|--------|
| **B** CPU T6-A | `lane_b_cpuverif` | `jobs/logs/lane_b_cpuverif_*.log` | — | Running: 200 calib → agreement vs `results/raw_node30` → main E1-evid (`data/lane_b/main_e1_evid.jsonl`, n≈245) |
| **C** M1 H2 OR | `lane_c_m1_h2` | `jobs/logs/lane_c_m1_h2_*.log` | **$3** lane / **$10** night (`scripts/lane_or_night_budget.py`) | Running: V1/V1b/V1c/V4/V5/V6×4 → `results/raw_m1/lane_c/` |
| **A** packs | `lane_a_generation` | `jobs/logs/lane_a_generation_*.log` | **$2** (`notes/lane_a_spend.json`) | Running: smoke 5+5 → main_ext + IAA + T18 (no scoring) |

**OR chain (unchanged):** `jobs/run_or_resume_priority.sh` — main backfill → T17 → T14 → v4 unparsed.

**GPU (max 2 ours):** T19 3B **61477**, T15 **61476**. Bespoke-7B deferred until GPU free.

## T19 scale

- Cohort **1703** (+80 `main_pol`); **1B** done (1623); **3B** finishing 1623 then resume **80 POL**; **8B** on full 1703 after 3B.
- Report script: `scripts/t19_report.py` (notes after 3B/8B complete).

## T17 V4 Llama

- **612/612** → `results/raw/t17/v4_ragas_nli.llama.jsonl` (all `meta-llama/llama-3.3-70b-instruct`).

## Git

- Latest pushed: `a5a952e` (T17 rename + T19 POL cohort); `26538db` (T19 report).

<!-- job-elapsed-table -->

## Job wall times (auto)

| JobID | Name | Pack / task | Verifier | Rows | Wall | GPU | State |
|------:|------|-------------|----------|-----:|------|-----|-------|
| 61477 | t19-llama32_3b | T19 | local RAGAS | — | — | 1 | RUNNING |
| 61476 | t15-train | T15 | MiniCheck FT | — | — | 1 | RUNNING |
