# T1 priority (2026-09-29)

PI raised **T1 (M1 + M2 hybrid)** above expansion.

## Deliverables

- `results/tables/cost_vs_validity.md` — $/1k claims, paper AggreFact BAcc, our invariance/sensitivity (raw, M1 infer, M1+M2 hybrid).
- `results/raw_m1/` — M1 scores: **HPC** V1/V4 (OpenRouter); **node30** V2a/V3 (CPU encoders).

## Jobs

| Where | Command |
| --- | --- |
| **HPC** M1 OR (V1+V4) | `jobs/run_t1_m1_rescore_openrouter.sh` (tmux `t1_m1_or`) |
| **node30** M1 V2/V3 | `jobs/run_t1_m1_score_node30.sh` |
| Report (HPC, after sync) | `python3 scripts/t1_cost_validity_report.py` |

Do **not** run `jobs/run_t1_m1_rescore_cpu.sh` on HPC (stub exits 2).

## Node30

Input: `data/v3/instances_m1_pending_node30.jsonl` (`scripts/build_m1_pending_node30.py`).

Output: `results/raw_m1/v2a_minicheck.jsonl`, `results/raw_m1/v3_alignscore.jsonl`.
