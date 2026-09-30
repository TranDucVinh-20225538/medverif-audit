# M1-strong pre-registration (Oct 2025 freeze)

Frozen **before** any M1-strong scoring or table generation for this track.

## Primary criterion (verbatim)

Numeral binding is supported for a checker if US_up_after >= NS_x10 - 5 points AND US_down_after >= NS_div10 - 5 points, or the 95% cluster-bootstrap CIs overlap. US_after above NS is expected and not counted against. Evaluated on spans parsed by BOTH M1 and M1-lib.

## Design notes

- **US_up** / **US_down**: unit-sensitivity FAIL rates (| C0 PASS) on paired **up** (T7 E1-unit ×1000) and **down** (T17 E1-unit-down) cohorts separately; reported after M1 normalization.
- **NS_x10**: numeral-sensitivity FAIL rate (| C0 PASS) on E1 **×10** value perturbations (claim and evidence reported separately).
- **NS_div10**: numeral-sensitivity FAIL rate (| C0 PASS) on T17 **÷10** (`E1-down10`) when scored; if not available at step-2 time, US_up is reported first and US_down when T17 scores land—no substitute NS.
- **M1**: in-repo regex canonicalizer (`src/quantity_norm.py`).
- **M1-lib**: quantulum3 extraction + pint conversion; explicit mcg/µg/ug alias map; alias fixes logged. **No M2.**
- **Coverage gate**: dose-span coverage computed first; causal metrics only on instances whose edited spans lie in the **M1 ∩ M1-lib** parse intersection.
- **API budget (M1-strong rescoring)**: ≤ **$2** total; **RAGAS × Llama-3.3-70B** and **MedScore × Mistral-Small-24B** only.

## Outputs

- `results/tables/m1_strong.md`
- `notes/m1_strong_report.md`

## Held-out (steps 3–5; separate commit)

T14, T17, T18, T24 approved rows only; side effects on C0, POL rephrase, T4 444 answers, LLM-AggreFact balanced accuracy; T15 columns only if AggreFact-ft checkpoint exists by **Oct 4 22:00**.
