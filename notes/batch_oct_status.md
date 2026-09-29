# Batch Oct status (HPC)

Updated: 2026-09-29 17:12 (UTC+7)

## Gates

| Item | Status |
|------|--------|
| H0–H2 | Not tracked in-repo; T19 scaffold ready (P1, local GPU). |
| H3–H4 | — |
| T14 OR scoring | Background `run_t14_score_openrouter.sh` (check `/tmp/t14_or_score.log`). |
| **medverif-v3** | **HELD** (`notes/HOLD_medverif_v3`); 61441 cancelled — confirm before resubmit. |
| Data integrity | `notes/integrity_check_2026-09-29.md`; hooks: shrink guard on `data/` + `results/raw/`. |
| T15 step 1 | Builder fixed (`span_start_in_sentence`); re-run `scripts/t15_build_training_data.py` (long CPU). |
| T17 pack | Missing (`data/v3/t17_downdose.jsonl`); T19 runs without T17 until built. |

## T19 scale sweep (P1)

- **Pack:** `data/t19/instances_t19.jsonl` (n=1060: main DOSE + E1-unit + T14; non-dose excluded).
- **Local models (1 GPU, serial):** Llama-3.2-1B/3B/3.1-8B Instruct via `jobs/run_t19_scale_sweep.sh`.
- **70B:** existing `results/raw/v4_ragas_nli.llama.jsonl` + `results/raw/t14/v4_ragas_nli.jsonl` (no rerun).
- **Outputs:** `notes/t19_scale_sweep.md`, `results/figures/t19_scale.png`.
- **Slurm:** flock `t19_<slug>`; chain via `jobs/run_t19_submit_chain.sh`.
- **Blocker:** Meta Llama weights not in `HF_HOME` — accept HF license + run `scripts/t19_prefetch_models.sh` on login node (`notes/t19_llama_hf_gate.md`). Job 61439 cancelled (stuck load, 0 rows).
- **61439 fix:** `HF_HUB_OFFLINE=1`, progress flush every 20 rows in `scripts/t19_score_jsonl.py`.

## GPU

- Partition: `defq`, 1×GPU/job, ~4 GPUs/user (vip4 when available).

<!-- job-elapsed-table -->

## Job wall times (auto)

| JobID | Name | Pack / task | Verifier | Rows | Wall | GPU | State |
|------:|------|-------------|----------|-----:|------|-----|-------|
| 61411 | t3rep-U2-A2 | — | — |  | 00:00:00 | — | CANCELLED |
| 61412 | t3rep-U3-A2 | — | — |  | 00:00:00 | — | CANCELLED |
| 61413 | t3rep-U2-A3 | — | — |  | 00:00:00 | — | CANCELLED |
| 61414 | t3rep-U3-A3 | — | — |  | 00:00:00 | — | CANCELLED |
| 61415 | t3rep-U2-A4 | — | — |  | 00:00:00 | — | CANCELLED |
| 61416 | t3rep-U3-A4 | — | — |  | 00:00:00 | — | CANCELLED |
| 61417 | t3rep-U2-A5 | — | — |  | 00:00:00 | — | CANCELLED |
| 61418 | t3rep-U3-A5 | — | — |  | 00:00:00 | — | CANCELLED |
| 61419 | t3rep-U2-A6 | — | — |  | 00:00:00 | — | CANCELLED |
| 61420 | t3rep-U3-A6 | — | — |  | 00:00:00 | — | CANCELLED |
| 61421 | t3rep-U1-A5 | — | — |  | 00:00:00 | — | CANCELLED |
| 61422 | t3rep-U1-A2 | — | — |  | 00:00:00 | — | CANCELLED |

