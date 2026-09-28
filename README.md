# medverif-audit

Pilot: clinical counterfactual audit of medical RAG faithfulness verifiers (E1 / E2 / INV).

Stage 0 is recorded in `notes/environment.md` and `REPORT.md`. Stages 1–5 are not started. No results have been computed.

## Layout

- `notes/environment.md` — what was actually found (models, commits, licenses, deviations)
- `REPORT.md` — one entry per stage
- `configs/` — verifier and stage configs (added when a stage runs)
- `data/` — `base_pairs.jsonl`, `instances.jsonl`
- `src/` — pair builder, perturbations, verifier wrappers
- `jobs/` — SLURM `sbatch` scripts
- `results/raw/`, `results/tables/`, `results/figures/`
- `qc/qc_samples.md` — hand-check sample, written in Stage 2
- `analysis/analyze.py` — written in Stage 4

## Reproduce

Not end-to-end yet. GPU jobs must go through SLURM on partition `defq` (A100-80GB). Do not commit model weights or corpora.
