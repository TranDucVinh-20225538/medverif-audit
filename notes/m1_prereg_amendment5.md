# M1-strong pre-registration amendment 5

**After:** amendment 4 · **Found:** Oct 1 2026.

## Summary

- **The M1 spec was fixed in amendment 4** (`notes/m1_prereg_amendment4.md`): mass→mg, volume→mL, mass/mass→mg/kg, rate suffixes kept; concentrations out of scope.
- **84 scored after-M1 texts did not follow that spec**: 46 rows (23 bases) in US_up for the local checkers and 38 rows (19 bases) in US_up for the API judges. US_down: 0. NS packs are scored without M1 by design.
- **The fix was made after the results had been seen** (`m1_strong_final`, `8939e6c`).
- **The criterion is unchanged** (verbatim in `notes/m1_preregistration.md`).
- **Both results are reported**: pre-amendment-5 `results/tables/m1_strong_final.md` (kept untouched) and amendment 5 `results/tables/m1_strong_final_amend5.md`. The paper reports the amendment-5 table and mentions this amendment. Side by side: `notes/m1_strong_amend5_side_by_side.md`. Cell-level change list: `notes/m1_strong_amend5_changes.md`.

## 1. Bug fix: after-M1 texts did not follow the amendment-4 spec

**Issue.** The regex that rewrote checker inputs (`text_utils.DOSE_RE`, used by `src/quantity_norm.py` at `8939e6c`) had no plain `mcg/kg`, `µg/kg`, `g/kg`, `L` or comma-grouped numerals, so those spans reached the checkers unchanged. The gate canonicalized the same spans correctly, so these rows passed the gate even though their text had not been normalized.

**Provenance** (`scripts/m1_provenance_check.py`, `notes/m1_provenance.md`). Two normalizers produced the texts behind `m1_strong_final`:

| Pack | Built with | Reproduced byte-for-byte |
| --- | --- | --- |
| US_up after, local checkers (`data/lane_b/m1_t7_e1_unit.jsonl`) | `text_utils.DOSE_RE` at `8939e6c` | 214/214 (node30 normalizer: 204/214) |
| US_up after, API judges (`data/t7/instances_e1_unit_m1_pending.jsonl`) | node30 normalizer | 230/230 E1-unit rows |
| US_down after (`data/lane_b/m1_t17_unit_down.jsonl`) | either (identical output) | 150/150 |
| T1 raw_m1 (`data/v3/instances_m1_pending_node30.jsonl`, not in M1-strong) | node30 normalizer | 942/942 |

The node30 normalizer was never committed. It is recovered from the stash "pre node30-results merge" and committed as `quantity_norm.M1_DOSE_RE_NODE30` (`87087da`).

**Off-spec scored rows** (scored text ≠ spec M1 of the source): US_up local 46, US_up API 38, US_down 0; total 84. For the NS packs, 10/10 RoBERTa scores were reproduced with `MEDVERIF_M1=0`.

**Fix.** `quantity_norm.M1_DOSE_RE_SPEC` (default `M1_DOSE_RE`, `ae8ce5d`) rewrites every mass, volume, mass/kg and volume/kg dose with an optional `/min|/day|/dose|/h|/hr|/d` suffix. Only the 84 off-spec rows were rebuilt (`scripts/m1_amend5_build.py`) and rescored (job 61850; same envs as the originals: cpuverif for local checkers, vllm for Bespoke, API for the judges).

**T1 raw_m1 (superseded, not rescored).** `results/raw_m1/` T1 rows built with the node30 normalizer include 38 off-spec rows. T1 is not in the paper, so these rows are marked superseded and not rescored. `results/raw_m1/v1_medscore.jsonl` is also not read by any paper loader. It was the source of the earlier MedScore polarity E2 n=25 (11 current + 14 raw_m1 rows; reproduced 21/25). The correct value is n=11 (8/11).

## 2. Gate: M1-lib was not independent of M1

**Issue.** `src/m1_lib.py` gave both gate sides the same function (`_canonical_for_gate`, built on `quantity_norm.canonicalize_dose_span` and `text_utils.DOSE_RE`), so "M1 ∩ M1-lib" could never disagree and the "independent normalizer" claim did not hold.

**Fix.** `src/m1_lib_indep.py` uses quantulum3 for extraction and pint for conversion, with no imports from this repo. Its only surface rewrite is µg/μg→mcg (quantulum3 has no micro-sign entry), counted per pack. Gate = every edited target span parses under M1 (spec) and M1-lib-indep to the same quantity.

**Result** (`scripts/m1_gate_independent.py`, `notes/m1_gate_independent.md`): all 1,546 edited target spans across the six packs agree (0 differ, 0 M1-lib failures, 0 M1 failures; 74 spans use the micro-sign rewrite). Instance gate and base cohort are unchanged (110 bases), so no rescoring follows from the gate change.

## 3. Effect on the criterion

Small checkers binding overall: 1/8 pre-amendment-5 (Granite) → 5/8 at amendment 5 (RoBERTa, AlignScore-large, SummaC-ZS, Granite, Bespoke). DeBERTa, Flan-T5 and AlignScore-base still fail on the EVID side of US_up. API judges (Mistral, Llama) bind in both versions. US_down is unchanged except for DeBERTa, whose values move only because of the approved cpuverif swap (one row fewer).
