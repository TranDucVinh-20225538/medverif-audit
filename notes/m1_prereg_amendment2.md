# M1-strong pre-registration amendment 2

**After:** amendment 1 (`8fe6441`) · **Before:** any accepted **non-NA** M1-strong causal table.

## Bug fix — silent parse failures

**Issue:** `m1_canonical_mg_for_surface` (introduced `dd98330`) referenced `parse_decimal` without importing it; a bare `except Exception` returned `None`, forcing **M1 gate false negatives** on every dose-matching edited span.

**Fix:** Import `parse_decimal` from `text_utils`; replace silent swallow in M1 / M1-lib / gate paths with **counted** errors logged to `logs/m1_parse_errors.jsonl` (exception type + surface + pack). Runs **abort** if any pack’s error rate exceeds **5%** of spans.

**Impact audit:** `notes/m1_bug_audit.md` (shared `quantity_norm` M1 rewriter **not** affected).
