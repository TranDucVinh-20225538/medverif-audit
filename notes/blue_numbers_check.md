# "Blue numbers" check: recomputed from commit ee1ba47 with the current scripts (Oct 1)

All values were recomputed from a clean checkout of `ee1ba47`. Report scripts were run with their outputs redirected
to scratch, so no committed file changed. **Match**: Y = same value and n; N = differs (see note); Y* = matches under
one reading of the paper wording.

| # | Item | Paper value | Current value | n | Source file(s) | Match |
|---|---|---|---|---|---|---|
| 1 | QC: polarity flips accepted | 26/46 | 26/46 (56.5%) | 46 | `qc/flip_PI_ok_labels.csv` | Y |
| 2 | QC: rephrases accepted | 34/42 | 34/42 (81.0%) | 42 | `qc/inv_manual_review_PI_ok_labels.csv` (template rows) | Y |
| 3 | QC: frequency/route edits accepted | 36/51 | 36/51 (70.6%): frequency 14/22, route 22/29 | 51 | `qc/inv_claim_PI_ok_labels.csv` | Y |
| 4 | QC: unit edits accepted | 30/30 | 30/30 | 30 | `qc/t7_PI_ok_labels.csv` (T7 unit ×1000 sample) | Y* (a) |
| 5 | QC: value edits accepted | 86–89% | ×2 32/37 (86.5%), ×10 33/37 (89.2%) | 37 | `qc/dose3_labels.csv`, `notes/dose3_main_audit_apply.json` | Y |
| 6 | Gemini-approved dose rewrites rejected by author | 17/40 | 17/40 | 40 | `qc/inv_manual_review*.csv`, `data/v3/para_attempts_g.jsonl` (`scripts/qc_gemini_vs_author.py`) | Y |
| 7 | StatPearls spot-check | 63% | 34/54 accepted (63.0%) | 54 | `qc/dose2_PI_ok_labels.csv` | Y (b) |
| 8 | Main-set audit: under-specified base claims | 16/37 | 16/37 | 37 | `qc/dose3_labels.csv` (C0_ok = N) | Y |
| 9 | Weak contrast: instances / bases | 318 / 60 | 318 / 60 in `data/v3/instances_cpu_early.jsonl`; **312 / 59** in `instances_main.jsonl` | — | `scripts/dose3_robustness_report.py` (`weak_contrast_breakdown`) | N (c) |
| 10 | Robustness: max abs Δ of any Table-2 cell, weak-contrast rows excluded | (current data) | **4.90 pp**: Llama-3.3-70B (RAGAS NLI) NS 92.3% → 97.2% | 209 → 109 | main card loader + `metrics_block` | — (d) |
| 11 | Robustness: max abs Δ of any Table-2 cell, under-specified bases excluded | (current data) | **6.36 pp**: Mistral-Small-24B (MedScore) QI_nat 63.6% → 70.0% | 22 → 20 | same | — (d) |
| 12 | T19 Llama 1B: QI_all, NS claim | — | 43/49 (87.8%); NS claim 9/169 (5.3%) | 49; 169 | `results/raw/t19/*`, `scripts/t19_report.py` | — (e) |
| 13 | T19 Llama 3B | — | 3/23 (13.0%); 85/93 (91.4%) | 23; 93 | same | — (e) |
| 14 | T19 Llama 8B | — | API 16/58 (27.6%), NS 202/203 (99.5%); local 23/61 (37.7%), NS 198/205 (96.6%) | 58/203; 61/205 | same | — (e) |
| 15 | T19 Llama 70B | — | 47/62 (75.8%) (= main card QI_all); NS claim 203/209 (97.1%) | 62; 209 | `results/raw/v4_ragas_nli.llama.jsonl` | — (e) |
| 16 | T17 NS ÷2 claim, small checkers | range across 7 | 94.7% (Flan-T5 89/94) – 98.9% (DeBERTa 87/88) | 80–94 | `results/tables/t17_ns.md` | N (f) |
| 17 | T17 NS ÷10 claim, small checkers | range across 7 | 91.2% (AlignScore-base 83/91) – 98.9% (DeBERTa 88/89) | 81–95 | same | N (f) |
| 18 | T14 unit_spell P(PASS \| C0), 7 small checkers | range | 96.9% (DeBERTa 94/97) – 100% | 87–107 | `results/tables/t14_c0_conditional_pass.md` | Y |
| 19 | T14 spacing P(PASS \| C0), 7 small checkers | range | 100% for all 7 | 87–107 | same | Y |
| 20 | Repair: MedScore×Mistral E1-unit-evid PASS before → after M1 | 44/115 → 9/115 | 44/115 → 9/115 | 115 | `notes/m1_e1_unit_repair_report.md` | Y |
| 21 | Repair: Llama-70B (RAGAS) | 53/114 → 16/114 | 53/114 → 16/114 | 114 | same | Y |
| 22 | Typo-naming explanations | 4/44, 4/53 | 4/44, 4/53 | — | `notes/repair_typo_explanations.md` | Y (g) |
| 23 | E2 PASS, fine-tuned checkers | range | 98.2% (Flan-T5 220/224) – 100% (Bespoke 110/110; small encoders n = 19–23) | 19–224 | `scripts/e2_t7_comparison_report.py` (regenerated) | N (h) |
| 24 | E2 PASS, LLM judges | range | MedScore×Mistral 212/229 (92.6%), Llama-70B 236/244 (96.7%) | 229, 244 | same | N (h) |
| 25 | Frequency rewrites accepted: MiniCheck-DeBERTa / RoBERTa | 2/14, 4/14 | 2/14, 4/14 | 14 | `results/tables/t3_family_pass.md` | Y |
| 26 | MiniCheck median score drop: conversion vs doubled dose | 0.85 vs 0.91 | 0.837 (n=73) vs 0.913 (n=132) on the legacy cohort; 0.854 (n=60) vs 0.919 (n=101) on main DOSE (cpuverif) | see value | `results/tables/prelim_v2v3.md` (marked LEGACY) | N (i) |
| 27 | LLM-AggreFact manual check: genuine re-expressions | 10/40 | 10/40 | 40 | `qc/t8_mismatch_check.csv`, `notes/t8b_DROPPED.md` | Y |
| 28 | T4 eco answers | 438 | 438 | 438 | `notes/t4_eco_report.md` | Y |
| 29 | Surface-variant false alarms, MedScore×GPT-4o vs GPT-4o-mini | 11.5% vs 1.1%, p = 0.03 | Each model: surface variant 3/26 (11.5%) vs verbatim 1/89 (1.1%), p = 0.033; GPT-4o and GPT-4o-mini identical | 26 vs 89 | `notes/t4c_eco_report.md` (T4c, not T4) | N (j) |

