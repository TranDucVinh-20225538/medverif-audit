# OpenRouter priority (429 handling)

1. **V1 / V4** — never pause mid-run; do not change V4 provider/model mid-run.
2. **T1 M1 re-score (V1/V4 → `results/raw_m1/`)** — high priority after V1/V4 main catch-up; inflight ≤2.
3. **T2 full (v1b + v5)** — approved (`notes/t2_full_approved`); pause before expand on 429.
4. **Expansion Stage-1** — pause first on sustained 429 (`touch notes/pause_expand_openrouter`).
5. **T3 INV-family T2 scores** — when `data/t3/instances_inv_families.jsonl` is non-empty.
6. **T6-B zoo** — pilot then full; cap **$10**; pause via `notes/pause_t6_openrouter`; inflight **1**.
7. **G** — stopped.

Inflight caps: V4 (existing), V1 `MEDVERIF_OR_MAX_INFLIGHT=4`, T1 M1 / T2 / T3 `=2`.

Credit floor: `MEDVERIF_OR_MIN_CREDIT=2` → stop and report.
