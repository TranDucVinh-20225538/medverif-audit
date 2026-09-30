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

Paired rule: a pair needs a parsed BEFORE and a parsed AFTER-M1 verdict on a gated row of a C0-PASS base; rows missing either score are excluded, never counted as PASS. `n` = n_pairs / n_after_scored / n_after_missing (of gated candidates). b = PASS→FAIL, c = FAIL→PASS (McNemar, continuity-corrected).

### US_up (×1000) vs NS_x10

| Model | Side | NS_x10 FAIL | US_up before | US_up after | n | b/c | p≈ | Bind up |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| MiniCheck-RoBERTa | CLAIM | 94.6% [89.1,98.9] (87/92) | 33.3% [25.0,42.7] (32/96) | 80.2% [71.9,87.5] (77/96) | 96 / 96 / 0 | 47/2 | 3.26e-10 | False |
| MiniCheck-RoBERTa | EVID | 92.4% [87.0,97.8] (85/92) | 20.8% [13.5,29.2] (20/96) | 68.8% [59.4,77.1] (66/96) | 96 / 96 / 0 | 47/1 | 8.29e-11 | False |
| MiniCheck-DeBERTa | CLAIM | 96.8% [92.5,100.0] (90/93) | 86.5% [80.2,92.7] (83/96) | 89.6% [83.3,94.8] (86/96) | 96 / 96 / 0 | 6/3 | 0.505 | True |
| MiniCheck-DeBERTa | EVID | 93.5% [88.2,97.8] (87/93) | 71.9% [63.5,80.2] (69/96) | 58.3% [47.9,67.7] (56/96) | 96 / 96 / 0 | 6/19 | 0.0164 | False |
| MiniCheck-Flan-T5-Large | CLAIM | 94.9% [89.9,99.0] (94/99) | 52.4% [42.7,61.2] (54/103) | 82.5% [74.8,89.3] (85/103) | 103 / 103 / 0 | 31/0 | 7.12e-08 | False |
| MiniCheck-Flan-T5-Large | EVID | 83.8% [75.8,90.9] (83/99) | 21.4% [14.6,29.1] (22/103) | 45.6% [36.9,55.3] (47/103) | 103 / 103 / 0 | 33/8 | 0.000178 | False |
| AlignScore-base | CLAIM | 91.6% [85.3,96.8] (87/95) | 12.1% [6.1,19.2] (12/99) | 74.7% [65.7,82.8] (74/99) | 99 / 99 / 0 | 62/0 | 9.41e-15 | False |
| AlignScore-base | EVID | 90.5% [84.2,95.8] (86/95) | 16.2% [9.1,23.3] (16/99) | 53.5% [43.4,62.7] (53/99) | 99 / 99 / 0 | 39/2 | 1.88e-08 | False |
| AlignScore-large | CLAIM | 96.9% [92.8,100.0] (94/97) | 53.5% [43.6,63.4] (54/101) | 87.1% [80.2,93.1] (88/101) | 101 / 101 / 0 | 34/0 | 1.52e-08 | True |
| AlignScore-large | EVID | 89.7% [83.5,94.8] (87/97) | 40.6% [31.7,50.5] (41/101) | 69.3% [60.4,78.2] (70/101) | 101 / 101 / 0 | 30/1 | 4.93e-07 | False |
| SummaC-ZS | CLAIM | 95.1% [90.2,98.8] (78/82) | 27.1% [17.6,36.5] (23/85) | 69.4% [58.8,78.8] (59/85) | 85 / 85 / 0 | 36/0 | 5.43e-09 | False |
| SummaC-ZS | EVID | 93.9% [89.0,98.8] (77/82) | 23.5% [15.3,31.8] (20/85) | 63.5% [52.9,73.0] (54/85) | 85 / 85 / 0 | 35/1 | 3.8e-08 | False |
| Granite Guardian 2B | CLAIM | 86.3% [79.4,93.1] (88/102) | 43.4% [34.0,52.8] (46/106) | 90.6% [84.9,96.2] (96/106) | 106 / 106 / 0 | 50/0 | 4.22e-12 | True |
| Granite Guardian 2B | EVID | 68.6% [59.8,77.5] (70/102) | 20.8% [13.2,28.3] (22/106) | 67.0% [57.5,76.4] (71/106) | 106 / 106 / 0 | 49/0 | 7.03e-12 | True |
| Bespoke-MiniCheck-7B | CLAIM | 97.1% [93.2,100.0] (100/103) | 67.3% [58.9,76.6] (72/107) | 95.3% [90.7,99.1] (102/107) | 107 / 107 / 0 | 30/0 | 1.19e-07 | True |
| Bespoke-MiniCheck-7B | EVID | 89.3% [82.5,95.1] (92/103) | 36.4% [27.1,45.8] (39/107) | 67.3% [57.9,75.7] (72/107) | 107 / 107 / 0 | 33/0 | 2.54e-08 | False |

### US_down (unit-down) vs NS_div10