## Notes

- (a) 30/30 holds for the T7 unit ×1000 edits. The unit-conversion rewrite labels (`qc/unit2_PI_ok_labels.csv`) are 14/40.
- (b) 63% is the **accept** rate. `notes/main_ext_manifest.json` mislabels it "QC fail ~63%".
- (c) The 6 extra rows are base D0164. It is marked invalid (non-dose target) in `instances_main.jsonl` but still
  valid in the older `instances_cpu_early.jsonl`, which the robustness report reads. Canonical value: **312
  instances / 59 bases**.
- (d) Table 2 = the main card (`Main card (main DOSE)` rows of `paper_numbers_final.md`). With no exclusion, all 111 cells
  match `paper_numbers_final`. Weak-contrast flags exist only on E1/E2 rows, so only NS moves under that exclusion.
  Runners-up: weak exclusion, MiniCheck-DeBERTa NS +4.21 and MedScore NS +3.87; under-specified exclusion,
  GPT-4o-mini (MedScore) QI_all +5.04, SummaC-Conv US_claim_up −4.43. REPORT's "largest shift −3.3 pp" refers to the
  `dose3_robustness_report.py` metric set, not Table 2.
- (e) The committed `notes/t19_scale_sweep.md` (Sep 30) is older than the 8B-local score file, so it shows 8B local as NA.
  Regenerating gives the values above. The 70B main-card `ns` (92.3%) is NS **evid**, not claim.
- (f) Only **6** small checkers have T17 ÷2/÷10 scores. Granite Guardian 2B's T17 file holds only the 150 `E1-unit-down`
  rows (`results/tables/t17_ns.md`: "No T17 scores: SummaC-Conv, HHEM, Granite Guardian 2B").
- (g) The typo report counts Llama as 53/115 rows, while the repair report pairs 114.
- (h) The committed `notes/e2_t7_verifier_comparison.md` (Sep 29) is out of date (it shows 98.3% 228/232 and LLM judges 86.4–100%).
  At ee1ba47 the script finds E2 rows for only two LLM judges, because GPT-4o-mini and the RAGAS/Sonnet E2 scores
  sit in `results/raw/t23`, which it does not scan. Adding that folder (exploratory) gives 92.6–99.2%.
- (i) This metric is not in `paper_numbers_final`. The table it comes from is marked LEGACY, and neither cohort reproduces
  both numbers.
- (j) The numbers are correct, but the comparison is **surface variant vs verbatim within each model** (T4c sentence-level
  claims), not GPT-4o vs GPT-4o-mini. In T4 both models are 2/26 (7.7%) on surface variants.
