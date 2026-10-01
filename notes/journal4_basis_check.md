# Journal 4: deterministic dose-basis check (rule frozen BEFORE the full evaluation)

**Status at the freeze commit: rule + tests only, no full-set results.** Code: `scripts/journal4/basis_check.py`
(rule `basis-check-1`), tests: `scripts/journal4/test_basis_check.py` (`python -m unittest scripts/journal4/test_basis_check.py`;
also `python scripts/journal4/basis_check.py --selftest`). Python >= 3.8 (tests pass on 3.8 and 3.13), stdlib only.

## What it does

Input = the same two texts a fact-checker sees: the generator answer (`claim`) and the FDA label excerpt (`evidence`) of
`results/journal2/real_dose/instances.jsonl` (1451 RD answers). It does **not** use the gold target sentence / span
(`evidence_span`, `auto_class`), unlike `scripts/journal2/rd_extract.py` which built the auto labels.

1. **Parse** dose mentions on both sides with the repo's unit normalizer: UNF v2 surface pre-pass
   (`src/unit_norm_fix_v2.prenormalize`, frozen sha256 `1e816234...`, unchanged) + UNF v1 spans (`src/unit_norm_fix.find_spans`:
   number/range, mass/volume/units/mEq/mmol, `/kg`, `/m2`, concentration, time). Local extensions after a span:
   `/lb` / `per pound` (E1), `<n> mcg of <drug> per kg` (E2), `per minute per kilogram` (E3), `once daily / daily / a day` -> /day
   and `once weekly / weekly` -> /week (E4; "twice daily", "every 12 hours" are frequencies, not a basis). Context tags:
   *bound* (maximum / exceed / up to / less than ...), *strength* (absolute dose followed by tablet/capsule/vial ...),
   concentration spans (/mL, /L) are never compared.
2. **Consistent** if an answer dose MATCHes any evidence dose (same kind, same body basis with kg<->lb at 5% tolerance,
   time equal/convertible/missing on one side, equal value or range containment). Matched doses are never flagged.
3. **R1 paired (number neighbourhood)**: evidence doses sharing a surface numeral with the unmatched answer dose are typed
   `basis_dropped` (evidence /kg|/m2|/lb, answer none), `basis_changed` (other body basis), `unit_kind` (mass vs units/mEq/mmol),
   `unit_scale` (mg vs mcg vs g, not equal after conversion), `time_basis` (/min,/h,/day,/week, not equivalent), or compatible
   (`basis_ok`, `basis_added` = answer has a basis the evidence mention lacks, `time_ambiguous` = /dose vs /day). Flag if a
   flaggable type exists and no compatible candidate exists. Also `unit_scale` if an evidence dose with the same basis and a
   different unit is exactly 1000^k times the answer value (mis-conversion, e.g. 500 mcg -> 0.5 g).
4. **R2 unpaired (basis neighbourhood)**: for an unmatched, non-bound answer dose without any compatible R1 candidate: if
   every comparable evidence dose (same kind; bounds, strengths, concentrations excluded; same time basis if any, else
   time-compatible) carries a body basis and the answer's basis is not among them -> `basis_dropped_unpaired` /
   `basis_changed_unpaired`.
5. **Guards**: an absolute answer dose equal (+-10%) to a per-weight answer dose x a weight stated in the answer is a worked
   example, not an error (R1 basis_dropped and R2). R2 also skips absolute doses when the answer gives a matching body-based dose.
6. **Item status**: `flag` | `pass` (a comparable pair was found and agreed) | `abstain` (doses present, nothing comparable) |
   `no_dose`. Variants: **full = R1 + R2 (primary)**, **strict = R1 only (pre-specified secondary)**.

Out of scope: value errors with the right basis, per-dose vs per-day when a side has no explicit time, population /
indication mismatches with the same basis, IU<->mg factors, numbers in tables whose unit is only in a header.

## Provenance (read before interpreting any number)

* The rule was designed **after** reading all 47 auto-flagged unit-type rows (`auto_class` in unit_error/basis_error) and the
  12 AI-precheck "true" unit errors in `qc/ai_precheck_real_dose_unit_errors.csv` (AI labels by an LLM agent, **not human-verified**).
  These 47 rows are the **dev set**; recall on them is optimistic by construction. R2, E1-E4, the bound/strength tags, the
  weight guard and the `/dose`-vs-`/day` = not-judged decision were all chosen while looking at them (the last one after a
  pregabalin row, "150-300 mg per dose" vs "300 mg/day", was flagged by the first draft).
