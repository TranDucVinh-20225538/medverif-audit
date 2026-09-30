# M1-strong (steps 1–2) — **final**

**Cohort:** `post_amendment4_fixed_gate` · amendment4 file: True · M1-lib dimension fix in code: True

Pre-registration: `notes/m1_preregistration.md` · Amendments: `notes/m1_prereg_amendment1.md`, `notes/m1_prereg_amendment2.md`, `notes/m1_prereg_amendment4.md`
M1-lib backend: **quantulum3+pint** · Gate bases: **110** (gate cache refreshed=True)
Report IDs: **V1** = Mistral-Small-24B (MedScore); **V2a** = MiniCheck-Flan-T5-Large; **V3** = AlignScore-large; **V4** = Llama-3.3-70B (RAGAS NLI).

## Criterion (verbatim)

> Numeral binding is supported for a checker if US_up_after >= NS_x10 - 5 points AND US_down_after >= NS_div10 - 5 points, or the 95% cluster-bootstrap CIs overlap. US_after above NS is expected and not counted against. Evaluated on spans parsed by BOTH M1 and M1-lib.

## Coverage by pack (edited target spans; before US/NS metrics)

| Pack | instances | inst gate pass | target spans | M1 only | M1-lib only | both |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| us_up_x1000 | 214 | 214 | 430 | 0 | 0 | 430 |
| us_down_unit | 150 | 150 | 300 | 0 | 0 | 300 |
| ns_x10_claim | 106 | 106 | 212 | 0 | 0 | 212 |
| ns_x10_evid | 106 | 106 | 212 | 0 | 0 | 212 |
| ns_div10_claim | 98 | 98 | 196 | 0 | 0 | 196 |
| ns_div10_evid | 98 | 98 | 196 | 0 | 0 | 196 |

## Primary — small fine-tuned checkers (decision M: SummaC-Conv & HHEM excluded)

| Model | Side | NS_x10 FAIL | US_up before FAIL | US_up after FAIL | NS_div10 FAIL | US_down FAIL | Bind? | n paired (McN) | p≈ |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| MiniCheck-RoBERTa | CLAIM | 94.6% [89.1,98.9] (87/92) | 33.3% [25.0,42.7] (32/96) | 80.2% [71.9,87.5] (77/96) | 97.7% [94.2,100.0] (84/86) | 7.1% [1.4,12.9] (5/70) | False | 96 (11 drop) | 3.26e-10 |
| MiniCheck-RoBERTa | EVID | 92.4% [87.0,97.8] (85/92) | 20.8% [13.5,29.2] (20/96) | 68.8% [59.4,77.1] (66/96) | 96.5% [91.9,100.0] (83/86) | 5.7% [1.4,11.4] (4/70) | False | 96 (11 drop) | 8.29e-11 |
| MiniCheck-DeBERTa | CLAIM | 96.8% [92.5,100.0] (90/93) | 86.5% [80.2,92.7] (83/96) | 89.6% [83.3,94.8] (86/96) | 98.9% [96.6,100.0] (86/87) | 88.6% [81.4,95.7] (62/70) | True | 96 (11 drop) | 0.505 |
| MiniCheck-DeBERTa | EVID | 94.6% [89.2,98.9] (88/93) | 71.9% [63.5,80.2] (69/96) | 58.3% [47.9,67.7] (56/96) | 94.3% [88.5,98.9] (82/87) | 80.0% [71.4,88.6] (56/70) | False | 96 (11 drop) | 0.0164 |
| MiniCheck-Flan-T5-Large | CLAIM | 94.9% [89.9,99.0] (94/99) | 52.4% [42.7,61.2] (54/103) | 82.5% [74.8,89.3] (85/103) | 92.4% [87.0,97.8] (85/92) | 5.4% [1.4,10.8] (4/74) | False | 103 (4 drop) | 7.12e-08 |
| MiniCheck-Flan-T5-Large | EVID | 83.8% [75.8,90.9] (83/99) | 21.4% [14.6,29.1] (22/103) | 45.6% [36.9,55.3] (47/103) | 87.0% [79.3,93.5] (80/92) | 8.1% [2.7,14.9] (6/74) | False | 103 (4 drop) | 0.000178 |
| AlignScore-base | CLAIM | 91.6% [85.3,96.8] (87/95) | 12.1% [6.1,19.2] (12/99) | 74.7% [65.7,82.8] (74/99) | 90.9% [84.1,96.6] (80/88) | 7.0% [1.4,14.1] (5/71) | False | 99 (8 drop) | 9.41e-15 |
| AlignScore-base | EVID | NA | 16.2% [9.1,23.3] (16/99) | 53.5% [43.4,62.7] (53/99) | 90.9% [84.1,96.6] (80/88) | 9.9% [4.2,16.9] (7/71) | None | 99 (8 drop) | 1.88e-08 |
| AlignScore-large | CLAIM | 96.9% [92.8,100.0] (94/97) | 53.5% [43.6,63.4] (54/101) | 87.1% [80.2,93.1] (88/101) | 94.4% [88.9,98.9] (85/90) | 12.2% [5.4,18.9] (9/74) | True | 101 (6 drop) | 1.52e-08 |
| AlignScore-large | EVID | 89.7% [83.5,94.8] (87/97) | 40.6% [31.7,50.5] (41/101) | 69.3% [60.4,78.2] (70/101) | 96.7% [92.2,100.0] (87/90) | 10.8% [4.1,17.6] (8/74) | False | 101 (6 drop) | 4.93e-07 |
| SummaC-ZS | CLAIM | 95.1% [90.2,98.8] (78/82) | 27.1% [17.6,36.5] (23/85) | 69.4% [58.8,78.8] (59/85) | 91.0% [84.6,97.4] (71/78) | 6.5% [1.6,12.9] (4/62) | False | 85 (22 drop) | 5.43e-09 |
| SummaC-ZS | EVID | NA | 23.5% [15.3,31.8] (20/85) | 63.5% [52.9,73.0] (54/85) | 92.3% [85.9,97.4] (72/78) | 4.8% [0.0,(None, None)] (3/62) | None | 85 (22 drop) | 3.8e-08 |
| Bespoke-MiniCheck-7B | CLAIM | 97.1% [93.2,100.0] (100/103) | 67.3% [58.9,76.6] (72/107) | 95.3% [90.7,99.1] (102/107) | 96.8% [92.6,100.0] (92/95) | 80.0% [70.7,89.3] (60/75) | True | 107 (0 drop) | 1.19e-07 |
| Bespoke-MiniCheck-7B | EVID | NA | 36.4% [27.1,45.8] (39/107) | 67.3% [57.9,75.7] (72/107) | 95.8% [91.6,98.9] (91/95) | 38.7% [28.0,49.3] (29/75) | None | 107 (0 drop) | 2.54e-08 |