| Model | Side | NS_div10 FAIL | US_down before | US_down after | n | b/c | p≈ | Bind down |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| MiniCheck-RoBERTa | CLAIM | 97.7% [94.2,100.0] (84/86) | 7.1% [1.4,12.9] (5/70) | 95.7% [90.0,100.0] (67/70) | 70 / 70 / 0 | 63/1 | 2.44e-14 | True |
| MiniCheck-RoBERTa | EVID | 96.5% [91.9,100.0] (83/86) | 5.7% [1.4,11.4] (4/70) | 95.7% [90.0,100.0] (67/70) | 70 / 70 / 0 | 63/0 | 5.66e-15 | True |
| MiniCheck-DeBERTa | CLAIM | 98.9% [96.6,100.0] (86/87) | 88.6% [81.4,95.7] (62/70) | 98.6% [95.7,100.0] (69/70) | 70 / 70 / 0 | 8/1 | 0.0455 | True |
| MiniCheck-DeBERTa | EVID | 94.3% [88.5,98.9] (82/87) | 80.0% [71.4,88.6] (56/70) | 97.1% [92.9,100.0] (68/70) | 70 / 70 / 0 | 12/0 | 0.0015 | True |
| MiniCheck-Flan-T5-Large | CLAIM | 92.4% [87.0,97.8] (85/92) | 5.4% [1.4,10.8] (4/74) | 91.9% [85.1,97.3] (68/74) | 74 / 74 / 0 | 64/0 | 3.41e-15 | True |
| MiniCheck-Flan-T5-Large | EVID | 87.0% [79.3,93.5] (80/92) | 8.1% [2.7,14.9] (6/74) | 97.3% [93.2,100.0] (72/74) | 74 / 74 / 0 | 66/0 | 1.23e-15 | True |
| AlignScore-base | CLAIM | 90.9% [84.1,96.6] (80/88) | 7.0% [1.4,14.1] (5/71) | 90.1% [83.1,97.2] (64/71) | 71 / 71 / 0 | 59/0 | 4.32e-14 | True |
| AlignScore-base | EVID | 90.9% [84.1,96.6] (80/88) | 9.9% [4.2,16.9] (7/71) | 94.4% [88.7,98.6] (67/71) | 71 / 71 / 0 | 60/0 | 2.6e-14 | True |
| AlignScore-large | CLAIM | 94.4% [88.9,98.9] (85/90) | 12.2% [5.4,18.9] (9/74) | 91.9% [85.1,97.3] (68/74) | 74 / 74 / 0 | 59/0 | 4.32e-14 | True |
| AlignScore-large | EVID | 96.7% [92.2,100.0] (87/90) | 10.8% [4.1,17.6] (8/74) | 95.9% [91.9,100.0] (71/74) | 74 / 74 / 0 | 63/0 | 5.66e-15 | True |
| SummaC-ZS | CLAIM | 91.0% [84.6,97.4] (71/78) | 6.5% [1.6,12.9] (4/62) | 93.5% [87.1,98.4] (58/62) | 62 / 62 / 0 | 54/0 | 5.5e-13 | True |
| SummaC-ZS | EVID | 92.3% [85.9,97.4] (72/78) | 4.8% [0.0,11.3] (3/62) | 90.3% [82.3,96.8] (56/62) | 62 / 62 / 0 | 53/0 | 9.15e-13 | True |
| Granite Guardian 2B | CLAIM | 74.5% [64.9,83.0] (70/94) | 29.7% [20.3,40.5] (22/74) | 89.2% [81.1,95.9] (66/74) | 74 / 74 / 0 | 44/0 | 9.02e-11 | True |
| Granite Guardian 2B | EVID | 68.1% [58.5,76.6] (64/94) | 23.0% [13.5,33.8] (17/74) | 87.8% [79.7,94.6] (65/74) | 74 / 74 / 0 | 48/0 | 1.17e-11 | True |
| Bespoke-MiniCheck-7B | CLAIM | 96.8% [92.6,100.0] (92/95) | 80.0% [70.7,89.3] (60/75) | 96.0% [90.7,100.0] (72/75) | 75 / 75 / 0 | 12/0 | 0.0015 | True |
| Bespoke-MiniCheck-7B | EVID | 95.8% [91.6,98.9] (91/95) | 38.7% [28.0,49.3] (29/75) | 85.3% [76.0,93.3] (64/75) | 75 / 75 / 0 | 35/0 | 9.08e-09 | True |

### Bind? (criterion uses AFTER values only)

Side = Bind up AND Bind down, where Bind up compares **US_up after** with NS_x10 and Bind down compares **US_down after** with NS_div10 (pass if after >= NS - 5 points, or 95% CIs overlap). None = an input is NA (e.g. after-M1 scores missing).

