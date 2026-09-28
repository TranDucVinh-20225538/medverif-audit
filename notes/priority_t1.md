# T1 priority (2026-09-29)

PI raised **T1 (M1 + M2 hybrid)** above expansion.

## Deliverables

- `results/tables/cost_vs_validity.md` — $/1k claims, paper AggreFact BAcc, our invariance/sensitivity (raw, M1 infer, M1+M2 hybrid).
- `results/raw_m1/` — V1/V4/V2a/V3 re-scored with `MEDVERIF_M1=1`.

## Jobs

| Job | Command |
| --- | --- |
| M1 OR (V1+V4) | `jobs/run_t1_m1_rescore_openrouter.sh` (tmux `t1_m1_or`) |
| M1 CPU (V2a+V3 pending) | `jobs/run_t1_m1_rescore_cpu.sh` (tmux `t1_m1_cpu` or node30) |
| Report refresh | `python3 scripts/t1_cost_validity_report.py` |

## Node30

V2/V3 M1 pending: `data/v3/instances_m1_pending_node30.jsonl` (from `scripts/build_m1_pending_node30.py`; scores → `results/raw_m1/`).
