# Batch Oct status (HPC)

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
