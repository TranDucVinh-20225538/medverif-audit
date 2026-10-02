# RD2 — pre-registration (frozen BEFORE any answer is generated)

**Study:** RD2, an independent, drug-disjoint, pre-registered expansion of the real LLM dose-answer set (RD,
`results/journal2/real_dose/`, 1451 answers) of the medverif-audit paper.
**Status:** frozen. This file, `prereg/rd2_freeze.json`, the question file and all `scripts/journal5/*.py` are added in ONE
commit (`journal5: RD2 prereg (frozen before generation)`), parent `b68dd09`. **That commit is the pre-registration
commit.** It contains no answers, no instances and no scores. Any later change goes to `prereg/rd2_amendments.md` (dated,
with reason, made before or after unblinding stated explicitly).
**Author of the protocol:** prepared by Grok Bot for Tran Vinh, 2026-10-02 (UTC+7).

## 1. Why RD2

RD has 47 auto-flagged unit/basis ("unit-type") errors, of which only 12 were judged true by an AI pre-check (not
human-verified), all from two API generators. That is too few to estimate how often fact-checkers PASS natural unit/basis
errors, and the dose-basis check frozen at `fdb95de` was designed after reading those 47 rows (its RD recall is DEV-set
recall). RD2 provides (i) many more naturally occurring unit/basis errors, (ii) a held-out set, disjoint by drug, for
validating the basis check, the fine-tuned checkers and the unit normaliser (UNF), and (iii) a human reference standard.

## 2. Questions (frozen)

| item | value |
|---|---|
| file | `results/journal5/rd2/real_dose/questions.jsonl` |
| sha256 | `e3e339e260e90dbd3e851bb05fd5129855a315642a8772fd0c5138a2c08f86ca` |
| n questions / drugs | 480 / 215 (1–3 per drug) |
| labels | `results/journal5/rd2/labels/labels.jsonl`, sha256 `6df85f0c1819429e1f50bfdefbdc4a98928df9a6595845052080abce0a7e2b9c` (230 openFDA labels, retrieved 2026-10-02) |
| generator | `scripts/journal5/rd2_questions.py --n 480 --per-drug 3 --gap 300 --fixed-share 0.15 --seed 20261002` (defaults) |

**Source.** Same as RD: openFDA drug label API, most recent HUMAN PRESCRIPTION DRUG SPL per generic name with a
`dosage_and_administration` section that has ≥ 1 parseable dose; `scripts/journal5/rd2_fetch_labels.py` reuses RD's
`rd_fetch_labels.fetch()` unchanged. The cached RD labels (`data/real_labels/`) cannot be reused: 197 of their 200 drugs
are RD drugs (the other 3 were re-fetched by the same query).

**Exclusion of RD (drug-level, stricter than drug/population/indication).** A label is dropped if it shares with RD any
lexicon drug name, set_id, openFDA generic or brand name, or ingredient word (≥ 5 letters, salt/form words ignored)
(`rd2_common.label_overlaps_rd1`). Result, checked by `scripts/journal5/test_rd2.py`: **0** RD drugs, **0** shared set_ids,
**0** shared target sentences, so **0** RD drug/population/indication combinations recur.

**Construction = RD's.** Sentence splitting (`rd_questions.sentences`), eligibility (≥ 1 non-concentration dose span from
`src/unit_norm_fix.find_spans`, 25–600 chars), excerpt (target ± whole sentences up to 900 chars), exactly one `[DOSE]`
slot (first non-concentration dose = `primary_target`, other doses masked `[...]`) and the question template are RD's code;
`rd2_questions.build_question` is that code factored out, and the unit test regenerates RD's 364 questions **byte for
byte** from RD's labels with it.

