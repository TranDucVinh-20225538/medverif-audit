# RD2 amendment 2 — 2–3 pharmacist raters, majority rule, rating rules

- Written: 2026-10-14 (ICT, UTC+7), before any rater file was sent. **No rating of any RD2 answer has been returned or seen.**
- Changes amendment 1 sections 4 (P1 / order) and 5 (second rater) only; selection, strata, weights and estimators of
  amendment 1 section 3 are unchanged. Sheet v2 (`results/journal5/rd2/amend1/rd2_adjudication_sheet_v2.csv`,
  sha256 `f573bfd617685fd066fc1e6e6a28c7821a9c293e644b9fc2a8927e87af041891`) is unchanged.
- Code: `scripts/journal5/rd2_rater_files.py` (new). Outputs: `results/journal5/rd2/amend2/`.

## 1. Raters and assignment

DS1 = primary rater (licensed clinical pharmacist); DS2 and optionally DS3 = additional licensed pharmacists, rating
independently (no discussion of individual rows, no AI tool used to decide a rating; prereg section 5).

Assignment (seed 20261014, `rater_assignment.csv`):
- **P1** (RD2V2-0001…0200): DS1 rates all 200.
- **Overlap** (the 50 overlap rows inside P1 fixed in amendment 1, seed 20261005): rated by DS1, DS2 and DS3 (if present);
  DS2 and DS3 get them in different random orders.
- **Rest** (2,273 rows): dealt stratified by sampling stratum into three shares S1 (758) → DS1, S2 (758) → DS2, S3 (757) → DS3.
  If DS3 does not take part, S3 is pre-split (stratified) into S3a (379) → DS1 and S3b (378) → DS2.
- Workload: with 3 raters DS1 958, DS2 808, DS3 807 rows; with 2 raters DS1 1,337, DS2 1,186 rows.
- Order in each file: batch 1 (DS1: P1; DS2/DS3: the 50 overlap rows) before batch 2 (the share).
- Whether DS3 takes part is recorded as a dated line in `prereg/rd2_amendments.md` before any rating is returned. If DS3
  stops part-way, the S3 rows DS3 has not rated go to DS1 (S3a rows) and DS2 (S3b rows); rows DS3 completed stay DS3's.

Files (blinded: row_id, batch, question, label excerpt, answer, the pre-registered rating columns, and a "Huong dan" sheet
with the rules of section 3; no generator, condition, automatic class, checker verdict, basis flag, stratum or source):
`RD2_DS1.xlsx`, `RD2_DS2.xlsx`, `RD2_DS3.xlsx`, `RD2_DS1_them_neu_khong_co_DS3.xlsx`, `RD2_DS2_them_neu_khong_co_DS3.xlsx`
(sha256 in `rater_manifest.json`; the committed bytes are the ones sent). The earlier draft
`amend1/RD2_P1_bang_cham.xlsx` is superseded and not sent.

## 2. Primary label per row

- Rows rated by one rater: that rater's label.
- Overlap rows with 3 raters: **majority**. Answer (Y / N / unclear): the value given by ≥ 2 raters; if all three differ,
  DS1's. Error type: the type given by ≥ 2 of the raters in the answer majority; if they differ, DS1's type when DS1 is in the
  majority, otherwise DS2's.
- Overlap rows with 2 raters: DS1's label (as amendment 1). Disagreements are reported, never overwritten.

Definitions are those of prereg section 5: natural unit/basis error = Y with type unit or basis; non-error = N; unclear and
other types are excluded from both sets and counted.

## 3. Rating rules given to all raters (fixed before any rating)

1. Compare only with the label excerpt shown; rate only the dose given for the `[DOSE]` slot.
2. Equivalent notation is correct (52 mg/m² = 52 mg/m2; 0.5 g = 500 mg).
3. A dose that is correct for a different population or indication than the `[DOSE]` slot → Y + other_population_or_indication.
4. Correct number, unit and basis but **missing** frequency/duration → N + none; Y + time only when frequency/duration is wrong.
5. Several doses in the answer: rate the primary dose given for `[DOSE]`; secondary doses (e.g. for another group) are ignored.
   If the primary dose is a range: range equal to the label → N; range containing a dose that is wrong for the label → Y, with
   a note.
6. No dose given (refusal, "ask your doctor") → unclear, note "không có liều".
7. Cannot be decided (truncated label, ambiguous answer) → unclear with the reason in the note.

## 4. Agreement and rater analyses

- Overlap rows: percent agreement and Cohen's κ for each rater pair, and Fleiss' κ when 3 raters, on Y vs N (unclear
  excluded and counted) and, as sensitivity, on Y / N / unclear; κ on the derived three-way outcome (natural unit/basis error /
  non-error / other) for the primary comparison sets. 95% CIs by question-clustered bootstrap (10,000 resamples, seed 20261002).
- Rater sensitivity: because the rest is split at random within strata, the confirmed-error rate per stratum is reported by
  rater share; the primary estimates are repeated excluding each additional rater's share in turn.

## 5. Stopping

Unchanged in substance: the P1 analysis (amendment 1, P1 weights) is run once DS1 has finished P1, with agreement statistics
from whatever overlap ratings exist at that time reported as interim; the full analysis is run once all shares are rated.
No assignment or stopping decision depends on any rating.
