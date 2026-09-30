# M1-strong pre-registration amendment 4

**After:** amendment 2 · **Before:** any **binding** M1-strong causal table with refreshed gate under fixed M1-lib.

**Discovered:** Draft run **`be27e05`** (job 61599) and partial table **61606** (`--skip-legacy`) showed ~**23%** `m1_lib.pint` parse errors on **us_up** (and similar on NS packs): M1-lib forced **flat mg** via pint on **mg/kg**, **mL/L**, and other non–mass-only units. That inflated M1-lib-only failures and triggered the amendment-2 **5%** guard.

## Bug fix (M1-lib gate canonicalization)

**Issue:** `lib_canonical_mg_for_surface` / `_to_mg_string` converted every span to **milligrams**, so mass-per-weight and volume doses did not match M1’s `quantity_norm` canonical forms (mg, mL, mg/kg, … with **/day**, **/dose** suffixes preserved).

**Fix:** M1-lib gate matching uses the same **`canonicalize_dose_span`** as M1 (`src/quantity_norm.py`): mass→**mg**, volume→**mL**, mass/mass→**mg/kg**, rate suffixes unchanged.

**Impact:** Gate intersection and parse-error guard counts change; **primary criterion text is unchanged** (verbatim in `notes/m1_preregistration.md`).

## Reporting (dual cohort)

| Cohort | Label | Gate / M1-lib | Artifact |
| --- | --- | --- | --- |
| Pre-amendment-4 draft | `pre_amendment4` | Flat-mg pint path (61606) | `notes/m1_strong_report_pre_amendment4.json`, `results/tables/m1_strong_pre_amendment4.md` |
| Post-amendment-4 final | `post_amendment4_fixed_gate` | Dimension-aware lib + **`--refresh-gate`** | `notes/m1_strong_final.json`, `results/tables/m1_strong_final.md` |

Do **not** overwrite the pre-amendment-4 draft when generating the final table.
