# T4 ecological answer classifier (rule-based)

Fixed category precedence (first match wins):

1. **`changed_value`** — answer dose ≠ target (same unit, different amount, or wrong dose after unit check)
2. **`frequency_rephrased`** — dose matches; frequency wording differs (e.g. q6h ↔ every 6 hours)
3. **`exact_surface_variant`** — dose matches; surface form differs (spacing, words vs abbreviations, `200mg` ↔ `200 mg`)
4. **`exact_verbatim`** — dose string appears verbatim in evidence (with target span)

## Before labeling `changed_value`

If the answer’s dose **number appears elsewhere in the evidence** but does **not** match the task target → classify as **`omitted`** (target mismatch / wrong anchor), not `changed_value`.

## Surface form

- **`Nmg` without a space** (and similar digit+unit glue) → **`exact_surface_variant`**, not verbatim.

## Human labels

PI sheets (`eco_PI_ok_labels.csv`, `eco2_PI_ok_labels.csv`) override classifier output via `correct_category` / `PI_ok`.
