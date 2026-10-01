# M1-strong: pre-amendment-5 vs amendment-5 (side by side)

Sources: `results/tables/m1_strong_final.md` (pre-amendment-5) and `results/tables/m1_strong_final_amend5.md` (amendment 5). Each cell is `pre → **amend5**` when it changed, otherwise one value. Rates are % FAIL (k/n); 95% cluster-bootstrap CIs are in the source tables. n = paired rows; b/c = PASS→FAIL / FAIL→PASS. MiniCheck-DeBERTa's pre-amendment-5 values are the node30 scores; amendment 5 uses the cpuverif scores (approved swap), so its NS and before cells move too.

## US_up (×1000) vs NS_x10

| Checker | Side | NS_x10 | before | after | n | b/c | Bind |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MiniCheck-RoBERTa | CLAIM | 94.6 (87/92) | 33.3 (32/96) | 80.2 (77/96) → **93.8 (90/96)** | 96 | 47/2 → **59/1** | False → **True** |
| MiniCheck-RoBERTa | EVID | 92.4 (85/92) | 20.8 (20/96) | 68.8 (66/96) → **83.3 (80/96)** | 96 | 47/1 → **61/1** | False → **True** |
| MiniCheck-DeBERTa | CLAIM | 96.8 (90/93) → **96.7 (89/92)** | 86.5 (83/96) → **86.3 (82/95)** | 89.6 (86/96) → **93.7 (89/95)** | 96 → **95** | 6/3 → **11/4** | True |
| MiniCheck-DeBERTa | EVID | 93.5 (87/93) → **93.5 (86/92)** | 71.9 (69/96) → **72.6 (69/95)** | 58.3 (56/96) → **58.9 (56/95)** | 96 → **95** | 6/19 → **9/22** | False |
| MiniCheck-Flan-T5-Large | CLAIM | 94.9 (94/99) | 52.4 (54/103) | 82.5 (85/103) → **96.1 (99/103)** | 103 | 31/0 → **45/0** | False → **True** |
| MiniCheck-Flan-T5-Large | EVID | 83.8 (83/99) | 21.4 (22/103) | 45.6 (47/103) → **55.3 (57/103)** | 103 | 33/8 → **43/8** | False |
| AlignScore-base | CLAIM | 91.6 (87/95) | 12.1 (12/99) | 74.7 (74/99) → **88.9 (88/99)** | 99 | 62/0 → **76/0** | False → **True** |
| AlignScore-base | EVID | 90.5 (86/95) | 16.2 (16/99) | 53.5 (53/99) → **63.6 (63/99)** | 99 | 39/2 → **49/2** | False |
| AlignScore-large | CLAIM | 96.9 (94/97) | 53.5 (54/101) | 87.1 (88/101) → **97.0 (98/101)** | 101 | 34/0 → **44/0** | True |
| AlignScore-large | EVID | 89.7 (87/97) | 40.6 (41/101) | 69.3 (70/101) → **81.2 (82/101)** | 101 | 30/1 → **42/1** | False → **True** |
| SummaC-ZS | CLAIM | 95.1 (78/82) | 27.1 (23/85) | 69.4 (59/85) → **87.1 (74/85)** | 85 | 36/0 → **51/0** | False → **True** |
| SummaC-ZS | EVID | 93.9 (77/82) | 23.5 (20/85) | 63.5 (54/85) → **81.2 (69/85)** | 85 | 35/1 → **50/1** | False → **True** |
| Granite Guardian 2B | CLAIM | 86.3 (88/102) | 43.4 (46/106) | 90.6 (96/106) → **98.1 (104/106)** | 106 | 50/0 → **58/0** | True |
| Granite Guardian 2B | EVID | 68.6 (70/102) | 20.8 (22/106) | 67.0 (71/106) → **78.3 (83/106)** | 106 | 49/0 → **61/0** | True |
| Bespoke-MiniCheck-7B | CLAIM | 97.1 (100/103) | 67.3 (72/107) | 95.3 (102/107) → **100.0 (107/107)** | 107 | 30/0 → **35/0** | True |
| Bespoke-MiniCheck-7B | EVID | 89.3 (92/103) | 36.4 (39/107) | 67.3 (72/107) → **77.6 (83/107)** | 107 | 33/0 → **44/0** | False → **True** |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0 (103/103) | 99.1 (106/107) | 99.1 (106/107) | 107 | 1/1 | True |
| Mistral-Small-24B (MedScore) | EVID | 93.2 (96/103) | 59.8 (64/107) | 88.8 (95/107) → **92.5 (99/107)** | 107 | 32/1 → **36/1** | True |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 99.0 (102/103) | 92.5 (98/106) | 97.2 (103/106) → **99.1 (105/106)** | 106 | 7/2 → **7/0** | True |
| Llama-3.3-70B (RAGAS NLI) | EVID | 90.3 (93/103) | 53.8 (57/106) | 84.9 (90/106) → **87.7 (93/106)** | 106 | 37/4 → **39/3** | True |
| Claude Sonnet 4.6 (RAGAS NLI) | CLAIM | 100.0 (103/103) | NA | NA | 0 | 0/0 | None |
| Claude Sonnet 4.6 (RAGAS NLI) | EVID | 98.1 (101/103) | NA | NA | 0 | 0/0 | None |

