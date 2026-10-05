# RD2 amendment 1 — parser patch, no-dose rule, adjudication sheet v2, weighting, P1

- Written: 2026-10-05, 21:45 ICT (UTC+7), before the adjudication sheet was sent to anyone.
- **No pharmacist (human) label of any RD2 answer has been seen.** No rating exists yet; the key files were not opened
  (only their sha256 was computed).
- Seen before this amendment: the automatic (pre-registered extractor) labels, checker scores and the provisional report at
  commits 103be8a / 9d51786. Everything below therefore changes only the *selection, labelling of strata and analysis* of the
  human adjudication; it does not change any checker run, prompt, model or frozen file hash in `prereg/rd2_freeze.json`.
- Code: `scripts/journal5/rd2_relabel_v2.py`, `scripts/journal5/test_rd2_relabel_v2.py`, `scripts/journal5/rd2_sheet_v2.py`
  (new files; the frozen code is imported unchanged). Outputs: `results/journal5/rd2/amend1/`.
- Lock: this file is committed together with the sheet v2 and the outputs above; the commit hash is the commit that adds this
  file to `prereg/` (reported in `results/journal5/rd2/analysis/paper_numbers_rd2.json` under `amendment_commit`).

## 1. Parser patch (v2 automatic labels)

Problem: the frozen extractor (`src/unit_norm_fix.py`, `scripts/journal2/rd_extract.py`) does not read body-surface-area units
whose superscript was flattened in the label or answer text (`mg/m 2`, `grams per m 2`, `International Units/m 2`,
`mg per sq m`, `**400 mg** per m 2`). Such doses lose their per-m² basis on one side, which the frozen `classify` then calls a
unit or basis error although the doses agree.

Patch: a text-only pre-pass (`patch_m2`) rewrites these surface forms to `…/m2` / `per m2` in the answer, the label target
sentence, the label excerpt and the primary label dose, and then calls the frozen `classify` **unchanged**. The pattern requires a
dose-unit token immediately before `/` or a literal `per`, and `m` followed by `2`, `²` or `^2` not followed by another digit, so
lengths (`2 m`), codes (`M2`, `Baichuan-M2`), `/kg`, `m 25`, `per mL` and `m 3` are untouched (unit tests).

Unit tests (`scripts/journal5/test_rd2_relabel_v2.py`, 10 tests, all pass): all 33 identified m² artefacts (ifosfamide_0 ×11,
pegaspargase_0 ×10, ritonavir_1 ×7, temozolomide_1 ×5; 11 of them grounded) flip from a per-m² unit/basis error to a
non-unit-type class; ≥10 negative cases (12 strings that must not change, 5 genuine BSA errors that keep their class, and all
unpatched rows keep their v1 class); no new unit/basis error is introduced; 5,760 rows; no_dose 72 → 68.

Result (`results/journal5/rd2/amend1/relabel_diff.md`): 49 answers change class (33 m² artefacts, 12 other m² answers whose
label or answer had the same surface form, 4 recovered no-dose answers); unit + basis errors 459 (v1) → 426 (v2); every class
total for v1 and v2 is listed separately and each column sums to 5,760.

Known limitation (not fixed): about 5 suspected per-kg artefacts have a different cause — "kg" is separated from the dose number
(e.g. "5 to 10 mg of colistin base per kg", "500 mg to 1000 mg per kilogram", "1 gram per 10 kg") — and the three examples
inspected are wrong in value as well, so they would remain errors after any fix. They are left under the frozen parser and are
reported as a known limitation; the human adjudication covers them because all unit/basis errors are in the census.

Both label sets are analysed and reported; v1 (pre-registered) remains the primary automatic label set for every comparison
that the pre-registration defines on automatic labels, v2 is reported alongside.

## 2. No-dose rule and counts

Rescan of the 72 answers that the frozen extractor calls `no_dose` (`results/journal5/rd2/amend1/nodose_rescan.md`, rule-based):
46 refusals, 2 state that the label has no such dose, 24 contain a dose (earlier hand estimate: 25): 4 are parseable after a
narrow recovery pass applied only to frozen `no_dose` answers ("N million units", "N, units: mg") and get a v2 class
(colistimethate_0/1 and nafcillin_0 → unverifiable, venlafaxine_1 → time_ambiguous); 20 use units outside the frozen
vocabulary (fluid ounces, mg PE, %, AUC, microdrops, tablets, anti-Xa units, a bare number) and stay `no_dose`.

Rule: all 72 answers go into the adjudication sheet as their own stratum (`no_dose_v1`, inclusion probability 1). They are
**excluded from the primary estimates** (as pre-registered: no-dose answers are not dose answers) and **included in a
sensitivity analysis** in which a human-confirmed dose that is wrong counts as an error and a refusal counts as not-an-error
(and, separately, as an error).

## 3. Adjudication sheet v2 and weighting

Selection (`scripts/journal5/rd2_sheet_v2.py`; `results/journal5/rd2/amend1/sheet_strata.md`) — a superset of the
pre-registered rule and of all 1,845 rows of the pre-registered sheet:

- census (π = 1): every answer that is not `correct` under v1 **or** v2 (this includes all `match_other_context`,
  `time_ambiguous`, `unverifiable` and the 72 no-dose answers), plus every answer flagged by the frozen basis check (full);