**Documented deviations from RD** (all before generation):
1. `mg/m 2` superscript repair: openFDA flattens m² to `m 2`, which `find_spans` reads as `75 mg` (basis lost; the source of
   RD's per-m² parser artifacts). RD2 rewrites `<unit>/m 2` → `<unit>/m2` in the label text before splitting.
2. Non-dose slots excluded: `[DOSE]` may not be a renal-function threshold (`creatinine clearance [DOSE] mL/min`, 107
   candidates dropped) or a diluent/reconstitution volume (121 dropped).
3. Every eligible sentence is a candidate (RD: the first 2 in text order); `dosage_and_administration` kept to 20 000 chars
   (RD 8 000) so late pediatric / renal subsections are eligible. Excerpts are still ≤ 900 chars, so prompts do not grow.
4. Error-prone selection. Pre-registered dosing-type tagger (`rd2_common.tag_dosing`, regex on the target sentence + 250
   chars of preceding label text): `bsa` (a /m² dose in the sentence), `weight_based` (/kg), `loading_maintenance`,
   `renal`, `pediatric`, `divided_daily`, otherwise `fixed`; stratum = first type present in that order. Per drug: ≤ 3
   targets, ≥ 300 chars apart, error-prone first, one per stratum in a first pass, seeded tie-break. Global: round-robin over
   the error-prone strata (seeded order) up to 408 (85 %), then 72 fixed-dose controls.

**Composition (stratum = primary type):** weight_based 138, bsa 108, pediatric 68, renal 43, loading_maintenance 28,
divided_daily 23, fixed 72. Multi-label: pediatric 172, weight_based 145, bsa 108, renal 75, divided_daily 68,
loading_maintenance 59. `[DOSE]` basis: /kg 133, /m² 95, absolute 252. 54 target sentences mix bases.

## 3. Answer generation (protocol frozen; not run yet)

**Prompts:** RD's, imported unchanged from `scripts/journal2/rd_generate.py` (`PROMPTS`, `render`, `MAX_TOKENS = 160`);
sha256 grounded `72e6b936…`, closed `8d797cc5…` (full values in the freeze file).

```
grounded: Answer the question using ONLY the drug label excerpt below. Answer in 1-2 sentences and state the dose (number and unit).\n\nLabel excerpt ({drug}):\n{excerpt}\n\nQuestion: {question}\n\nAnswer:
closed:   Answer from your own knowledge of the US prescribing information (no reference text is provided). Answer in 1-2 sentences and state the dose (number and unit).\n\nQuestion: {question}\n\nAnswer:
```

Both conditions for every question, so 960 answers per generator.

| generator id | model @ revision | path |
|---|---|---|
| llama31_8b | meta-llama/Llama-3.1-8B-Instruct @ 0e9e39f249a16976918f6564b8830bc894c89659 | HPC vLLM 0.8.3 |
| qwen25_14b | Qwen/Qwen2.5-14B-Instruct @ cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8 | HPC vLLM |
| medgemma_27b | google/medgemma-27b-text-it @ 5b667cf2ddcf064085bc90952edb35a0edbfb79c | HPC vLLM |
| baichuan_m2_32b | baichuan-inc/Baichuan-M2-32B @ 360f684d3cd527a4ef986c54071015eb0e6def58 | HPC vLLM |
| gpt4o_mini | openai/gpt-4o-mini, provider OpenAI (RD generator) | OpenRouter, `jr_common.chat_pinned` (RD's call path) |
| gemma3_27b | google/gemma-3-27b-it, provider DeepInfra (RD generator) | OpenRouter, `jr_common.chat_pinned` |

All models are already in the HPC Hub cache (`results/journal3/models.json`, loaded offline at the pinned revision).
`qwen25_7b` is an optional 5th generator. It is only used if one of the four fails to run, and that switch must be
recorded as an amendment.

**Decoding:** temperature 0, top_p 1, seed 42, max 160 new tokens, bf16, TP = 1. The open models get the prompt as **one
user turn through their chat template** (RD's API calls also sent one user message), with thinking disabled where the
template supports it, rendered as in `j3_judge_score.render`. A closed `<think>…</think>` block is removed. An
unterminated one (reasoning cut off at 160 tokens) is stored as an empty answer, i.e. missing.

**Retries / resume:** resumable by (qid, generator, condition). Up to 3 passes per run for empty or failed rows, and
re-runs resume. Greedy decoding makes reruns identical; the first non-empty answer is kept.

**Cost cap:** one cap of **$3** covers all RD2 OpenRouter spend (generation + API judges), ledger = sum of `api_cost_usd`
under `results/journal5/rd2/`. Every 20-call batch reserves its worst case first. Expected spend ≈ $0.07 for generation
plus ≈ $1.0 for the two API judges.

## 4. Extraction and auto-classification (frozen)

`scripts/journal5/rd2_extract.py` calls RD's `rd_extract.classify` **unchanged** (classes correct, match_other_context,
unit_error, basis_error, value_error, time_ambiguous, unverifiable, no_dose). Instances are written in exactly RD's
`instances.jsonl` schema (same keys and conventions; the unit test re-creates RD's 1451 instances from RD's
questions + answers), plus the additive keys `stratum`, `dosing_types`, `primary_basis`, `population`, `rd2`;
`source = journal5_rd2`. sha256 of every defining file (`src/unit_norm_fix.py`, `rd_extract.py`, `rd_questions.py`,
`rd_generate.py`, `rd2_common.py`, `rd2_questions.py`, `rd2_extract.py`) is in `prereg/rd2_freeze.json`. Generation and
extraction stop if any differs. Runner/analysis files are hashed too; a change there is logged and must be documented as
an amendment.

## 5. Reference standard: pharmacist adjudication

A licensed pharmacist (human), blind to checker/judge verdicts, auto class, basis-check flag and selection source,
adjudicates the **adjudication set** in `results/journal5/rd2/qc/rd2_adjudication_sheet.csv`
(`rd2_adjudication_sheet.py`, seed 20261002). The set is built only from the deterministic extractor and the frozen basis
check, never from checker scores:
- **A:** all auto unit_error, basis_error, value_error, time_ambiguous and unverifiable answers;
- **B:** all answers flagged by the frozen basis check (full variant);
- **C:** max(150, 10 %) seeded random controls from the remaining answers.

For each row the pharmacist decides whether the answer's dose is an error for the population/regimen of the `[DOSE]` slot
(Y/N/unclear) and assigns a type: unit / basis / value / time / other_population_or_indication / none.
**Natural unit/basis error = Y with type unit or basis.** Non-error = N. Unclear and other types are excluded from both
(reported). A second rater on a random 20 % (Cohen's κ) is desirable but not required. AI pre-checks may be used only as
reviewer aids, never as the reference.

## 6. Analyses (pre-specified)

Rates come with Wilson 95 % CIs (primary) and a 95 % drug-cluster bootstrap (5 000 resamples, secondary).
`scripts/journal5/rd2_report.py`; verdicts are read as in journals 3/4 (`j3_common.verdict_map`: stored verdict, else
score > 0.5). A judge's PARSE_FAIL is excluded from the denominator and counted (sensitivity: PARSE_FAIL = FAIL).

- **P1 (primary).** For each of the 7 paper checkers (MiniCheck-RoBERTa, MiniCheck-DeBERTa, AlignScore-base,
  MiniCheck-Flan-T5-Large, AlignScore-large, Llama-3.3-70B RAGAS-NLI, MedScore × Mistral-Small-24B): the **PASS rate on
  natural unit/basis errors**. Also the PASS rate on non-errors. For context, on RD the stored verdicts FAILed 75–92 % of the
  12 AI-pre-check-true errors (8–25 % PASS).
- **P2 (primary).** Frozen basis check (`fdb95de`, rule `basis-check-1`; full = primary, strict = secondary):
  - **recall** on natural unit/basis errors found independently of the rule (sources A or C) = primary; recall on all
    adjudicated errors = secondary;
  - **false-alarm rate** = flags adjudicated as non-unit/basis errors ÷ estimated non-error answers (adjudicated-negative
    rate of controls C extrapolated to the unselected rest);
  - PPV of flags.

  RD DEV-set values for comparison: recall 12/12 on true12, flag rate 1.7 %.
- **P3 (primary, transfer).**
  - (a) Chain-1 fine-tuned MiniCheck-Flan-T5 (r1 primary; r0.5, r2 and AlignScore-large FT secondary) vs the same-path base:
    FAIL on errors and PASS on non-errors.
  - (b) UNF v1 and frozen UNF v2 (sha `1e816234…`) applied before the 5 small checkers and the FT models: PASS on errors and
    on non-errors, raw vs UNF. Unchanged rows keep their raw verdicts.
- **Secondary.** P1 for the chain-3 local LLM judges (`j3_judge_score`, RAGAS-NLI prompt); error rates by generator,
  condition and dosing stratum. Frontier API judges are optional and not part of the primary analyses.
- Until the adjudication is complete, every number is labelled **PROVISIONAL (auto labels)** and is not a result.

## 7. Stopping rule

Generation stops when every (question, generator, condition) has an answer or has failed 3 passes plus one rerun (failures
are reported, not replaced), or when the $3 cap is reached (then RD2 = what was generated, reported as such). A generator
that cannot be loaded after 2 attempts is dropped (optional replacement `qwen25_7b`, as an amendment). **No questions,
models or generations are added after any answer or score has been seen.** The analysis runs once on the full set. If fewer
than 30 natural unit/basis errors are adjudicated, P1/P2 are reported as underpowered; any extension (e.g. RD3) needs a new
pre-registration.

## 8. Expected yield (ESTIMATE, not a result)

`scripts/journal5/rd2_expected_errors.py` → `notes/rd2_expected_errors.md`. It applies RD error rates per stratum
(same tagger) to the RD2 composition × 6 generators × 2 conditions = 5 760 answers. Expected: ≈ 308 auto-flagged
unit/basis errors (sum of cell Wilson bounds 192–626), ≈ 99 AI-pre-check-true-like unit/basis errors (48–363), and ≈ 387
value errors. RD had 47 / 12 / 93 in 1 456 answers. Caveats:
- most of the yield comes from closed-book weight-based questions (RD: 9/108 = 8.3 % true);
- RD's BSA cells were parser artifacts that RD2 repairs;
- open 7–32B models may err differently from RD's API models.

With ≥ 60 adjudicated errors, a Wilson CI half-width is ≤ ±13 percentage points at p = 0.5.

## 9. Files

`scripts/journal5/`: `rd2_common.py`, `rd2_fetch_labels.py`, `rd2_questions.py`, `rd2_expected_errors.py`, `rd2_freeze.py`,
`rd2_generate.py`, `rd2_extract.py`, `rd2_basis_check.py`, `rd2_unf_pack.py`, `rd2_adjudication_sheet.py`,
`rd2_j3_score.py`, `rd2_report.py`, `test_rd2.py`.

Jobs (added after this commit): `jobs/journal5/*.sbatch`, `jobs/run_rd2_chain.sh`. Run guide: `notes/rd2_cursor_prompt.md`.
