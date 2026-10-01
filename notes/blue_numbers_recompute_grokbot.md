# Blue-numbers check: Same Dose, Different Verdict (v2, recomputed)

**Status (2026-10-01 ~12:30 ICT).** Repo cloned at `ee1ba47` and moved to `7043858`. Commit `7043858` changes no data and no
scoring scripts: it adds only notes, the zip and the `--tag` option. All recomputation is CPU only, with no API calls.
**Src** column: **R** = recomputed from raw files with the repo's own loaders/scripts (scripts in `scripts/grokbot_recompute/`, outputs to `results/grokbot_recompute/`);
**F** = value read from a committed artifact, not recomputed.
I re-ran `scripts/paper_numbers_final.py` and it reproduces all **666** values: value and n are identical to the committed `notes/paper_numbers_final.json`.
I re-ran `m1_strong_run.py --final --amend5` and the Table-3 cells are identical.
**Reproducibility gap:** `data/lane_b/m1_strong_ns.jsonl` is not committed. I rebuilt it with `m1_strong_score_missing.build_ns_instances()` (n=408).

| # | Item | Paper | Current value | n | Src | Match / note |
|---|---|---|---|---|---|---|
| 1 | QC polarity flips accepted | 26/46 | 26/46 | 46 | F | Y |
| 2 | QC template rephrases accepted | 34/42 | 34/42 | 42 | F | Y |
| 3 | QC freq/route edits accepted | 36/51 | 36/51 (14/22 + 22/29) | 51 | F | Y |
| 4 | QC unit edits accepted | 30/30 | 30/30 (T7 ×1000 sample) | 30 | F | Y (the unit-conversion rewrite labels `qc/unit2_PI_ok_labels.csv` are a different set, 14/40) |
| 5 | QC value edits valid | 86–89% | ×2 32/37, ×10 33/37 | 37 | F | Y |
| 6 | Gemini-approved rewrites rejected | 17/40 | 17/40 | 40 | F | Y |
| 7 | StatPearls spot-check accepted | 63% | 34/54 = 63.0% | 54 | F | Y |
| 8 | Under-specified base claims | 16/37 | 16/37; 16 flagged bases in the card cohort | 37 | F/R | Y |
| 9 | Weak-contrast items | 318 / 60 | **312 rows / 59 bases** in the main card cohort; 318/60 only in the older `instances_cpu_early.jsonl`, which still includes D0164 | — | R | **N**: use 312/59 |
| 10 | Robustness, max abs Δ over all 111 Table-2 cells (19 configs × 6 metrics, C0-conditional), weak-contrast excluded | — | **4.90 pp**: Llama-3.3-70B NS 92.3% (n=209) → 97.2% (n=109). 4 of 111 cells move by more than 3 pp | | R | Only NS moves, because weak flags sit only on E1/E2 rows. Runners-up: DeBERTa NS +4.21, Mistral-MedScore NS +3.87, Flan-T5 NS −3.35 |
| 11 | Same, under-specified bases excluded | — | **6.36 pp**: Mistral-24B (MedScore) QI_nat 63.6% (n=22) → 70.0% (n=20). 12 of 111 cells move by more than 3 pp | | R | Runners-up: GPT-4o-mini MedScore QI_all +5.04 (61→53), QI_nat +5.00, SummaC-Conv US_claim −4.43, Llama-8B QI_all +3.79 |
| 12 | Main card (Table 2) | — | All cells identical to `paper_numbers_final.md` | | R | Y |
| 13 | M1 table (Table 3) | — | All cells identical (`notes/m1_strong_final_amend5.json`) | | R | Y. The JSON embeds absolute HPC paths |
| 14 | MiniCheck median score drop, conversion vs ×2 dose | 0.85 vs 0.91 | Legacy table `prelim_v2v3.md` (committed): 0.8522 vs 0.9134. **Re-run of that script today: 0.837 (n=73) vs 0.913 (n=132).** Main DOSE card cohort, C0-PASS bases: **Flan-T5-Large 0.854 (n=60) vs 0.919 (n=101)**; RoBERTa 0.758 (55) vs 0.889 (94); DeBERTa 0.798 (55) vs 0.832 (95); Bespoke-7B 0.206 (62) vs 0.851 (105) | | R | **N/caveat**: (a) `v2a_minicheck` is **MiniCheck-Flan-T5-Large**, not RoBERTa. (b) The 0.85/0.91 pair comes from a stale legacy table (the INV rows were backfilled later). Suggested text: "MiniCheck-FT5: 0.85 vs 0.92 (main set)" |
| 15 | E2 faithful-but-wrong PASS, fine-tuned checkers | 95–100% | Main card cohort, E2|C0: Flan-T5 210/212 99.1%; AlignScore-L 206/208 99.0%; AS-base 100/102 98.0%; RoBERTa 98/99; DeBERTa 97/98; Granite 108/109; SummaC-ZS 88/88; SummaC-Conv 82/82; HHEM 107/107; Bespoke 110/110. **Range 98.0–100%** | 82–212 | R | Y (within range) |
| 16 | E2 PASS, LLM judges | 95–100% | Main card cohort, E2 PASS given C0 PASS: MedScore×Mistral **204/218 = 93.6%**; MedScore×GPT-4o-mini 207/218 = 95.0%; RAGAS×Llama-8B 203/212 = 95.8%; Llama-70B 210/218 = 96.3%; Mistral-3.2 218/220 = 99.1%; RAGAS×GPT-4o-mini 207/212 = 97.6%; Haiku 4.5 210/214 = 98.1%. **MedScore×GPT-4o and Sonnet 4.6 have no E2 scores anywhere (all branches, all result dirs)**. Scoring them: `scripts/e2_remaining_judges.py`, about $1.70. Full table: `notes/e2_all_judges.md` | 212–220 | R | **N**: Mistral is below 95%, so the range across 7 judges is 93.6–99.1%. The 5 extra judges come from `results/raw/t23/` (pins match the registry). The old **86.4% (273/316)** is a stale note (Sep 29); today the script gives 212/229 = 92.6% (120 bases, including 11 POLARITY rows). There are no duplicate ids. 316 is not reproducible from committed files |
| 17 | T17 value-decrease NS, small checkers | 91–99%, n=80–95, "7 checkers" | Claim cells (÷2, ÷10): 91.2% (AS-base ÷10 83/91) – 98.9% (DeBERTa ÷10 88/89), n=80–95, **6 checkers**. With Bespoke (7): same range, n=80–98. Evid cells: 87.4% (FT5 ÷10 83/95) – 98.9% | 80–98 | R | **N (count)**: 6 checkers for n≤95, or 7 checkers with n≤98. HHEM, SummaC-Conv and Granite have no T17 scores |
| 18 | T14 unit_spell/spacing given C0 | 97–100%, n=87–107 | 96.9–100%, n=87–107 | | F | Y |
| 19 | T14 INV-nat given C0 | 0–23% | 0.0–22.7% | 17–22 | F | Y |
| 20 | Repair MedScore×Mistral | 44/115 → 9/115 | same | 115 | F | Y |
| 21 | Repair Llama-70B | 53/114 → 16/114 | same | 114 | F | Y (the typo note uses 53/115) |
| 22 | Typo explanations | 4/44, 4/53 | same | | F | Y |
| 23 | Frequency rewrites DeBERTa/RoBERTa | 2/14, 4/14 | same | 14 | F | Y |
| 24 | AggreFact genuine re-expressions | 10/40 | **10/40** (`qc/t8_mismatch_check.csv` and `qc/t8_PI_ok_labels.csv` both have 40 rows, 10 Y) | 40 | R | **Y**. This corrects my earlier "10/39" |
| 25 | T4 eco answers | 438 | 438 = 146 tasks × 3. Original run 444 = 148 × 3; D0171 and D0173 were later dropped as non-dose | 438 | R | Y |
| 26 | "No answer re-expressed a unit … 0/444" | 0/444 | **0/444 replaced the source unit** (current cohort 0/438). 2 answers kept the source unit and added an equivalent in parentheses: D0133/deepseek "0.4 mg (400 mcg)" (target dose) and D0156/command_r "1 g (1000 mg)" (non-target). 51 answers spell units out ("milligrams") | 444 | R | Y if worded as "replaced". Also say "2 added a parenthetical equivalent". Separately: real dose errors are **1/444** (D0162/command_r), not 0 |
| 27 | T4c surface-variant false alarms | 11.5% vs 1.1%, p=0.03 | 3/26 vs 1/89, p=0.033, identical for MedScore×GPT-4o and ×GPT-4o-mini | | F | Y, but the comparison is surface variant vs verbatim within each model, not GPT-4o vs GPT-4o-mini |
| 28 | T19 1B / 3B / 70B QI_all | 87.8 / 13.0 / 75.8% | same (n=49/23/62) | | R | Y |
| 29 | T19 8B | 27.6% (n=58) | **API row** 16/58 = 27.6%, NS claim 99.5% (n=203). **Local 8B** (from regenerating `t19_report.py`): QI_all 23/61 = 37.7%, QI_nat 40.9% (n=22), NS claim 96.6% (n=205), C0 100% (n=108). Local vs API verdict agreement: 88.5% (n=1401) | | R | Y as API. The committed `notes/t19_scale_sweep.md` is stale (local 8B shows NA). Label the paper row "8B (API)" or switch to local |
| 30 | Real-RAG questions | 53 | 56 − 1 duplicate − 2 thresholds | | F | Y (text fix) |
| 31 | NeMo rail | 16/21, 15/20 | same | | F | Y |
| 32 | Selection harm | 77–100% of 22 | 0.773–1.000 | 22 | F | Y |
| 33 | Fine-tune OOD and base | 41/41, 37/37; 59/12%; 98%; 89 vs 85% | same | | F | Y |

