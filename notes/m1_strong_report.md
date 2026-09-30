# M1-strong (steps 1–2)

**Cohort:** `pre-amendment-4-draft-gate` · amendment4 file: True · M1-lib dimension fix in code: False

Pre-registration: `notes/m1_preregistration.md` · Amendments: `notes/m1_prereg_amendment1.md`, `notes/m1_prereg_amendment2.md`
M1-lib backend: **quantulum3+pint** · Gate bases: **104** (gate cache refreshed=False)
Report IDs: **V1** = Mistral-Small-24B (MedScore); **V2a** = MiniCheck-Flan-T5-Large; **V3** = AlignScore-large; **V4** = Llama-3.3-70B (RAGAS NLI).

## Criterion (verbatim)

> Numeral binding is supported for a checker if US_up_after >= NS_x10 - 5 points AND US_down_after >= NS_div10 - 5 points, or the 95% cluster-bootstrap CIs overlap. US_after above NS is expected and not counted against. Evaluated on spans parsed by BOTH M1 and M1-lib.

## Coverage by pack (edited target spans; before US/NS metrics)

| Pack | instances | inst gate pass | target spans | M1 only | M1-lib only | both |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| us_up_x1000 | 214 | 170 | 430 | 0 | 34 | 376 |
| us_down_unit | 150 | 150 | 300 | 0 | 0 | 300 |
| ns_x10_claim | 106 | 100 | 212 | 0 | 0 | 200 |
| ns_x10_evid | 106 | 100 | 212 | 0 | 0 | 200 |
| ns_div10_claim | 98 | 93 | 196 | 0 | 0 | 186 |
| ns_div10_evid | 98 | 93 | 196 | 0 | 0 | 186 |

## Primary — small fine-tuned checkers (decision M: SummaC-Conv & HHEM excluded)

| Model | Side | NS_x10 FAIL | US_up before FAIL | US_up after FAIL | NS_div10 FAIL | US_down FAIL | Bind? | n paired (McN) | p≈ |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| MiniCheck-RoBERTa | CLAIM | 94.3% [89.8,98.9] (83/88) | 33.7% [25.0,43.5] (31/92) | 94.9% [89.9,98.7] (75/79) | 97.6% [94.0,100.0] (81/83) | 7.1% [1.4,12.9] (5/70) | True | 92 (15 drop) | 3.26e-10 |
| MiniCheck-RoBERTa | EVID | 92.0% [86.3,96.6] (81/88) | 19.6% [12.0,28.3] (18/92) | 79.7% [70.9,87.3] (63/79) | 96.4% [92.8,100.0] (80/83) | 5.7% [1.4,11.4] (4/70) | True | 92 (15 drop) | 8.29e-11 |
| MiniCheck-DeBERTa | CLAIM | 96.6% [92.0,100.0] (85/88) | 90.1% [83.5,96.7] (82/91) | 93.5% [87.0,98.7] (72/77) | 100.0% [100.0,100.0] (83/83) | 88.6% [81.4,95.7] (62/70) | True | 91 (16 drop) | 0.505 |
| MiniCheck-DeBERTa | EVID | 94.3% [88.6,98.9] (83/88) | 74.7% [65.9,83.5] (68/91) | 57.1% [45.5,67.5] (44/77) | 95.2% [90.4,98.8] (79/83) | 80.0% [71.4,88.6] (56/70) | False | 91 (16 drop) | 0.00796 |
| MiniCheck-Flan-T5-Large | CLAIM | 94.7% [89.4,98.9] (89/94) | 55.1% [45.9,65.3] (54/98) | 95.2% [90.4,98.8] (79/83) | 93.2% [87.5,97.7] (82/88) | 5.4% [1.4,10.8] (4/74) | True | 98 (9 drop) | 7.12e-08 |
| MiniCheck-Flan-T5-Large | EVID | 84.0% [76.6,91.5] (79/94) | 22.4% [15.3,30.6] (22/98) | 55.4% [44.6,66.3] (46/83) | 88.6% [81.8,94.3] (78/88) | 8.1% [2.7,14.9] (6/74) | False | 98 (9 drop) | 0.000178 |
| AlignScore-base | CLAIM | 91.2% [85.7,96.7] (83/91) | 8.4% [3.2,14.7] (8/95) | 87.3% [79.7,94.9] (69/79) | 91.8% [85.9,97.6] (78/85) | 7.0% [1.4,14.1] (5/71) | True | 95 (12 drop) | 9.41e-15 |
| AlignScore-base | EVID | NA | 12.6% [6.3,20.0] (12/95) | 60.8% [50.6,70.9] (48/79) | 91.8% [85.9,96.5] (78/85) | 9.9% [4.2,16.9] (7/71) | None | 95 (12 drop) | 1.88e-08 |
| AlignScore-large | CLAIM | 96.7% [93.5,100.0] (89/92) | 54.2% [44.8,63.5] (52/96) | 96.3% [91.5,100.0] (79/82) | 94.2% [89.5,98.8] (81/86) | 12.2% [5.4,18.9] (9/74) | True | 96 (11 drop) | 1.52e-08 |
| AlignScore-large | EVID | 89.1% [82.6,94.6] (82/92) | 40.6% [31.2,50.0] (39/96) | 79.3% [70.7,87.8] (65/82) | 96.5% [91.9,100.0] (83/86) | 10.8% [4.1,17.6] (8/74) | True | 96 (11 drop) | 4.93e-07 |
| SummaC-ZS | CLAIM | 94.9% [89.9,98.7] (75/79) | 28.0% [19.5,37.8] (23/82) | 84.3% [75.7,92.9] (59/70) | 92.0% [85.3,97.3] (69/75) | 6.5% [1.6,12.9] (4/62) | True | 82 (25 drop) | 5.43e-09 |
| SummaC-ZS | EVID | NA | 24.4% [15.9,35.4] (20/82) | 77.1% [67.1,87.1] (54/70) | 93.3% [88.0,98.7] (70/75) | 4.8% [0.0,(None, None)] (3/62) | None | 82 (25 drop) | 3.8e-08 |
| Granite Guardian 2B | CLAIM | 85.6% [78.4,91.8] (83/97) | 42.6% [33.7,52.5] (43/101) | 94.4% [83.3,100.0] (17/18) | NA | NA | True | 20 (87 drop) | 0.00257 |
| Granite Guardian 2B | EVID | NA | 18.8% [11.9,27.7] (19/101) | 61.1% [38.9,83.3] (11/18) | NA | NA | None | 20 (87 drop) | 0.0412 |
| Bespoke-MiniCheck-7B | CLAIM | 98.0% [94.9,100.0] (96/98) | 66.7% [57.8,74.5] (68/102) | 100.0% [100.0,100.0] (85/85) | 96.7% [92.3,100.0] (88/91) | 80.0% [70.7,89.3] (60/75) | True | 102 (5 drop) | 1.19e-07 |
| Bespoke-MiniCheck-7B | EVID | NA | 36.3% [27.5,46.1] (37/102) | 75.3% [65.9,83.5] (64/85) | 96.7% [92.3,100.0] (88/91) | 38.7% [28.0,49.3] (29/75) | None | 102 (5 drop) | 2.54e-08 |

