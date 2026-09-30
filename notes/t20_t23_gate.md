# T20–T23 gate (2026-09-30)

**Do not start T20–T23 until today's six prerequisites are done.**

| # | Item | Status |
|---|------|--------|
| 1 | Lane C v6 Llama-8B + Mistral-Small (854 each) | IN PROGRESS (`v6_ragas_llama31_8b` partial) |
| 2 | Bespoke GPU (Lane B packs, no main_ext/T18) | IN PROGRESS (Slurm 61514) |
| 3 | T15 AggreFact + `notes/t15_report.md` | IN PROGRESS (~14k/29k base AggreFact) |
| 4 | T16 IG + `notes/t16_report.md` | IN PROGRESS (CPU job) |
| 5 | H7 prompt×model (232 rows) | IN PROGRESS (resume run) |
| 6 | `canonical_sources.tsv` + `audit_snapshot.zip` | PENDING (after 1–5) |

**T20–T23 caps (when started):** total OR **$12**; T20 wild **$2**, T21 **$3**, T23 **$5**. Frozen: `data/v3/instances_main*`.

**Order after gate:** T20 steps 1–4 ∥ T21 steps 1–4 → T22 (GPU, after Bespoke) → T23 → post-review scoring (T20 wild, T21, main_ext, T18).