## Secondary — LLM judges (non-primary; same splits)

| Model | Side | NS_x10 FAIL | US_up before | US_up after | NS_div10 | US_down | Bind? | n paired | p≈ |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0% [100.0,100.0] (103/103) | 99.1% [97.2,100.0] (106/107) | 99.1% [97.2,100.0] (106/107) | 100.0% [100.0,100.0] (95/95) | 100.0% [100.0,100.0] (75/75) | True | 107 (0 drop) | 0.48 |
| Mistral-Small-24B (MedScore) | EVID | 93.2% [88.3,98.1] (96/103) | 59.8% [50.5,69.2] (64/107) | 88.8% [82.2,94.4] (95/107) | 98.9% [96.8,100.0] (94/95) | 93.3% [86.7,98.7] (70/75) | True | 107 (0 drop) | 1.77e-07 |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 100.0% [100.0,100.0] (102/102) | 100.0% [100.0,100.0] (104/104) | 97.2% [93.4,100.0] (103/106) | 97.9% [94.7,100.0] (93/95) | 89.2% [81.1,95.9] (66/74) | True | 104 (3 drop) | 0.248 |
| Llama-3.3-70B (RAGAS NLI) | EVID | 91.2% [85.3,96.1] (93/102) | 82.1% [74.5,89.6] (87/106) | 84.9% [77.4,91.5] (90/106) | 93.5% [88.2,97.8] (87/93) | 62.2% [51.4,73.0] (46/74) | True | 106 (1 drop) | 0.646 |
| Claude Sonnet 4.6 (RAGAS NLI) | CLAIM | 100.0% [100.0,100.0] (103/103) | 98.1% [95.3,100.0] (105/107) | NA | 100.0% [100.0,100.0] (95/95) | 100.0% [100.0,100.0] (75/75) | None | 0 (107 drop) | — |
| Claude Sonnet 4.6 (RAGAS NLI) | EVID | 98.1% [95.1,100.0] (101/103) | 68.2% [58.9,76.6] (73/107) | NA | 98.9% [96.8,100.0] (94/95) | 93.3% [86.7,98.7] (70/75) | None | 0 (107 drop) | — |

## V4 denominator reconciliation (7338b21 pooled bug)

- **7338b21** pooled E1-unit-claim + E1-unit-evid under one bootstrap → US_up before ≈ **91.0%** (191/210 FAIL instances).
- **Correct (EVID only, |C0 PASS|, parsed):** **82.1% [74.5,89.6] (87/106)** — matches repair report **n_paired≈114** on E1-unit-evid.
- **Card/repair (~55.8% PASS / 61 FAIL):** same **evid-only** cohort; 7338b21 **91.1%** was **FAIL rate on pooled 203**, not PASS.


## NeMo Guardrails (T9) — after non-dose base exclusion

Group **d** = T7 E1-unit (unit errors); group **c** = E1-claim ×2 (value errors). Rail blocks when AlignScore < 0.5. **Value-error detection** = blocked k/n; **unit pass-through** = not blocked k/n (177/230 raw = errors slipping past rail).

| Checkpoint | Slice | n | blocked k/n [CI] | not blocked k/n |
| --- | --- | ---: | --- | --- |
| AlignScore-base | unit-error (d) | 216 | **44/216** (0.204)  | 172/216 |
| AlignScore-base | value-error (c) | 110 | **108/110** (0.982)  | 2/110 |
| AlignScore-large | unit-error (d) | 216 | **107/216** (0.495)  | 109/216 |
| AlignScore-large | value-error (c) | 110 | **108/110** (0.982)  | 2/110 |


## Dual cohort (amendment 4)

- **Pre-amendment-4 draft** (`pre_amendment4`, job 61606): gate bases **104** — `results/tables/m1_strong_pre_amendment4.md`
- **Post-amendment-4 final** (`post_amendment4_fixed_gate`): gate bases **110** — this file.

