# m1_strong_final: every changed cell (old → new)

Original = accepted `m1_strong_final` (`8939e6c`). Corrected table: `results/tables/m1_strong_final_amend5.md` (`scripts/m1_strong_run.py --final --amend5`). Script: `scripts/m1_strong_amend5_changes.py`.

## Overall binding verdict (criterion on AFTER values)

| Model | CLAIM old → new | EVID old → new | Overall old → new |
| --- | --- | --- | --- |
| MiniCheck-RoBERTa | False, True → **False** → True, True → **True** | False, True → **False** → True, True → **True** | **False** → **True** |
| MiniCheck-DeBERTa | True, True → **True** → True, True → **True** | False, True → **False** → False, True → **False** | **False** → **False** |
| MiniCheck-Flan-T5-Large | False, True → **False** → True, True → **True** | False, True → **False** → False, True → **False** | **False** → **False** |
| AlignScore-base | False, True → **False** → True, True → **True** | False, True → **False** → False, True → **False** | **False** → **False** |
| AlignScore-large | True, True → **True** → True, True → **True** | False, True → **False** → True, True → **True** | **False** → **True** |
| SummaC-ZS | False, True → **False** → True, True → **True** | False, True → **False** → True, True → **True** | **False** → **True** |
| Granite Guardian 2B | True, True → **True** → True, True → **True** | True, True → **True** → True, True → **True** | **True** → **True** |
| Bespoke-MiniCheck-7B | True, True → **True** → True, True → **True** | False, True → **False** → True, True → **True** | **False** → **True** |
| Mistral-Small-24B (MedScore) | True, True → **True** → True, True → **True** | True, True → **True** → True, True → **True** | **True** → **True** |
| Llama-3.3-70B (RAGAS NLI) | True, True → **True** → True, True → **True** | True, True → **True** → True, True → **True** | **True** → **True** |
| Claude Sonnet 4.6 (RAGAS NLI) | None, None → **None** → None, None → **None** | None, None → **None** → None, None → **None** | **None** → **None** |

## 1. MiniCheck-DeBERTa scores → cpuverif (reference env)

| Block | Model | Side | Column | Old | New |
| --- | --- | --- | --- | --- | --- |
| US_down (unit-down) | MiniCheck-DeBERTa | CLAIM | NS_div10 FAIL | 98.9% [96.6,100.0] (86/87) | 98.8% [96.5,100.0] (85/86) |
| US_down (unit-down) | MiniCheck-DeBERTa | CLAIM | US_down before | 88.6% [81.4,95.7] (62/70) | 88.4% [79.7,95.7] (61/69) |
| US_down (unit-down) | MiniCheck-DeBERTa | CLAIM | US_down after | 98.6% [95.7,100.0] (69/70) | 98.6% [95.7,100.0] (68/69) |
| US_down (unit-down) | MiniCheck-DeBERTa | CLAIM | n | 70 / 70 / 0 | 69 / 69 / 0 |
| US_down (unit-down) | MiniCheck-DeBERTa | EVID | NS_div10 FAIL | 94.3% [88.5,98.9] (82/87) | 94.2% [88.4,98.8] (81/86) |
| US_down (unit-down) | MiniCheck-DeBERTa | EVID | US_down before | 80.0% [71.4,88.6] (56/70) | 79.7% [69.6,88.4] (55/69) |
| US_down (unit-down) | MiniCheck-DeBERTa | EVID | US_down after | 97.1% [92.9,100.0] (68/70) | 97.1% [92.8,100.0] (67/69) |
| US_down (unit-down) | MiniCheck-DeBERTa | EVID | n | 70 / 70 / 0 | 69 / 69 / 0 |
| US_up (×1000) | MiniCheck-DeBERTa | CLAIM | NS_x10 FAIL | 96.8% [92.5,100.0] (90/93) | 96.7% [92.4,100.0] (89/92) |
| US_up (×1000) | MiniCheck-DeBERTa | CLAIM | US_up before | 86.5% [80.2,92.7] (83/96) | 86.3% [80.0,92.6] (82/95) |
| US_up (×1000) | MiniCheck-DeBERTa | CLAIM | US_up after | 89.6% [83.3,94.8] (86/96) | 89.5% [83.2,94.7] (85/95) |
| US_up (×1000) | MiniCheck-DeBERTa | CLAIM | n | 96 / 96 / 0 | 95 / 95 / 0 |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | NS_x10 FAIL | 93.5% [88.2,97.8] (87/93) | 93.5% [88.0,97.8] (86/92) |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | US_up before | 71.9% [63.5,80.2] (69/96) | 72.6% [63.2,81.1] (69/95) |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | US_up after | 58.3% [47.9,67.7] (56/96) | 57.9% [47.4,67.4] (55/95) |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | n | 96 / 96 / 0 | 95 / 95 / 0 |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | b/c | 6/19 | 5/19 |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | p≈ | 0.0164 | 0.00796 |

