# Batch Oct status (HPC)

Updated: **2026-09-30 ~15:50 UTC+7** · Freeze **Oct 5 23:59** (no extension)

## M1-strong / Oct batch (this thread)

| Step | Status |
|------|--------|
| **Amendment 1** | **`8fe6441`** pushed (`notes/m1_prereg_amendment1.md`) |
| **Gate code** | `src/m1_gate.py` + `m1_lib.py` (`parse_decimal` fix); script commit pending push |
| **M1-strong run** | `sbatch jobs/run_m1_strong.sbatch` → `results/tables/m1_strong.md` + `results/cache/m1_strong_gate.json` |
| **T17 down10 CPU** | Lane B pack **588** rows / **218** E1-down10 already in `results/raw/lane_b/t17_downdose/` (6 checkers + Bespoke) |
| **Parallel** | `jobs/run_batch_oct_parallel.sh` → repair, T9 nat3, **T24** (`qc/t24_review.csv`) |
| **T24 ETA** | ~1.5h Slurm after submit (skeleton CSV immediate; full BM25+OR when script extended) |

## Active Slurm

| Job | Role | Node | Notes |
|-----|------|------|--------|
| **61555** | T15 AggreFact **base** | node002 | Target 29 320 rows |
| **61549** | T15 AggreFact **ft** | node002 | Same node → shared GPU |
| **61554** | T15 pack ft MiniCheck | — | **DONE** |

## Scoring / analysis

| Track | Status |
|-------|--------|
| **Score lock** | Per **(verifier, pack)** under `jobs/locks/score_{verifier}__{pack}.lock` (`MEDVERIF_GPU_GLOBAL_SCORE_LOCK=pack`) |
| **main_ext OR** | v1 **380/380**; v4 in progress · **356 valid** at analysis (`scripts/main_ext_scoring_report.py`) |
| **main_ext CPU** | `main_ext_score_checkers.py` started in parallel with OR |
| **T18 OR** | `jobs/run_t18_or_only.sh` ($2) parallel with main_ext |
| **T18 CPU/GPU** | Full `run_t18_score_hpc.sh` continues CPU; Bespoke → **node004** after **61555** |
| **T17 filters** | Revert done: **540** valid; retro guard **−6** (`notes/pi_review_filter_manifest.json`) |
| **T18 pack** | **331** scorable + **6** INV appendix (`notes/t18_scoring_manifest.json`, commit `5a80a3f`) |
| **T20** | 194 drugs; fetch labels → **≥100**; steps 3–4 CPU (`notes/t20_report.md`, no wild CSV) |
| **T22** | GPU **RewardBench** RMs (InternLM2 7B/1.8B, FsfairX-Llama3) → `results/raw/t22/`; manifest `notes/t22_reward_models.json` |
| **T23** | Reasoning OR **$5** cap → `results/raw/t23/` |
| **T15 report** | `watch_t15_aggrefact_report.sh` after **61555+61549** |

## OR account

- OpenRouter **usage_daily** tracked; pack caps: main_ext **$2**, T18 **$2**, T23 **$5**

## Not in freeze scope if incomplete

- Full T15 29k AggreFact (parallel track)
- T20 wild PI review pack (explicitly dropped)
