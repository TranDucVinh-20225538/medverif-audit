# RD2 exploratory extension A — frontier generators on P1 questions

Locked **2026-10-16 12:43 ICT**, **before any frontier generation call**.
Not a change to the pre-registered RD2 analyses; reported as exploratory.
No pharmacist rating of these answers has been seen (the main RD2 sheet may still be in progress).

## Project context (one paragraph)

**medverif-audit / RD2:** real US prescribing-label dose questions answered by LLMs (closed-book and grounded); automatic dose extractors + fact-checkers / judges scored on those answers; a blinded pharmacist sheet (`amend1` / `amend2`) is the reference standard. Amendment 1 = m² parser patch + sheet v2 + P1. Amendment 2 = 2–3 pharmacist raters, majority on overlap, rating rules, assignment shares. This note = optional frontier **re-generation** on the P1 question set so the paper can show whether stronger APIs still produce unit/basis errors and whether checkers/judges still pass them.

## Sample (fixed)

- Source: the 200 P1 rows `RD2V2-0001`…`RD2V2-0200` in `results/journal5/rd2/amend1/rd2_adjudication_sheet_v2.csv` (key v2, not committed until adjudication ends).
- Those 200 rows cover **149 unique `qid`s** (some questions appear more than once under different original generators/conditions in P1). The generation set is those **149 qids**, not a new draw.
- List written at run time to `results/journal5/rd2/frontier_gen_A/p1_qids.txt` (sorted) and hashed into the run manifest; regenerating the list from key v2 + P1 flags must match.

## Phases (closed first; grounded locked as phase 2)

| Phase | Condition | Generators | Max answers | When sent to pharmacist |
|---|---|---|---|---|
| **1** | closed only | GPT-4o + Claude Sonnet | 149 × 2 = **298** | After the current amendment-2 batch is finished |
| **2** | grounded | same two models | 149 × 2 = **298** | Separate later sheet; **not** contingent on phase-1 results |

Phase 2 is pre-declared here so a grounded-only follow-up cannot be read as outcome-dependent selection. Total if both phases complete: **596** new answers (not 800: P1 has 149 distinct questions, not 200).

## Generators (pins; one sample per slot)

| slug | OpenRouter model | Provider pin |
|---|---|---|
| `gpt4o` | `openai/gpt-4o` | OpenAI |
| `claude_sonnet` | `anthropic/claude-sonnet-4.6` | Anthropic |

- **Samples per (qid, condition, model): 1** (no best-of-n).
- **Temperature: 0**; **seed: 42** (if the API honours it).
- **Prompt:** exact same user prompt as RD2 generation (`scripts/journal5/rd2_generate.py` / journal-2 question template); no system-prompt change unless recorded in the run manifest.
- **API call date** and returned `api_model` / provider / request id logged per row in the answers jsonl.
- Cap: `--max-usd` (default 30 for phase 1). Resume by `instance_id`.

## Blinding for the pharmacist sheet

- Sheet columns: `row_id`, `batch`, `question`, `label_excerpt`, `answer` + the same rating columns as amendment 2; **no** generator, condition, auto class, checker, or phase tag.
- Row order: single shuffle of all phase-1 rows (and stability anchors), seed **`20261016`**.
- Key file (gitignored until adjudication done): maps `row_id` → `instance_id`, generator, condition, whether `stability_anchor`, original RD2 `row_id` if anchor; path `results/journal5/rd2/qc/rd2_frontier_gen_A_phase1_key.csv`.
- Caveat (acknowledged): GPT-4o vs Claude prose can still partially unblind a careful reader; we do not try to style-normalize (that would change the object of study). Reported as a limitation.

## Stability anchors (within-rater, across sessions)

- Into the phase-1 sheet, insert **~8%** (target **24**, clip to 20–30) **already-rated** RD2 answers: drawn from P1 rows that are **closed** under the original generators, seed **`20261016`**, without replacement.
- Text identical to the prior sheet; new `row_id`s; key marks `stability_anchor=True` and the source RD2 `row_id`.
- Purpose: agreement of the same pharmacist with herself across batches (not inter-rater κ). Anchors are excluded from frontier-generator prevalence estimates.

## Analyses (exploratory)

- Auto labels under v1 and v2 on the new answers; unit/basis error rates by model × condition.
- Checker / frontier-judge PASS on auto (and later human) errors — same definitions as RD2.
- Human ratings when returned: prevalence and PASS-on-confirmed-error with the amendment-1 estimators where π = 1 (census of this exploratory set).
- Side-by-side with the original P1 generators on the same qids (paired where both exist).

## What this is not

- Not part of the pre-registered primary RD2 table until explicitly promoted by a future amendment after ratings exist.
- Does not replace amendment-2 assignment or the main sheet v2.
- Does not use Gemini (OpenRouter Google ToS 403 on this org).

## Outputs (planned)

```
results/journal5/rd2/frontier_gen_A/
  p1_qids.txt
  phase1_manifest.json      # pins, sha256, call date, spend
  answers_phase1.jsonl
  sheet_phase1.xlsx         # blinded, for the pharmacist
results/journal5/rd2/qc/rd2_frontier_gen_A_phase1_key.csv   # gitignored pattern *key*
```

Code: to be added as new files under `scripts/journal5/` (e.g. `rd2_frontier_gen_A.py`) only after this note is committed; **no generation until that commit exists on the remote.**
