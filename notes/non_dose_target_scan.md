# Non-dose target scan (DOSE bases)

Invalidated with `valid=false`, `invalid_reason=non_dose_target`:

| base_id | dose_kind | target | reason |
|---|---|---|---|
| D0171 | measurement | 3.5 g | Daily urine **protein** threshold (nephrotic range), not a medication dose |
| D0173 | prescriptive | 1 µg | **IU conversion factor** in bracket note (`1 µg vitamin D = 40 IU`), not a dose to take |

## Scan: `dose_kind ∈ {measurement, unclear}` (C0 rows, main+threshold)

No additional bases flagged beyond **D0171** after manual review. Other measurement rows (e.g. diagnostic thresholds, OGTT glucose) remain valid dose-verification targets for counterfactuals.

**T4:** `D0171` / `D0173` removed from `eco_tasks.jsonl` and `eco_answers.jsonl` (6 answers); verifier instances rebuilt without those tasks.
