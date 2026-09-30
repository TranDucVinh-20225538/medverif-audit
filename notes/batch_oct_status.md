# Batch Oct status (HPC)

Updated: 2026-09-30 10:26 (UTC+7)

## Today's six (before T20–T23)

| # | Item | Status |
|---|------|--------|
| 1 | **Lane C** v6 Llama + Mistral | **RUNNING** — gpt4o + haiku **854/854**; llama **~136/854** (`lane_c_resume_*` log) |
| 2 | **Bespoke** GPU | **RUNNING** — Slurm **61514** (node002); `v2b_bespoke` module fixed |
| 3 | **T15** | **RUNNING** — base AggreFact **~14372/29320** (deduped); report when eval completes |
| 4 | **T16** | **RUNNING** — 226 instances built; full attribution CPU job |
| 5 | **H7** pxm | **RUNNING** — gpt4o **224/232**; Sonnet leg resumed |
| 6 | **audit zip** | **PENDING** — after 1–5: `build_canonical_sources.py` + `build_audit_snapshot.py` |

**OR (30/9):** night baseline **reset** → **$10** total, Lane C **$3** (`lane_or_night_budget.py`).

**Decision M:** SummaC-Conv + HHEM excluded from new packs; see `notes/decision-log.md`.

**Held:** main_ext + T18 scoring until PI review (unchanged).

**T20–T23:** gated — `notes/t20_t23_gate.md` (start after six above; OR cap **$12** total for T20–23).

**Git:** pushed through latest `feat(30sep)` commit on `master`.

<!-- job-elapsed-table -->
