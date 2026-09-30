# M1-strong pre-registration amendment 5

**After:** amendment 4 · **Found:** Oct 1 2026, **after** the final results (`m1_strong_final`, `8939e6c`) had been seen. **Primary criterion text is unchanged** (verbatim in `notes/m1_preregistration.md`). The paper reports the corrected table and mentions this amendment.

## 1. Bug fix: after-M1 texts did not follow the amendment-4 spec

**Issue.** Amendment 4 fixes the M1 canonical forms: mass→mg, volume→mL, mass/mass→mg/kg, rate suffixes kept. The regex that rewrote checker inputs (`text_utils.DOSE_RE`, used by `src/quantity_norm.py` at `8939e6c`) had no plain `mcg/kg`, `µg/kg`, `g/kg`, `L` or comma-grouped numerals, so those spans reached the checkers unchanged. The gate canonicalized the same spans correctly, so the rows passed the gate without their text having been normalized.

**Provenance** (`scripts/m1_provenance_check.py`, `notes/m1_provenance.md`). Two normalizers produced the texts behind `m1_strong_final`:

| Pack | Built with | Reproduced byte-for-byte |
| --- | --- | --- |
| US_up after, local checkers (`data/lane_b/m1_t7_e1_unit.jsonl`) | `text_utils.DOSE_RE` at `8939e6c` | 214/214 (node30 normalizer: 204/214) |
| US_up after, API judges (`data/t7/instances_e1_unit_m1_pending.jsonl`) | node30 normalizer | 230/230 E1-unit rows |
| US_down after (`data/lane_b/m1_t17_unit_down.jsonl`) | either (identical output) | 150/150 |
| T1 raw_m1 (`data/v3/instances_m1_pending_node30.jsonl`, not in M1-strong) | node30 normalizer | 942/942 |

The node30 normalizer was never committed; it is recovered from the stash "pre node30-results merge" and committed as `quantity_norm.M1_DOSE_RE_NODE30` (`87087da`).

**Off-spec scored rows** (scored text ≠ spec M1 of the source): US_up local 46 rows (23 bases), US_up API 38 rows (19 bases), US_down 0. NS packs are scored without M1 by design (verified: 10/10 RoBERTa scores reproduced with `MEDVERIF_M1=0`).

**Fix.** `quantity_norm.M1_DOSE_RE_SPEC` (default `M1_DOSE_RE`, `ae8ce5d`): every mass, volume, mass/kg and volume/kg dose with optional `/min|/day|/dose|/h|/hr|/d` is rewritten; concentrations (mg/dL, mcg/mL) stay out of scope as in amendment 4. Only the off-spec rows are rebuilt and rescored.

## 2. Gate: M1-lib was not independent of M1

**Issue.** `src/m1_lib.py` gave both gate sides the same function (`_canonical_for_gate`, built on `quantity_norm.canonicalize_dose_span` and `text_utils.DOSE_RE`), so "M1 ∩ M1-lib" could never disagree and the "independent normalizer" claim did not hold.

**Fix.** `src/m1_lib_indep.py`: quantulum3 extraction + pint conversion, no imports from this repo; its only surface rewrite is µg/μg→mcg (quantulum3 has no micro-sign entry), counted per pack. Gate = every edited target span parses under M1 (spec) and M1-lib-indep to the same quantity.

**Result** (`scripts/m1_gate_independent.py`, `notes/m1_gate_independent.md`): all 1,546 edited target spans across the six packs agree (0 differ, 0 M1-lib failures, 0 M1 failures; 74 spans use the micro-sign rewrite). Instance gate and base cohort unchanged (110 bases), so no rescoring follows from the gate change.

## 3. Corrected table

Rescored rows and every changed `m1_strong_final` cell (old → new): see `notes/m1_strong_amend5_changes.md`.
