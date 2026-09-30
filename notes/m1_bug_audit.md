# M1-strong gate bug impact audit (P0)

**Bug:** `m1_canonical_mg_for_surface` (`dd98330`) used `parse_decimal` without import; bare `except Exception` → `None` → **false M1 gate failure** on every dose-matching edited span.

**`git log -S parse_decimal` (src/scripts/analysis):** hits in `quantity_norm.py` (correct import, shared M1 rewriter), T20/T18 scripts, and **`dd98330`** (gate helper only).

## Shared M1 normalizer

| Module | Uses `parse_decimal`? | Affected by gate bug? |
|--------|----------------------|------------------------|
| `src/quantity_norm.py` | Yes (imported from `text_utils`) | **No** |
| `m1_lib.m1_canonical_mg_for_surface` | Missing until fix | **Yes** (gate-only) |

## Results artifacts

| Path | Role | Superseded? | Spans falsely failed under bug |
|------|------|-------------|--------------------------------|
| `results/raw_m1/*` | M1 text rewrite at score time (`normalize_quantities`) | **No** | 0 (different code path) |
| `results/raw/lane_b/m1_t7_e1_unit/*` | Same | **No** | 0 |
| `results/tables/m1_strong.md` | Gate + causal table | **SUPERSEDED** if from pre-fix run | all gated spans (see below) |
| `notes/m1_strong_report.{md,json}` | Step 1–2 report | **SUPERSEDED** | same |
| `results/cache/m1_strong_gate.json` | Gate cache (job 61572 partial) | **SUPERSEDED** when re-run with fix + amendment 2 | same |

## False M1 failures (dose-regex edited target spans)

Under the bug, **every** edited target span matching `DOSE_RE` was treated as M1-fail (lib could still pass → **intersection ≈ 0**).

| Pack | n spans (dose-regex on edited targets) |
|------|----------------------------------------:|
| us_up_x1000 | 93 |
| ns_x10_claim | 105 |
| ns_x10_evid | 105 |
| ns_div10 | 97 |
| **Total unique evaluations** | **400** |

Machine-readable: `notes/m1_bug_audit.json`.

**No non-NA M1-strong binding table was accepted before fix** (amendment 2, pre–61572 completion).
