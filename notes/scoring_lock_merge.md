# scoring_lock merge (HPC ↔ node30)

- **HPC:** `src/scoring_lock.py` — per-`(verifier, out)` flock under `.cache/score_locks/`.
- **node30:** same module also acquires `jobs/locks/gpu0_scoring.lock` when `MEDVERIF_GPU_GLOBAL_SCORE_LOCK` is not disabled (default **on**).

When merging branches, **do not replace** one side’s file wholesale. Keep:

1. node30’s `gpu0_scoring.lock` path and any node30-only helpers.
2. HPC’s hashed per-output locks (required for parallel OpenRouter / multi-out scoring).

Disable global GPU lock only for debugging: `MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0`.