## Disagreements with Cursor's `notes/blue_numbers_check.md` (commit 7043858)
- Rows 9, 10, 11, 14 (T19 8B), 16/17 (T17), 26 (MiniCheck drop values), 29 (T4c): **same values**. Cursor's weak-contrast "312/59" matches my recompute.
- **E2** (Cursor rows 23/24): Cursor reports the regenerated `e2_t7_comparison_report.py` cohort (FT5 220/224, Mistral 212/229, Llama-70B 236/244). That cohort includes 11 POLARITY E2 rows and DOSE bases outside the 110-base card. On the card cohort I get FT5 210/212, Mistral **204/218 (93.6%)**, Llama-70B 210/218 (96.3%). Either way, Mistral is below the paper's 95% lower bound. Cursor's 92.6–99.2% for LLM judges uses `results/raw/t23`, which I did not check.
- **MiniCheck**: Cursor does not say that `v2a_minicheck` is Flan-T5-Large. A paper sentence that says "MiniCheck (RoBERTa)" would be wrong. RoBERTa gives 0.76 vs 0.89.
- **AggreFact 10/40**: Cursor is right (my earlier 10/39 was wrong).
- **"0/444" unit re-expression**: Cursor doesn't check it. My count: 0/444 replaced the unit, and 2/444 added a parenthetical equivalent.

## Zip
Cursor's `release/audit_snapshot_v4.zip` (7043858) **leaks**:
- `/root/medverif-audit` in 13 files (`jobs/run_*_node30.sh`, `notes/environment_node30.md`, `notes/t6a_eco_checkers.json`)
- `bright92` in `notes/t9_setup.md`
- `$HOME/.cursor/projects/data2-hpcshared-Vinh/...` in 3 scripts
- node30 / node001/002/004 hostnames
- Vietnamese PI notes in 20 `qc/*.csv` files, `notes/expand_dose2_failure_types.{md,json}` and 2 scripts

Replaced in this commit by the scrubbed rebuild (`scripts/scrub_audit_v4.py --src-zip <cursor v4> --out release/audit_snapshot_v4.zip --head 7043858`): 1873 files + README + manifest. It reproduces all 666 `paper_numbers_final` values. Residual grep hits are only in public-dataset text (LLM-AggreFact, T15 pairs, Wikipedia/T18, FDA labels) or are random-ID substrings. The leaky zip is still in git history (blob from 7043858).