| Model | CLAIM (up, down → side) | EVID (up, down → side) | Overall |
| --- | --- | --- | --- |
| MiniCheck-RoBERTa | False, True → **False** | False, True → **False** | **False** |
| MiniCheck-DeBERTa | True, True → **True** | False, True → **False** | **False** |
| MiniCheck-Flan-T5-Large | False, True → **False** | False, True → **False** | **False** |
| AlignScore-base | False, True → **False** | False, True → **False** | **False** |
| AlignScore-large | True, True → **True** | False, True → **False** | **False** |
| SummaC-ZS | False, True → **False** | False, True → **False** | **False** |
| Granite Guardian 2B | True, True → **True** | True, True → **True** | **True** |
| Bespoke-MiniCheck-7B | True, True → **True** | False, True → **False** | **False** |

## Secondary — LLM judges (non-primary; same splits)

Paired rule: a pair needs a parsed BEFORE and a parsed AFTER-M1 verdict on a gated row of a C0-PASS base; rows missing either score are excluded, never counted as PASS. `n` = n_pairs / n_after_scored / n_after_missing (of gated candidates). b = PASS→FAIL, c = FAIL→PASS (McNemar, continuity-corrected).

### US_up (×1000) vs NS_x10

| Model | Side | NS_x10 FAIL | US_up before | US_up after | n | b/c | p≈ | Bind up |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0% [100.0,100.0] (103/103) | 99.1% [97.2,100.0] (106/107) | 99.1% [97.2,100.0] (106/107) | 107 / 107 / 0 | 1/1 | 0.48 | True |
| Mistral-Small-24B (MedScore) | EVID | 93.2% [88.3,98.1] (96/103) | 59.8% [50.5,69.2] (64/107) | 88.8% [82.2,94.4] (95/107) | 107 / 107 / 0 | 32/1 | 1.77e-07 | True |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 99.0% [97.1,100.0] (102/103) | 92.5% [86.8,97.2] (98/106) | 97.2% [93.4,100.0] (103/106) | 106 / 107 / 0 | 7/2 | 0.182 | True |
| Llama-3.3-70B (RAGAS NLI) | EVID | 90.3% [83.5,96.1] (93/103) | 53.8% [44.3,63.2] (57/106) | 84.9% [77.4,91.5] (90/106) | 106 / 106 / 1 | 37/4 | 5.81e-07 | True |
| Claude Sonnet 4.6 (RAGAS NLI) | CLAIM | 100.0% [100.0,100.0] (103/103) | NA | NA | 0 / 0 / 107 | 0/0 | — | None |
| Claude Sonnet 4.6 (RAGAS NLI) | EVID | 98.1% [95.1,100.0] (101/103) | NA | NA | 0 / 0 / 107 | 0/0 | — | None |

### US_down (unit-down) vs NS_div10

| Model | Side | NS_div10 FAIL | US_down before | US_down after | n | b/c | p≈ | Bind down |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0% [100.0,100.0] (95/95) | 100.0% [100.0,100.0] (75/75) | 100.0% [100.0,100.0] (75/75) | 75 / 75 / 0 | 0/0 | — | True |
| Mistral-Small-24B (MedScore) | EVID | 98.9% [96.8,100.0] (94/95) | 93.3% [86.7,98.7] (70/75) | 96.0% [90.7,100.0] (72/75) | 75 / 75 / 0 | 3/1 | 0.617 | True |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 97.9% [94.7,100.0] (93/95) | 89.3% [81.3,96.0] (67/75) | 100.0% [100.0,100.0] (75/75) | 75 / 75 / 0 | 8/0 | 0.0133 | True |
| Llama-3.3-70B (RAGAS NLI) | EVID | 93.5% [88.2,97.8] (87/93) | 62.7% [52.0,73.3] (47/75) | 98.7% [96.0,100.0] (74/75) | 75 / 75 / 0 | 27/0 | 5.62e-07 | True |
| Claude Sonnet 4.6 (RAGAS NLI) | CLAIM | 100.0% [100.0,100.0] (95/95) | NA | NA | 0 / 0 / 75 | 0/0 | — | None |
| Claude Sonnet 4.6 (RAGAS NLI) | EVID | 98.9% [96.8,100.0] (94/95) | NA | NA | 0 / 0 / 75 | 0/0 | — | None |

### Bind? (criterion uses AFTER values only)

Side = Bind up AND Bind down, where Bind up compares **US_up after** with NS_x10 and Bind down compares **US_down after** with NS_div10 (pass if after >= NS - 5 points, or 95% CIs overlap). None = an input is NA (e.g. after-M1 scores missing).

| Model | CLAIM (up, down → side) | EVID (up, down → side) | Overall |
| --- | --- | --- | --- |
| Mistral-Small-24B (MedScore) | True, True → **True** | True, True → **True** | **True** |
| Llama-3.3-70B (RAGAS NLI) | True, True → **True** | True, True → **True** | **True** |
| Claude Sonnet 4.6 (RAGAS NLI) | None, None → **None** | None, None → **None** | **None** |

## V4 denominator reconciliation (7338b21 pooled bug)

- **7338b21** pooled E1-unit-claim + E1-unit-evid under one bootstrap → US_up before ≈ **73.2%** (156/213 FAIL instances).
- **Correct (EVID only, |C0 PASS|, parsed):** **54.2% [43.9,63.6] (58/107)** — matches repair report **n_paired≈114** on E1-unit-evid.
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

