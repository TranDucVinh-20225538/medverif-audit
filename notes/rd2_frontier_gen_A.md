# RD2 exploratory extension A — frontier generators on P1 questions

Locked **2026-10-16 12:43 ICT**; **revised 2026-10-16 12:45 ICT** (adjudication = auto-filter, not full census), still **before any frontier generation call**.
Not a change to the pre-registered RD2 analyses; in the manuscript this block is a **supplementary / exploratory analysis**.
No pharmacist rating of these frontier answers has been seen (the main RD2 sheet may still be in progress).

## Project context (one paragraph)

**medverif-audit / RD2:** real US prescribing-label dose questions answered by LLMs (closed-book and grounded); automatic dose extractors + fact-checkers / judges scored on those answers; a blinded pharmacist sheet (`amend1` / `amend2`) is the reference standard. Amendment 1 = m² parser patch + sheet v2 + P1. Amendment 2 = 2–3 pharmacist raters, majority on overlap, rating rules, assignment shares. This note = optional frontier **re-generation** on the P1 question set so the paper can show whether stronger APIs still produce unit/basis errors and whether checkers/judges still pass them.

## Sample (fixed): 149 distinct questions, not 200

- Source: the 200 P1 *answer rows* `RD2V2-0001`…`RD2V2-0200` in `results/journal5/rd2/amend1/rd2_adjudication_sheet_v2.csv`.
- Those rows are **not** 200 distinct questions. The same `qid` recurs across models and conditions in P1 (e.g. dexrazoxane appears on several P1 `row_id`s). Counted from key v2: **149 unique `qid`s**.
- The generation set is those **149 qids** (sorted list → `results/journal5/rd2/frontier_gen_A/p1_qids.txt`, sha256 in the manifest). Recomputing from key v2 + `in_P1` must match.

## Phases (closed first; grounded locked as phase 2)

| Phase | Condition | Generators | Answers generated | Pharmacist load |
|---|---|---|---|---|
| **1** | closed only | GPT-4o + Claude Sonnet | 149 × 2 = **298** | **Auto-filtered sheet only** (below), after the current amendment-2 batch |
| **2** | grounded | same two models | 149 × 2 = **298** | Separate later sheet; same filter rule; **not** contingent on phase-1 results |

Phase 2 is pre-declared so a grounded follow-up cannot be read as outcome-dependent. Closed-first matches RD2: almost all automatic unit/basis errors are closed-book.

## Pharmacist sheet = RD2-style filter (do not rate all 298)

Sister rates a **subset**, not every frontier answer (≈1 min/row → hundreds of rows is too heavy).

Selection on phase-1 answers, after v1/v2 auto labels (and basis-check full if scored), same spirit as amendment 1 / sheet v2:

1. **Census (π = 1):** every answer that is **not** `correct` under v1 **or** v2 (includes unit/basis/value/time/unverifiable/other-context/no_dose), **plus** any basis-check `flag_full` if the row was scored.
2. **Sample (π = 0.1):** answers `correct` under **both** v1 and v2 and not flagged — simple random sample, seed **`20261016`**, size `max(20, round(0.10 × |rest|))` (floor 20 so the control set is usable even if few dual-correct rows).
3. **Stability anchors:** ~**8%** of the *sheet* size (target 20–30, typically ≈24) already-rated **closed** RD2 P1 answers, seed **`20261016`**, identical text; excluded from frontier prevalence.

Expected phase-1 sheet size: on the order of **tens to low hundreds** of rows (depends on how often GPT-4o/Claude are auto-correct), not 298 and not 800.

Sheet: blinded columns as amendment 2; shuffle seed **`20261016`** over selected rows + anchors. Key gitignored: `results/journal5/rd2/qc/rd2_frontier_gen_A_phase1_key.csv`.  
Caveat: GPT-4o vs Claude style may partially unblind; not style-normalized; listed as a limitation.

## Generators (pins; one sample per slot; version + date logged)

| slug | OpenRouter model id | Provider pin |
|---|---|---|
| `gpt4o` | `openai/gpt-4o` | OpenAI |
| `claude_sonnet` | `anthropic/claude-sonnet-4.6` | Anthropic |

- **Samples per (qid, condition, model): 1** (no best-of-n).
- **Temperature: 0**; **seed: 42** when the API honours it.
- **Prompt:** identical to RD2 (`scripts/journal5/rd2_generate.py` / journal-2 template).
- **Per-row log (required):** UTC timestamp of the call, OpenRouter `api_model` string as returned, provider, request id, prompt/completion tokens, `api_cost_usd`. Manifest also stores the calendar **run date (ICT)** and the pinned model ids above (API snapshots can drift; the returned `api_model` is the version of record for the paper).
- Cap: `--max-usd` (default 30 for phase 1). Resume by `instance_id`.

## Analyses (exploratory / supplementary)

- Auto labels v1 and v2 on all generated answers (full 298/phase); unit/basis rates by model.
- Checker / frontier-judge PASS on auto errors (and on human-confirmed errors once rated).
- Human sheet: HT / ratio estimators with π as in the filter above; unclear excluded and counted; anchors reported separately (self-agreement).
- Manuscript wording: **supplementary exploratory analysis**, not the pre-registered primary RD2 table, unless a later amendment promotes it after ratings exist.

## What this is not

- Not a full pharmacist census of all frontier answers.
- Does not replace amendment-2 or sheet v2.
- Does not use Gemini (OpenRouter Google ToS 403 on this org).

## Outputs (planned)

```
results/journal5/rd2/frontier_gen_A/
  p1_qids.txt                 # 149 ids
  phase1_manifest.json        # pins, run date ICT, sha256, spend, filter counts
  answers_phase1.jsonl        # all 298 closed generations
  sheet_phase1.xlsx           # blinded filtered subset + anchors
results/journal5/rd2/qc/rd2_frontier_gen_A_phase1_key.csv
```

Code: new files under `scripts/journal5/` only after this note is on the remote; **no generation until then.**
