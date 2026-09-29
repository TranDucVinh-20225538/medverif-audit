# Batch Oct status (HPC)

Updated: 2026-09-29 (UTC+7)

## Gates

| Item | Status |
|------|--------|
| H0–H2 | Not tracked in-repo; T19 scaffold ready (P1, local GPU). |
| H3–H4 | — |
| T14 OR scoring | Background `run_t14_score_openrouter.sh` (check `/tmp/t14_or_score.log`). |
| T15 step 1 | Builder fixed (`span_start_in_sentence`); re-run `scripts/t15_build_training_data.py` (long CPU). |
| T17 pack | Missing (`data/v3/t17_downdose.jsonl`); T19 runs without T17 until built. |

## T19 scale sweep (P1)

- **Pack:** `data/t19/instances_t19.jsonl` (n=1060: main DOSE + E1-unit + T14; non-dose excluded).
- **Local models (1 GPU, serial):** Llama-3.2-1B/3B/3.1-8B Instruct via `jobs/run_t19_scale_sweep.sh`.
- **70B:** existing `results/raw/v4_ragas_nli.llama.jsonl` + `results/raw/t14/v4_ragas_nli.jsonl` (no rerun).
- **Outputs:** `notes/t19_scale_sweep.md`, `results/figures/t19_scale.png`.
- **Slurm:** `squeue` empty before submit; flock `t19_<slug>`; no duplicate `t19-*` job names.

## GPU

- Partition: `defq`, 1×GPU/job, ~4 GPUs/user (vip4 when available).