## 2. Amendment 5 (84 off-spec after-M1 rows rescored with spec M1 text)

| Block | Model | Side | Column | Old | New |
| --- | --- | --- | --- | --- | --- |
| US_up (×1000) | AlignScore-base | CLAIM | US_up after | 74.7% [65.7,82.8] (74/99) | 88.9% [82.8,94.9] (88/99) |
| US_up (×1000) | AlignScore-base | CLAIM | b/c | 62/0 | 76/0 |
| US_up (×1000) | AlignScore-base | CLAIM | p≈ | 9.41e-15 | 7.76e-18 |
| US_up (×1000) | AlignScore-base | CLAIM | Bind up | False | True |
| US_up (×1000) | AlignScore-base | EVID | US_up after | 53.5% [43.4,62.7] (53/99) | 63.6% [54.5,72.8] (63/99) |
| US_up (×1000) | AlignScore-base | EVID | b/c | 39/2 | 49/2 |
| US_up (×1000) | AlignScore-base | EVID | p≈ | 1.88e-08 | 1.18e-10 |
| US_up (×1000) | AlignScore-large | CLAIM | US_up after | 87.1% [80.2,93.1] (88/101) | 97.0% [93.1,100.0] (98/101) |
| US_up (×1000) | AlignScore-large | CLAIM | b/c | 34/0 | 44/0 |
| US_up (×1000) | AlignScore-large | CLAIM | p≈ | 1.52e-08 | 9.02e-11 |
| US_up (×1000) | AlignScore-large | EVID | US_up after | 69.3% [60.4,78.2] (70/101) | 81.2% [73.3,88.1] (82/101) |
| US_up (×1000) | AlignScore-large | EVID | b/c | 30/1 | 42/1 |
| US_up (×1000) | AlignScore-large | EVID | p≈ | 4.93e-07 | 1.06e-09 |
| US_up (×1000) | AlignScore-large | EVID | Bind up | False | True |
| US_up (×1000) | Bespoke-MiniCheck-7B | CLAIM | US_up after | 95.3% [90.7,99.1] (102/107) | 100.0% [100.0,100.0] (107/107) |
| US_up (×1000) | Bespoke-MiniCheck-7B | CLAIM | b/c | 30/0 | 35/0 |
| US_up (×1000) | Bespoke-MiniCheck-7B | CLAIM | p≈ | 1.19e-07 | 9.08e-09 |
| US_up (×1000) | Bespoke-MiniCheck-7B | EVID | US_up after | 67.3% [57.9,75.7] (72/107) | 77.6% [69.2,84.1] (83/107) |
| US_up (×1000) | Bespoke-MiniCheck-7B | EVID | b/c | 33/0 | 44/0 |
| US_up (×1000) | Bespoke-MiniCheck-7B | EVID | p≈ | 2.54e-08 | 9.02e-11 |
| US_up (×1000) | Bespoke-MiniCheck-7B | EVID | Bind up | False | True |
| US_up (×1000) | Granite Guardian 2B | CLAIM | US_up after | 90.6% [84.9,96.2] (96/106) | 98.1% [95.3,100.0] (104/106) |
| US_up (×1000) | Granite Guardian 2B | CLAIM | b/c | 50/0 | 58/0 |
| US_up (×1000) | Granite Guardian 2B | CLAIM | p≈ | 4.22e-12 | 7.18e-14 |
| US_up (×1000) | Granite Guardian 2B | EVID | US_up after | 67.0% [57.5,76.4] (71/106) | 78.3% [70.8,85.8] (83/106) |
| US_up (×1000) | Granite Guardian 2B | EVID | b/c | 49/0 | 61/0 |
| US_up (×1000) | Granite Guardian 2B | EVID | p≈ | 7.03e-12 | 1.56e-14 |
| US_up (×1000) | Llama-3.3-70B (RAGAS NLI) | CLAIM | US_up after | 97.2% [93.4,100.0] (103/106) | 99.1% [97.2,100.0] (105/106) |
| US_up (×1000) | Llama-3.3-70B (RAGAS NLI) | CLAIM | b/c | 7/2 | 7/0 |
| US_up (×1000) | Llama-3.3-70B (RAGAS NLI) | CLAIM | p≈ | 0.182 | 0.0233 |
| US_up (×1000) | Llama-3.3-70B (RAGAS NLI) | EVID | US_up after | 84.9% [77.4,91.5] (90/106) | 87.7% [81.1,93.4] (93/106) |
| US_up (×1000) | Llama-3.3-70B (RAGAS NLI) | EVID | b/c | 37/4 | 39/3 |
| US_up (×1000) | Llama-3.3-70B (RAGAS NLI) | EVID | p≈ | 5.81e-07 | 6.64e-08 |
| US_up (×1000) | MiniCheck-DeBERTa | CLAIM | US_up after | 89.5% [83.2,94.7] (85/95) | 93.7% [88.4,97.9] (89/95) |
| US_up (×1000) | MiniCheck-DeBERTa | CLAIM | b/c | 6/3 | 11/4 |
| US_up (×1000) | MiniCheck-DeBERTa | CLAIM | p≈ | 0.505 | 0.121 |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | US_up after | 57.9% [47.4,67.4] (55/95) | 58.9% [48.4,68.4] (56/95) |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | b/c | 5/19 | 9/22 |
| US_up (×1000) | MiniCheck-DeBERTa | EVID | p≈ | 0.00796 | 0.0311 |
| US_up (×1000) | MiniCheck-Flan-T5-Large | CLAIM | US_up after | 82.5% [74.8,89.3] (85/103) | 96.1% [92.2,99.0] (99/103) |
| US_up (×1000) | MiniCheck-Flan-T5-Large | CLAIM | b/c | 31/0 | 45/0 |
| US_up (×1000) | MiniCheck-Flan-T5-Large | CLAIM | p≈ | 7.12e-08 | 5.41e-11 |
| US_up (×1000) | MiniCheck-Flan-T5-Large | CLAIM | Bind up | False | True |
| US_up (×1000) | MiniCheck-Flan-T5-Large | EVID | US_up after | 45.6% [36.9,55.3] (47/103) | 55.3% [46.6,65.0] (57/103) |
| US_up (×1000) | MiniCheck-Flan-T5-Large | EVID | b/c | 33/8 | 43/8 |
| US_up (×1000) | MiniCheck-Flan-T5-Large | EVID | p≈ | 0.000178 | 1.93e-06 |
| US_up (×1000) | MiniCheck-RoBERTa | CLAIM | US_up after | 80.2% [71.9,87.5] (77/96) | 93.8% [88.5,97.9] (90/96) |
| US_up (×1000) | MiniCheck-RoBERTa | CLAIM | b/c | 47/2 | 59/1 |
| US_up (×1000) | MiniCheck-RoBERTa | CLAIM | p≈ | 3.26e-10 | 1.86e-13 |
| US_up (×1000) | MiniCheck-RoBERTa | CLAIM | Bind up | False | True |
| US_up (×1000) | MiniCheck-RoBERTa | EVID | US_up after | 68.8% [59.4,77.1] (66/96) | 83.3% [75.0,89.6] (80/96) |
| US_up (×1000) | MiniCheck-RoBERTa | EVID | b/c | 47/1 | 61/1 |
| US_up (×1000) | MiniCheck-RoBERTa | EVID | p≈ | 8.29e-11 | 6.73e-14 |
| US_up (×1000) | MiniCheck-RoBERTa | EVID | Bind up | False | True |
| US_up (×1000) | Mistral-Small-24B (MedScore) | EVID | US_up after | 88.8% [82.2,94.4] (95/107) | 92.5% [86.9,97.2] (99/107) |
| US_up (×1000) | Mistral-Small-24B (MedScore) | EVID | b/c | 32/1 | 36/1 |
| US_up (×1000) | Mistral-Small-24B (MedScore) | EVID | p≈ | 1.77e-07 | 2.28e-08 |
| US_up (×1000) | SummaC-ZS | CLAIM | US_up after | 69.4% [58.8,78.8] (59/85) | 87.1% [80.0,94.1] (74/85) |
| US_up (×1000) | SummaC-ZS | CLAIM | b/c | 36/0 | 51/0 |
| US_up (×1000) | SummaC-ZS | CLAIM | p≈ | 5.43e-09 | 2.53e-12 |
| US_up (×1000) | SummaC-ZS | CLAIM | Bind up | False | True |
| US_up (×1000) | SummaC-ZS | EVID | US_up after | 63.5% [52.9,73.0] (54/85) | 81.2% [71.8,89.4] (69/85) |
| US_up (×1000) | SummaC-ZS | EVID | b/c | 35/1 | 50/1 |
| US_up (×1000) | SummaC-ZS | EVID | p≈ | 3.8e-08 | 1.8e-11 |
| US_up (×1000) | SummaC-ZS | EVID | Bind up | False | True |