## US_down (unit-down) vs NS_div10

| Checker | Side | NS_div10 | before | after | n | b/c | Bind |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MiniCheck-RoBERTa | CLAIM | 97.7 (84/86) | 7.1 (5/70) | 95.7 (67/70) | 70 | 63/1 | True |
| MiniCheck-RoBERTa | EVID | 96.5 (83/86) | 5.7 (4/70) | 95.7 (67/70) | 70 | 63/0 | True |
| MiniCheck-DeBERTa | CLAIM | 98.9 (86/87) → **98.8 (85/86)** | 88.6 (62/70) → **88.4 (61/69)** | 98.6 (69/70) → **98.6 (68/69)** | 70 → **69** | 8/1 | True |
| MiniCheck-DeBERTa | EVID | 94.3 (82/87) → **94.2 (81/86)** | 80.0 (56/70) → **79.7 (55/69)** | 97.1 (68/70) → **97.1 (67/69)** | 70 → **69** | 12/0 | True |
| MiniCheck-Flan-T5-Large | CLAIM | 92.4 (85/92) | 5.4 (4/74) | 91.9 (68/74) | 74 | 64/0 | True |
| MiniCheck-Flan-T5-Large | EVID | 87.0 (80/92) | 8.1 (6/74) | 97.3 (72/74) | 74 | 66/0 | True |
| AlignScore-base | CLAIM | 90.9 (80/88) | 7.0 (5/71) | 90.1 (64/71) | 71 | 59/0 | True |
| AlignScore-base | EVID | 90.9 (80/88) | 9.9 (7/71) | 94.4 (67/71) | 71 | 60/0 | True |
| AlignScore-large | CLAIM | 94.4 (85/90) | 12.2 (9/74) | 91.9 (68/74) | 74 | 59/0 | True |
| AlignScore-large | EVID | 96.7 (87/90) | 10.8 (8/74) | 95.9 (71/74) | 74 | 63/0 | True |
| SummaC-ZS | CLAIM | 91.0 (71/78) | 6.5 (4/62) | 93.5 (58/62) | 62 | 54/0 | True |
| SummaC-ZS | EVID | 92.3 (72/78) | 4.8 (3/62) | 90.3 (56/62) | 62 | 53/0 | True |
| Granite Guardian 2B | CLAIM | 74.5 (70/94) | 29.7 (22/74) | 89.2 (66/74) | 74 | 44/0 | True |
| Granite Guardian 2B | EVID | 68.1 (64/94) | 23.0 (17/74) | 87.8 (65/74) | 74 | 48/0 | True |
| Bespoke-MiniCheck-7B | CLAIM | 96.8 (92/95) | 80.0 (60/75) | 96.0 (72/75) | 75 | 12/0 | True |
| Bespoke-MiniCheck-7B | EVID | 95.8 (91/95) | 38.7 (29/75) | 85.3 (64/75) | 75 | 35/0 | True |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0 (95/95) | 100.0 (75/75) | 100.0 (75/75) | 75 | 0/0 | True |
| Mistral-Small-24B (MedScore) | EVID | 98.9 (94/95) | 93.3 (70/75) | 96.0 (72/75) | 75 | 3/1 | True |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 97.9 (93/95) | 89.3 (67/75) | 100.0 (75/75) | 75 | 8/0 | True |
| Llama-3.3-70B (RAGAS NLI) | EVID | 93.5 (87/93) | 62.7 (47/75) | 98.7 (74/75) | 75 | 27/0 | True |
| Claude Sonnet 4.6 (RAGAS NLI) | CLAIM | 100.0 (95/95) | NA | NA | 0 | 0/0 | None |
| Claude Sonnet 4.6 (RAGAS NLI) | EVID | 98.9 (94/95) | NA | NA | 0 | 0/0 | None |

## Bind (up, down → side)

| Checker | CLAIM | EVID | Overall |
| --- | --- | --- | --- |
| MiniCheck-RoBERTa | False → **True** | False → **True** | False → **True** |
| MiniCheck-DeBERTa | True | False | False |
| MiniCheck-Flan-T5-Large | False → **True** | False | False |
| AlignScore-base | False → **True** | False | False |
| AlignScore-large | True | False → **True** | False → **True** |
| SummaC-ZS | False → **True** | False → **True** | False → **True** |
| Granite Guardian 2B | True | True | True |
| Bespoke-MiniCheck-7B | True | False → **True** | False → **True** |
| Mistral-Small-24B (MedScore) | True | True | True |
| Llama-3.3-70B (RAGAS NLI) | True | True | True |
| Claude Sonnet 4.6 (RAGAS NLI) | None | None | None |
