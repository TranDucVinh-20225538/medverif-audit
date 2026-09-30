# T20–T23 gate (updated 2026-09-30)

**Freeze target: Oct 5** (unchanged).

## Decoupled from T15 (Decision **N**)

- **Audit zip (#6)** and **T20 / T22 / T23** do **not** wait for full T15 AggreFact 29k eval.
- T15 scores may be appended to a later audit snapshot revision.
- **T15** tracks separately: GPU full eval **or** 3k stratified subsample + bootstrap CI (`notes/t15_report.md`).

## Prerequisites to **open T20 steps 1–4, T22, T23**

| # | Item | Status |
|---|------|--------|
| 1 | Lane C v6 (854× judges) | **DONE** |
| 2 | Bespoke Lane B (valid packs) | **DONE** |
| 3 | T16 + report | **DONE** |
| 4 | H7 prompt×model | **DONE** |
| 5 | `canonical_sources.tsv` + `audit_snapshot.zip` | **DONE** (2026-09-30) |
| 6 | T15 AggreFact report | **PARALLEL** (not blocking) |

## Open now

- **T20** steps 1–4 (wild pack build + review CSV; **no** verifier scoring until PI returns review).
- **T21** steps 1–4 (same pattern).
- **T22** GPU verifiers (after Bespoke cal — already passed).
- **T23** OR cap **$5** (total T20–23 OR **$12**).

## Still blocked

- **main_ext / T18** instance scoring until PI returns **FINAL** review CSVs (`release/pi_final_review_packs.zip`).
- **T20 wild / T21** scoring until PI review CSVs returned.

## Caps

Total OR **$12** for T20–T23; T20 wild **$2**, T21 **$3**, T23 **$5**. Frozen: `data/v3/instances_main*`.