## Secondary — LLM judges (non-primary; same splits)

| Model | Side | NS_x10 FAIL | US_up before | US_up after | NS_div10 | US_down | Bind? | n paired | p≈ |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0% [100.0,100.0] (98/98) | 99.0% [97.1,100.0] (101/102) | 98.8% [96.5,100.0] (84/85) | 100.0% [100.0,100.0] (91/91) | 100.0% [100.0,100.0] (75/75) | True | 102 (5 drop) | 0.48 |
| Mistral-Small-24B (MedScore) | EVID | 92.9% [87.8,98.0] (91/98) | 59.8% [51.0,69.6] (61/102) | 91.8% [85.9,96.5] (78/85) | 98.9% [96.7,100.0] (90/91) | 93.3% [86.7,98.7] (70/75) | True | 102 (5 drop) | 4.93e-07 |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 100.0% [100.0,100.0] (97/97) | 100.0% [100.0,100.0] (100/100) | 98.8% [96.4,100.0] (83/84) | 97.8% [94.5,100.0] (89/91) | 89.2% [81.1,95.9] (66/74) | True | 100 (7 drop) | 0.248 |
| Llama-3.3-70B (RAGAS NLI) | EVID | 90.7% [84.5,95.9] (88/97) | 83.2% [75.2,90.1] (84/101) | 85.7% [78.6,92.9] (72/84) | 93.3% [87.6,97.8] (83/89) | 62.2% [51.4,73.0] (46/74) | True | 101 (6 drop) | 0.814 |
| Claude Sonnet 4.6 (RAGAS NLI) | CLAIM | 100.0% [100.0,100.0] (98/98) | 98.0% [95.1,100.0] (100/102) | NA | 100.0% [100.0,100.0] (91/91) | 100.0% [100.0,100.0] (75/75) | None | 0 (107 drop) | — |
| Claude Sonnet 4.6 (RAGAS NLI) | EVID | 98.0% [94.9,100.0] (96/98) | 67.6% [58.8,76.5] (69/102) | NA | 98.9% [96.7,100.0] (90/91) | 93.3% [86.7,98.7] (70/75) | None | 0 (107 drop) | — |

## V4 denominator reconciliation (7338b21 pooled bug)

- **7338b21** pooled E1-unit-claim + E1-unit-evid under one bootstrap → US_up before ≈ **91.5%** (184/201 FAIL instances).
- **Correct (EVID only, |C0 PASS|, parsed):** **83.2% [75.2,90.1] (84/101)** — matches repair report **n_paired≈114** on E1-unit-evid.
- **Card/repair (~55.8% PASS / 61 FAIL):** same **evid-only** cohort; 7338b21 **91.1%** was **FAIL rate on pooled 203**, not PASS.


## NeMo Guardrails (T9) — after non-dose base exclusion

Group **d** = T7 E1-unit (unit errors); group **c** = E1-claim ×2 (value errors). Rail blocks when AlignScore < 0.5. **Value-error detection** = blocked k/n; **unit pass-through** = not blocked k/n (177/230 raw = errors slipping past rail).

| Checkpoint | Slice | n | blocked k/n [CI] | not blocked k/n |
| --- | --- | ---: | --- | --- |
| AlignScore-base | unit-error (d) | 216 | **44/216** (0.204)  | 172/216 |
| AlignScore-base | value-error (c) | 110 | **108/110** (0.982)  | 2/110 |
| AlignScore-large | unit-error (d) | 216 | **107/216** (0.495)  | 109/216 |
| AlignScore-large | value-error (c) | 110 | **108/110** (0.982)  | 2/110 |