- 10% sample (π = 0.1): answers `correct` under both label sets and not flagged. The sample is the pre-registered control draw
  itself (seed 20261002, 427 of the 4,270 pre-registered "rest" rows, π = 427/4,270 = 0.1 exactly), reproduced from the data
  and checked row by row against the committed blinded v1 sheet, restricted to rows still correct under both label sets.

Sheet: 2,473 rows = 1,845 pre-registered rows + 556 `match_other_context` (v1) answers not drawn as controls + 72 no-dose
answers. Columns: row_id, question, label excerpt, answer and the pre-registered rating columns; no generator, condition,
automatic class, checker verdict, basis flag or selection source.

Strata: v2 class × condition, with `correct` split into `correct_sampled` (π = 0.1) and `correct_census` (π = 1; correct under
v2 but not v1, or basis-flagged), plus `no_dose_v1`. Counts per stratum in `sheet_strata.md`.

Estimators (Horvitz–Thompson, weight w = 1/π: 10 for `correct_sampled`, 1 otherwise; ratio estimators Σw·y / Σw·x):

- prevalence of human-confirmed dose errors (and of unit/basis-type errors) among dose answers, overall and per condition;
- checker PASS rate on confirmed errors and PASS rate on confirmed correct answers, per checker and condition;
- basis-check recall (flagged among confirmed unit/basis errors) and PPV (confirmed unit/basis errors among flagged).

If only P1 is rated, the same estimators use P1 weights w = N_h / n_h (stratum population size / P1 rows in that stratum);
strata with no P1 row are reported as not covered.

CIs: stratified, question-clustered bootstrap (resample questions with replacement within each sampling stratum, recompute the
weighted estimator), 10,000 resamples, seed 20261002, percentile 95% intervals. Unweighted rates are reported alongside.
Rows rated "unclear" (cannot judge) are excluded from numerators and denominators and their number is reported per stratum.

## 4. Priority subset P1 and stopping rule

P1 = sheet rows RD2V2-0001…RD2V2-0200 (seed 20261005, drawn before the sheet was sent): 120 v2 unit/basis errors (the single
grounded v2 unit/basis error plus 119 closed-book, proportional to unit vs basis: 33 unit, 86 basis), 40 correct answers from the
10% sample (11 closed, 29 grounded, proportional), 20 value errors (all closed; the 2 grounded value errors were not drawn),
20 others (5 each from match_other_context, time_ambiguous, unverifiable and no_dose_v1). Deviation from the requested
"all grounded unit/basis errors, stratified": under v2 only 1 grounded unit/basis error remains, so the 120 are almost all
closed-book.

Order: P1 rows first (shuffled), then the remaining 2,273 rows (shuffled). Stopping rule: the rater completes P1 first; the
analysis is run on P1 (P1 weights) as soon as P1 is complete and again on the full sheet once all rows are rated. Rows beyond
P1 from an incomplete pass are reported descriptively only. No stopping or extension decision depends on the ratings.

## 5. Second rater

A second pharmacist rates an overlap set of 50 rows inside P1 (30 unit/basis, 10 correct, 5 value, 5 other; seed 20261005),
blinded to the first rater. Agreement: Cohen's κ (with bootstrap CI) on "is the dose an error" (Y/N; unclear excluded and
counted) and on the error type. The first rater's labels are primary; disagreements are reported, not overwritten.

## 6. Post-run analyses (unchanged design, now fixed in writing)

Question-clustered bootstrap CIs in addition to Wilson and drug-clustered intervals; McNemar tests with Holm correction over the
64 paired comparisons of `results/journal5/rd2/ci/rd2_ci_mcnemar.csv`; parse-failure sensitivity (parse failures as FAIL and
as excluded); closed-book-only and grounded-only rates. The primary outcome is reported as **PASS on errors** (the share of
erroneous answers that a checker lets through), with PASS on correct answers alongside.

## 7. Blinding of the adjudication keys

The v1 key (`results/journal5/rd2/qc/rd2_adjudication_key.csv`) has been in this **private** repository since commit 103be8a
(2026-10-02). It is not rewritten out of history. The rater does not have and will not have access to the repository. The public
release will be a clean snapshot (Zenodo/OSF) without `results/journal5/rd2/qc/`, not the git repository.
`results/journal5/rd2/**/*key*` is added to `.gitignore`. The v2 key is written but **not committed**; it will be committed
after adjudication is complete, and its hash below fixes its content now.

## 8. Lock

- sha256(`results/journal5/rd2/amend1/rd2_adjudication_sheet_v2.csv`) = `f573bfd617685fd066fc1e6e6a28c7821a9c293e644b9fc2a8927e87af041891`
- sha256(`results/journal5/rd2/qc/rd2_adjudication_key_v2.csv`, not committed) = `7fe7cc1e99a2cfa10541c8f99613d81b9d7948a6a1bdd778150e7df711539c00`
- sha256(`results/journal5/rd2/qc/rd2_adjudication_key.csv`, v1) = `6c4333e138073f8d390231bc6d0c47265a67ea37a834b0ed1d4e39bd323db339`
- sha256(`results/journal5/rd2/amend1/labels_v2.jsonl`) = `c053f42632944fde170890ace306d867ddb29174993dfdc293afb847152b1f20`
- Commit: the commit adding this file (see `git log -- prereg/rd2_amendment_1.md`).
