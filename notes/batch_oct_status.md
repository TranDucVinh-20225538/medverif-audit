# Batch Oct status (HPC)

Updated: **2026-09-30 ~22:15 UTC+7** · Freeze **Oct 5 23:59** · follow-up deadline (T15-OOD, token analysis) **Oct 3 22:00**

## Oct 1 decisions (author)

- **Env cleanup job 62017 done Oct 01 10:46:** decisions 1–8 applied; `paper_numbers_final.md` 640 numbers (reference 449, checked 156, UNCHECKED 20, node30-only 10, n/a (human labels) 5); report `notes/env_cleanup_oct1.md`.
- **Polarity MedScore E2 n:** **11 is correct** (8/11; matches author's independent card). The old n=25 came from `results/raw_m1/v1_medscore.jsonl` (M1-normalized T1 rescore, mistral-small-24b): current loader 11 rows + 14 E2 rows found only in that file reproduce the old 21/25 exactly. No paper loader reads `results/raw_m1/` (`t7_e1_unit_report.SCORE_DIRS`), so it is excluded. No further action.
- **T1 raw_m1 38 off-spec rows: SUPERSEDED, not rescored** (T1 is not in the paper). Recorded in `notes/m1_prereg_amendment5.md` §1.
- **Amendment 5 note** rewritten (spec fixed in amendment 4; 84 scored texts off-spec; fixed after results were seen; criterion unchanged; both results reported). Side by side: `notes/m1_strong_amend5_side_by_side.md` (`scripts/m1_amend5_side_by_side.py`).
- **Final chain (one sbatch):** Figure 1 final, audit zip v3 (with AggreFact), `paper_numbers_final.md` from amend5 → job ID / ETA below when submitted.
- **Final chain job 62016 done Oct 01 10:19:** Figure 1 final (18 points, HHEM/SummaC-Conv excluded); `paper_numbers_final.md` from amendment 5 (640 numbers: reference 397, UNCHECKED 146, checked 82, node30-only 10, n/a (human labels) 5); audit zip v3 1867 files, 79 MB, committed.

## Oct 1 ~01:15 update (supersedes rows below where they conflict)

- **M1-strong → amendment 5** (`notes/m1_prereg_amendment5.md`, found after final results; criterion unchanged). (1) After-M1 texts were off the amendment-4 spec: 46 rows (23 bases) US_up local pack, 38 (19) US_up API pack, 0 US_down, NS clean. Rescored (job 61850 local; OpenRouter for MedScore/RAGAS). (2) Gate was not independent (both sides one function) → `src/m1_lib_indep.py` (quantulum3+pint): 1546/1546 target spans agree, cohort unchanged (110 bases). **Corrected table** `results/tables/m1_strong_final_amend5.md`; every changed cell in `notes/m1_strong_amend5_changes.md`. **Overall binding 1/8 → 5/8 small checkers** (RoBERTa, AlignScore-large, SummaC-ZS, Bespoke now True; Granite unchanged True). The token-analysis no-op caveat is resolved by this fix.
- **node30 normalizer** recovered from stash and committed as canonical M1 (`87087da`, T1 942/942, US_down 150/150); spec regex default (`ae8ce5d`).
- **DeBERTa → cpuverif:** job 61826 done; 10 verdict flips across main/e2/T4-eco/T4c/T7 (`notes/deberta_cpuverif_swap.json`); backups `*.pre_cpuverif.quarantined.jsonl`. Clean change list (baseline regenerated under current code) in `notes/deberta_cpuverif_changes.md`.
- **Flan-T5 raw_m1 12 rows:** rescored with spec M1 text in cpuverif (`results/raw_m1/flant5_12_amend5/`); disagreement was text drift (old regex), spec-text scores match node30.
- ~~Open: 38 T1 raw_m1 rows~~ → resolved in the Oct 1 decisions below.
- **AggreFact 61690:** 82 tasks held until DeBERTa regeneration finishes.

## Per-task status (current)

| Task | Status | Headline / blocker | Deliverable |
| --- | --- | --- | --- |
| **M1-strong** | **done — accepted** (`8939e6c`) | 110 gate bases, post-amendment-4; paired before/after, McNemar b/c, Bind on AFTER up AND down; Granite row (cpuverif agreement 60/60). **Open caveat:** 40/214 US_up ×1000 rows (mg/kg→g/kg 30, mL→L 10) are M1 no-ops (checker-side `quantity_norm` DOSE_RE lacks g/kg, L); sensitivity in token-analysis note; accepted table unchanged pending author decision | `results/tables/m1_strong_final.md`, `notes/m1_strong_final.json` |
| **T13** | **done** (`4b892fb`) | Pair (1) ×1000 vs INV-natural now filled for all small checkers (n=22 natural pairs; `raw_node30` added at lowest priority, LLM rows unchanged). Small checkers 0.86–1.00 vs frontier LLM judges 0.00–0.16 | `results/tables/t13_pairwise_preference.md` |
| **T14** | **running** — job **61617** (rerun approved once) | Env agreement **passed** for every small checker (100% verdict agreement, 30/30 each); scored RoBERTa, DeBERTa, AlignScore-base, SummaC-ZS (227 each); Granite in progress. Table pasted when job ends | `results/raw/t14/`, `notes/t14_env_agreement.json` |
| **T15 card** | **done — accepted** (`7fa88c2`) | Main DOSE base vs ft; US up (T7 ×1000) + US down (unit-down) from same pipeline | `notes/t15_report.md`, `notes/t15_card.json` |
| **T15-OOD** | **scored; T18 base cross-check open** | T24b (53 q, T24_037/T24_066 excluded): ft C0 88.7%, value×10 97.9%, unit up 100%, unit down 100% vs base 84.9 / 100 / 59.0 / 11.8. T18 Wikipedia: base and ft 100% in every cell. Base T24b = existing scores 202/202; base T18 disagrees with earlier `results/raw/t18` RoBERTa on 8/74 same-text rows (large score gaps) → cpuverif recheck (4 of 8 finished before timeout) reproduces the **earlier** scores exactly (e.g. T180012 PASS 0.897 vs T15 pipeline FAIL 0.005). The T15 pipeline (vllm env) and the reference cpuverif env disagree on 7/37 T18 unit_swap rows plus 1 C0; cause not found (not length, not M1). **T18 T15-OOD cells are not citable** until resolved; T24b cells unaffected (202/202 agreement) | `notes/t15_ood_report.md`, `notes/t15_ood_card.json`, `data/t18/instances_t18_t15ood.jsonl` |
| **Token analysis** | **done — EXPLORATORY** | US_up after split by "original numeral survives as a token" per checker tokenizer; NS_x10 control (flag=yes n=0 for most single-token-number tokenizers). Found the M1 no-op caveat above | `notes/m1_token_overlap_exploratory.md` |
| **T18** | **appendix; scores partial** | Reviewed pack 372 rows (337 valid, 37 bases, ×2/÷2 + unit_swap + unit_spell; no ×10). Scores: RoBERTa 372, V1/V2b/V4 337, DeBERTa 124 (partial); AlignScore/SummaC/Granite not scored. Old T15 `base/ft_t18` (736) are from pre-review build `7d8e919` — do not cite | `results/raw/t18/` |
| **main_ext** | **partial** (PI labels present) | 480 instances; RoBERTa 480, V1 380, V4 380, Bespoke 356, DeBERTa 44; other small checkers not scored | `results/raw/main_ext/`, `qc/main_ext_labels.csv` |
| **T19 3B/8B** | **scored; report stale** | Local 3B 1703/1703 but **623 PARSE_FAIL (36.6%)**; local 8B 1703/1703 with 31 PARSE_FAIL (finished 01:53, after `notes/t19_scale_sweep.md` was written at 00:43, so its "8B local NA" row is stale). Needs report regen before citing | `results/raw/t19/llama32_3b_instruct.jsonl`, `llama31_8b_instruct.jsonl` |

## Preregistration / amendment hashes (`git log --format='%h %ad' -- <file>`)

| File | Commit | Date |
| --- | --- | --- |
| `notes/m1_preregistration.md` | `d3833a3` | 2026-09-30 15:16:10 +0700 |
| `notes/m1_prereg_amendment1.md` | `8fe6441` | 2026-09-30 15:45:30 +0700 |
| `notes/m1_prereg_amendment2.md` | `4eb9df5` | 2026-09-30 15:59:00 +0700 |
| amendment 3 | **no file** | only "narrow parse abort to us_up/us_down (amendment 3 code)" in this note; implemented as `abort_packs` in `scripts/m1_strong_run.py` |
| `notes/m1_prereg_amendment4.md` | `2d9563c` | 2026-09-30 19:39:11 +0700 |

## Spend

- OpenRouter: ~$12.84 remaining before the M1 US_down V1/V4 API run (~300 calls, ~$0.04); no API used for T15-OOD or token analysis.

---

## Previous snapshot (2026-09-30 ~17:45)

Updated: **2026-09-30 ~17:45 UTC+7** · Freeze **Oct 5 23:59** (no extension)

## Slurm queue (toandq)

| Job | Name | State | Exit | Elapsed | End (local) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **61599** | m1_strong | **FAILED** | 2 | 20:53 | 16:59:49 | Table **written** then `finalize_and_abort` (NS parse ~27% logged; us_up 22.8%) |
| 61593 | m1_strong | FAILED | 2 | 17:34 | 16:34:41 | Same abort pattern |
| 61572 | m1_strong | COMPLETED | 0 | 16:56 | 16:04:00 | Superseded table (7338b21 on remote) |
| 61573 | m1_repair | COMPLETED | 0 | — | 15:47 | `notes/m1_e1_unit_repair_report.md` |
| 61574 | t9_nat3 | COMPLETED | 0 | — | 15:47 | `notes/t9_inv_nat3_report.md` |
| 61585 | t24_fill | COMPLETED | 0 | 2:48 | 16:02 | `qc/t24_review.csv` 80/80 |
| 61579/61583 | t24_fill | FAILED | 1 / 127 | — | — | Superseded by 61585 |
| 61560 | t22_reward | FAILED | 1 | 4:48 | 14:49 | InternLM RM; **T22 CUT** for paper (no RMs) |
| 61556–61558 | bespoke/gpu | COMPLETED | 0 | ~4m | 14:44 | T18/main_ext bespoke partial |

**Active jobs:** none (2026-09-30 17:45).

---

## One-line track status (T13–T24, main_ext, M1-strong)

| Track | Status | Headline | Deliverable path |
| --- | --- | --- | --- |
| **T13** | **done** (main) | Pairwise harm; t6 encoders **n=22** on INV-nat / C0 pairs (node30 score subset) | `results/tables/t13_pairwise_preference.md` |
| **T14** | **done** (main) | C0-conditional; LLM **~109–110** bases; encoders **n=23** node30 | `results/tables/t14_c0_conditional_pass.md` |
| **T15** | **partial** | main_dose **996/996** base+ft; AggreFact test **n=29320** paired (BAcc ft **0.730** vs base **0.726**) | `notes/t15_report.md`, `notes/t15_aggrefact_report_run.md` |
| **T16** | **appendix** | Attribution report committed earlier | `notes/t16_report.md` |
| **T17** | **done** (needs dedupe→PI filter) | Raw LLM **612** lines / manifest **588**; lane B **588/588** | Dedupe + `qc/t17_labels.csv` → expect **540** (pending script) |
| **T18** | **appendix** (blocked→PI ok) | **`qc/t18_PI_ok_labels.csv`** present (**93** rows); NS/US + unit_spell only; no headline QI (**6/92** nat) | Rescore when FINAL PI locked |
| **T19** | **done** (8B local **NA**) | See results table below; **70B QI all 75.8%** (T19 cohort) | `notes/t19_scale_sweep.md` |
| **T20** | **appendix** | 194 drugs, 115 FDA labels, 11 unit-surface diffs | `notes/t20_report.md` |
| **T21** | **CUT** | — | — |
| **T22** | **CUT** | HHEM 996/996 only; **not** a reward model — drop from outputs | Remove HHEM from T22 narrative |
| **T23** | **appendix / CUT unless rescope** | v6 **996/996** ×4 models; llama31_8b **996/996** — **not reasoning**; paper: 1 closed + 1 open reasoning by Oct 3 22:00 or CUT | `results/raw/t23/` |
| **T24** | **done** | Review **80/80** | `qc/t24_review.csv` · **`0d30f8b`** |
| **main_ext** | **blocked→PI** | **`qc/main_ext_labels.csv`**; V1 **380/480**; score small checkers not only V1 | `results/raw/main_ext/` |
| **M1-strong** | **table local, job exit 2** | **104** gate bases; all 11 checkers aggregated; Summac/Granite **partial** (HF `\n` in token on 61599) | `results/tables/m1_strong.md` (**17:34**), `notes/m1_strong_report.json` |

---

## Delivered results (copy-paste headlines)

### M1-strong (`results/tables/m1_strong.md`, post-61599 run)

- Gate bases **104**; primary bind examples: RoBERTa CLAIM/EVID **Bind=True**; DeBERTa EVID **Bind=False**; Bespoke CLAIM **Bind=True**.
- **Caveats:** job **exit 2** (parse-error audit flags NS packs ~27%); Summac T17/M1 US legacy scores incomplete in 61599; Granite US_up after **NA** (0 paired).
- V4 reconcile: pooled 7338b21 **91.1%** FAIL → evid-only **~83% (84/101)** documented in table.

### M1 repair + T9 nat3

- Repair: V1 E1-unit-evid PASS **44/115 → 13/115**; V4 **53/114 → 19/114** (`notes/m1_e1_unit_repair_report.md`).
- T9 INV-unit: base rail **16/21** all, **15/20** nat3-Y (`notes/t9_inv_nat3_report.md`).

### T19 scale (RAGAS-NLI, `notes/t19_scale_sweep.md`)

| Model | C0 | QI all | QI nat | NS claim | US claim ×1k | US evid ×1k | n notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1B local | 87.6% (n=105) | 87.8% (n=49) | **94.1%** (n=17) | 5.3% FAIL (n=169) | 3.5% (n=85) | 1.2% (n=86) | cohort 1703 inst |
| 3B local | 87.5% (n=64) | 13.0% (n=23) | 22.2% (n=9) | 91.4% (n=93) | 100% (n=48) | 67.3% (n=49) | |
| 8B local | **NA** | NA | NA | — | — | — | use **8B API** + footnote |
| 8B API | 97.2% (n=109) | 27.6% (n=58) | 27.3% (n=22) | 99.5% (n=203) | 83.5% (n=103) | 47.6% (n=103) | |
| 70B API | 100% (n=109) | **75.8%** (n=62) | 72.7% (n=22) | 97.1% (n=209) | NA | NA | US cols not rescored |

**70B QI 75.8% vs card ~76.7%:** T19 uses **`instances_t19.jsonl`** (1703 inst, clustered `base_id`); card QI is **main_dose INV-natural** with possibly different base filter / bootstrap slice — compare `n=62 bases=62` (T19 QI all) vs card denominator (often **~109** C0-pass bases but QI on INV-nat subset only). T14 conditional QI for 70B: **72.7% (n=22)** on C0-pass — closer to T19 QI-nat **72.7%** than “all”.

### T13 (excerpt)

- Main DOSE **110** bases; pair (×1000 vs INV nat) **n=22** for encoders scored on **node30** only — full LLM judges have **n=22** on col (1), **n=107** on evid×1000 vs C0.
- Bespoke (1): **0.227** [0.045, 0.409] (n=22) vs V2a **0.955** [0.864, 1.000] (n=22).

### T14 (excerpt — small checkers + QI)

| Model | C0 (n) | QI INV\|C0 (n) | unit_spell | spacing | symbol |
| --- | --- | --- | --- | --- | --- |
| V2a | 0.964 (110) | 0.045 (22) | — (node30) | — | — |
| V3 | 0.945 (110) | 0.190 (21) | — | — | — |
| Bespoke | 1.000 (110) | **0.818 (22)** | — | — | — |
| V1 | 1.000 (110) | 0.636 (22) | 1.000 (109) | 1.000 (109) | 1.000 (9) |
| V4 70B | 1.000 (110) | 0.727 (22) | 1.000 (109) | 1.000 (109) | 1.000 (9) |

### T15 AggreFact (`notes/t15_aggrefact_report_run.md`)

- **base** BAcc **0.7263** (n=29320 paired); **ft** **0.7297** (n=29320).
- Subsets: AggreFact-CNN **558**, XSum **558**, RAGTruth **16371**, etc.

### T22 / T23 decisions

- **T22 CUT** — reward models never ran; **HHEM excluded** from T22 outputs (not an RM).
- **T23:** “v6” = **`v6_ragas_*`** (gpt4o-mini, haiku45, mistral_small32, llama31_8b filenames). **llama31_8b is instruct, not reasoning.** Rescope to one closed + one open reasoning (no Qwen/Gemini) by **Oct 3 22:00** or **CUT**.

---

## Spend

- **OpenRouter** (`notes/openrouter_credit.json`): **$37.16 / $50** used (**$12.84** remaining).
- **`results/api_cost.json`:** misleading **~$0.017** (legacy glob only) — **do not cite**; use OpenRouter credit for batch spend.

---

## Next (post-61599, no resubmit while author reviews)

1. Fix HF token `strip` + **gap-only** rescore Summac/Granite on M1 US + T17.
2. Narrow parse abort to **us_up / us_down** only (amendment 3 code) → clean exit 0.
3. T17 dedupe **612→588→540** + per-verifier **n** report.
4. T18/main_ext: FINAL PI CSVs → small-checker score passes.
5. Commit **M1-strong code** + final table when exit 0; push after author sign-off.
