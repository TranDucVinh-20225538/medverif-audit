# RD2 pre-adjudication status (2026-10-05) — PROVISIONAL automatic labels, no pharmacist label seen

**A (amendment 1).** Commit `3819182` (2026-10-05 21:42:19 ICT), pushed to origin/master right after. Files: `prereg/rd2_amendment_1.md`
(+1 pointer line in `prereg/rd2_amendments.md`), `results/journal5/rd2/amend1/`, three new scripts, `.gitignore`
(`results/journal5/rd2/**/*key*`). Key v2 written to `results/journal5/rd2/qc/rd2_adjudication_key_v2.csv`, not committed.
- Totals v1 → v2 (`amend1/relabel_diff.md`, each column 5,760): unit 135→119, basis 324→307 (unit+basis 459→426), correct 3,654→3,679,
  value 668→676, other context 623→619, time 207→212, unverifiable 77→80, no dose 72→68. 49 items changed (33 m² artefacts, 12 other
  m² surface fixes, 4 recovered no-dose answers); 10/10 unit tests pass (33 m² cases flip, ≥10 negatives).
- A2 (`amend1/nodose_rescan.md`): 72 no-dose answers = 46 refusals, 2 "label has no dose", 24 contain a dose (estimate was 25):
  4 parseable (3 unverifiable, 1 time_ambiguous), 20 in units outside the vocabulary (fl oz, mg PE, AUC, %, microdrops, …).
- Sheet v2 (`amend1/sheet_strata.md`): 2,473 rows = all 1,845 v1 rows (reproduced exactly) + 556 other-context + 72 no-dose.
  In sheet: value 676, basis 307, unit 119, other-context 619, time 211, unverifiable 77, correct sampled 362 (π 0.1), correct census 30, no dose 72.
- P1 = rows 1–200: 120 unit/basis (34 unit incl. the only grounded one, 86 basis), 40 correct (11 closed, 29 grounded), 20 value, 20 other (5 each); overlap 50.
- sha256: sheet v2 `f573bfd6…af041891`, key v2 `7fe7cc1e…711539c00` (full values in the amendment §8).

**C1** (`results/journal5/rd2/analysis/c1_condition_rates.csv`). Closed-book PASS on errors v1 / v2 | on correct v1 / v2:
RoBERTa 14.3/14.1 | 66.9/66.8 · DeBERTa 10.3/10.4 | 41.8/41.5 · AlignScore-base 18.1/18.4 | 63.9/63.5 · Flan-T5 16.3/15.5 | 55.3/55.5 ·
AlignScore-large 16.3/16.5 | 74.8/74.4 · RAGAS 4.9/4.2 | 71.3/71.1 · MedScore 6.7/6.6 | 72.3/72.0 · MedGemma-27B 5.8/5.4 | 68.9/68.6 ·
Baichuan-M2 6.1/5.4 | 68.7/68.6 · basis full 47.4/44.7 | 99.6/99.6 · basis strict 74.7/73.4 | 99.6/99.6 · FT Flan-T5 r0.5/r1/r2 26.8/19.5/19.5 (v1) ·
FT AlignScore-large r0.5/r1/r2 29.5/22.6/25.1 (v1). Closed-only FT Flan-T5 r1 vs base: errors 16.3→19.5% (b/c 27/41, p = 0.115; v2 p = 0.065),
correct 55.3→52.8% (p = 0.052). **Answer:** yes, roughly — closed-book checkers pass 4.9–18.1% (v1) / 4.2–18.4% (v2) of errors, because 447/459
(v1) and 425/426 (v2) errors are closed-book anyway; what the closed-book restriction changes is PASS on correct answers (41.8–74.8% vs 65.4–87.5%).
Grounded errors are only 12 (v1; 11 of them m² artefacts) / 1 (v2), so grounded rates on errors are not interpretable.

**C2** (`analysis/c2_subtypes_per_item.csv`): per_kg 265/265, per_m2 159/126, unit_swap 2/2, rest 33/33 (v1/v2). Committed rule (classifier's
primary answer dose vs matched label dose): absolute-for-relative 259/259, relative-for-absolute **131 (v1) / 98 (v2)** — reproduces the audit's
259/131 exactly; the ad hoc 255/123 matches no committed rule (alternatives give 255/129 and 253/124). Use the committed rule; report 259/98 alongside.

**Tables:** `results/journal5/rd2/analysis/rd2full.tex`, `rd2paired.tex`, `rd2gen.tex`. **C4:** no change — the 72 no-dose answers were never scored by
the checkers and the 4 parseable ones fall outside the error/correct sets (`analysis/c4_nodose_sensitivity.json`). **D:** `analysis/paper_numbers_rd2.{json,md}`.

**Deviations.** (1) 33 m² artefacts flip, not ≥38: the ~5 per-kg cases have another cause and are value-wrong; listed as a known limitation (user-approved).
(2) A narrow no-dose recovery pass (4 answers) in v2. (3) Only 1 grounded unit/basis error under v2, so P1's 120 are almost all closed-book.
(4) The 10% correct sample is the pre-registered control draw (π = 0.1 exactly), so sheet v2 ⊇ sheet v1. (5) Amendment text says 21:45 ICT; the commit
time 21:42:19 ICT is authoritative. (6) Key v1 stays in git history (private repo) per decision; new keys gitignored. (7) The drug-cluster CIs (5,000) use a
different seed stream from rd2_report.py, so they differ from report.md in the first decimal.