* Before this freeze the rule was run **only** on those 47 dev rows and the unit tests; it was **not** run on the other
  1404 RD answers. Dev numbers seen during design (frozen rule): full flags 12/12 true12 and 19/47 flagged47 (0/12 of the
  rows the precheck calls `parser_artifact_answer_correct`, 4/14 `different_indication_or_population`); strict flags 6/12
  true12 and 7/47 flagged47.
* The full evaluation (flag rate on all 1451 and on the presumably-correct 1451 - 47 as the false-alarm proxy, abstain
  rate, combined "checker PASS AND not flagged") is run afterwards by `scripts/journal4/basis_check_eval.py` and committed
  separately under `results/journal4/basis_check/`. `basis_check.py` must not be edited after this commit; problems found in
  the evaluation are reported, not fixed (verify with `git log -- scripts/journal4/basis_check.py`).

## Evaluation (added in the follow-up commit; rule unchanged since the freeze commit fdb95de)

`python scripts/journal4/basis_check_eval.py` -> `results/journal4/basis_check/{report.md,report.json,per_item.jsonl,flagged_outside_flagged47.csv}`.

* DEV recall (optimistic, see above): full 12/12 true12, 19/47 flagged47; strict 6/12, 7/47. The 6 true12 errors only the
  full variant catches are all R2 (unpaired: ivermectin x2, filgrastim, cyclophosphamide, ceftriaxone, epinephrine).
* False-alarm proxy: full flags 6/1404 (0.4%) of the answers outside flagged47 and 3/1062 (0.3%) of `auto_correct`;
  strict 4/1404, 3/1062. Abstain (full): 20/1451 (1.4%) overall, 0/1062 auto_correct; no_dose 3 (concentration-only answers).
* Combined "checker PASS AND not flagged" (full): 0/12 true12 errors slip through for every checker/judge with RD scores
  (DEV, by construction), at a cost of <=0.3 points PASS on auto_correct.
* The 6 flagged answers outside flagged47 — **provisional reading by the agent (Grok Bot), not human-verified**:
  - allopurinol (gemma3_27b, closed; auto `correct`): "100 mg orally every 8 to 12 hours" vs label pediatric
    "100 mg/m 2 ... every 8 hours to 12 hours" -> looks like a REAL dropped /m² that the auto extractor missed (v1 lost the
    superscript in the target sentence, so the auto label is itself a parser artifact).
  - hydroxychloroquine (gemma3_27b, closed; auto `value_error`): "pediatric >= 31 kg ... 310 mg" vs "6.5 mg/kg up to 400 mg"
    -> looks like a REAL dropped weight basis (R2).
  - lamotrigine (gpt4o_mini, closed; auto `time_ambiguous`): "no more rapidly than 50 mg every week" vs "50 to 100 mg/day
    every week" -> ambiguous: E4 read the titration interval "every week" as a /week basis; the answer does omit "/day".
  - glucagon (gpt4o_mini, closed; auto `correct`): "1 mg (1 unit)" vs "1 mg (1 mL)" -> FALSE ALARM (unit_kind; glucagon
    1 mg = 1 unit is a legitimate equivalence; the 1 mg itself matched).
  - ivermectin (gpt4o_mini, closed; auto `correct`): "200 micrograms (mcg) of ivermectin per kg" -> FALSE ALARM (parser: the
    "(mcg)" parenthesis defeats extension E2).
  - sulfamethoxazole (gemma3_27b, closed; auto `unverifiable`): "200 mg/40 mg per teaspoonful" -> FALSE ALARM (a per-teaspoon
    product strength is not recognised as a concentration; R2 then compares it with the pediatric mg/kg doses).
* Known parsing limits seen in the outputs: parenthetical unit restatements, "per teaspoonful" strengths, titration intervals
  read as a time basis, coincidental small-integer numeral pairs in R1 (e.g. "1.5-3 g/m²" paired with "3 mg per kg").
