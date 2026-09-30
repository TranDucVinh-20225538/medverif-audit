# Committed tables vs regeneration under current code (before DeBERTa swap): code/loader drift

Snapshot: `/tmp/pre_swap` vs working tree. Script: `scripts/table_change_list.py`.

## `results/tables/dose3_robustness_diff.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| (a) all valid / Bespoke / 78.8% | T7 unit-claim FAIL | 67.9% | 67.3% |
| (a) all valid / Bespoke / 78.8% | T7 unit-evid FAIL | 36.6% | 36.4% |
| (a) all valid / T6B gpt4o-mini / 74.2% | T7 unit-claim FAIL | 92.6% | 92.2% |
| (a) all valid / T6B gpt4o-mini / 74.2% | T7 unit-evid FAIL | 74.1% | 73.8% |
| (a) all valid / T6B haiku4.5 / 96.8% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (a) all valid / T6B haiku4.5 / 96.8% | T7 unit-evid FAIL | 88.1% | 88.5% |
| (a) all valid / T6B llama3.1-8b / 27.4% | T7 unit-claim FAIL | 84.3% | 83.5% |
| (a) all valid / T6B llama3.1-8b / 27.4% | T7 unit-evid FAIL | 49.1% | 47.6% |
| (a) all valid / T6B mistral3.2-24b / 97.0% | T7 unit-claim FAIL | 92.0% | 91.6% |
| (a) all valid / T6B mistral3.2-24b / 97.0% | T7 unit-evid FAIL | 48.2% | 46.7% |
| (a) all valid / V1 / 98.8% | T7 unit-evid FAIL | 90.0% | 89.5% |
| (a) all valid / V1b / 97.0% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (a) all valid / V1b / 97.0% | T7 unit-evid FAIL | 15.2% | 13.1% |
| (a) all valid / V2a / 100.0% | T7 unit-claim FAIL | 50.0% | 52.4% |
| (a) all valid / V2a / 100.0% | T7 unit-evid FAIL | 20.4% | 21.4% |
| (a) all valid / V3 / 100.0% | T7 unit-claim FAIL | 53.3% | 52.9% |
| (a) all valid / V3 / 100.0% | T7 unit-evid FAIL | 42.1% | 40.2% |
| (a) all valid / V4 / 98.8% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (a) all valid / V4 / 98.8% | T7 unit-evid FAIL | 82.7% | 84.8% |
| (a) all valid / V5 / 97.0% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (a) all valid / V5 / 97.0% | T7 unit-evid FAIL | 68.8% | 68.2% |
| (b) excl weak E1 / Bespoke / 78.8% | T7 unit-claim FAIL | 67.9% | 67.3% |
| (b) excl weak E1 / Bespoke / 78.8% | T7 unit-evid FAIL | 36.6% | 36.4% |
| (b) excl weak E1 / T6B gpt4o-mini / 74.2% | T7 unit-claim FAIL | 92.6% | 92.2% |
| (b) excl weak E1 / T6B gpt4o-mini / 74.2% | T7 unit-evid FAIL | 74.1% | 73.8% |
| (b) excl weak E1 / T6B haiku4.5 / 96.8% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (b) excl weak E1 / T6B haiku4.5 / 96.8% | T7 unit-evid FAIL | 88.1% | 88.5% |
| (b) excl weak E1 / T6B llama3.1-8b / 27.4% | T7 unit-claim FAIL | 84.3% | 83.5% |
| (b) excl weak E1 / T6B llama3.1-8b / 27.4% | T7 unit-evid FAIL | 49.1% | 47.6% |
| (b) excl weak E1 / T6B mistral3.2-24b / 97.0% | T7 unit-claim FAIL | 92.0% | 91.6% |
| (b) excl weak E1 / T6B mistral3.2-24b / 97.0% | T7 unit-evid FAIL | 48.2% | 46.7% |
| (b) excl weak E1 / V1 / 98.8% | T7 unit-evid FAIL | 90.0% | 89.5% |
| (b) excl weak E1 / V1b / 97.0% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (b) excl weak E1 / V1b / 97.0% | T7 unit-evid FAIL | 15.2% | 13.1% |
| (b) excl weak E1 / V2a / 100.0% | T7 unit-claim FAIL | 50.0% | 52.4% |
| (b) excl weak E1 / V2a / 100.0% | T7 unit-evid FAIL | 20.4% | 21.4% |
| (b) excl weak E1 / V3 / 100.0% | T7 unit-claim FAIL | 53.3% | 52.9% |
| (b) excl weak E1 / V3 / 100.0% | T7 unit-evid FAIL | 42.1% | 40.2% |
| (b) excl weak E1 / V4 / 98.8% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (b) excl weak E1 / V4 / 98.8% | T7 unit-evid FAIL | 82.7% | 84.8% |
| (b) excl weak E1 / V5 / 97.0% | T7 unit-claim FAIL | 98.2% | 98.1% |
| (b) excl weak E1 / V5 / 97.0% | T7 unit-evid FAIL | 68.8% | 68.2% |
| (c) excl C0 underspec / Bespoke / 81.0% | T7 unit-claim FAIL | 67.7% | 67.0% |
| (c) excl C0 underspec / T6B gpt4o-mini / 75.9% | T7 unit-claim FAIL | 91.3% | 90.8% |
| (c) excl C0 underspec / T6B gpt4o-mini / 75.9% | T7 unit-evid FAIL | 70.7% | 70.1% |
| (c) excl C0 underspec / T6B haiku4.5 / 96.4% | T7 unit-claim FAIL | 97.9% | 97.8% |
| (c) excl C0 underspec / T6B haiku4.5 / 96.4% | T7 unit-evid FAIL | 87.2% | 87.6% |
| (c) excl C0 underspec / T6B llama3.1-8b / 30.9% | T7 unit-claim FAIL | 82.8% | 81.8% |
| (c) excl C0 underspec / T6B llama3.1-8b / 30.9% | T7 unit-evid FAIL | 46.2% | 44.3% |
| (c) excl C0 underspec / T6B mistral3.2-24b / 96.6% | T7 unit-claim FAIL | 91.7% | 91.2% |
| (c) excl C0 underspec / T6B mistral3.2-24b / 96.6% | T7 unit-evid FAIL | 45.8% | 44.0% |
| (c) excl C0 underspec / V1 / 98.6% | T7 unit-evid FAIL | 90.4% | 89.9% |
| (c) excl C0 underspec / V1b / 96.6% | T7 unit-claim FAIL | 97.9% | 97.8% |
| (c) excl C0 underspec / V1b / 96.6% | T7 unit-evid FAIL | 15.6% | 13.2% |
| (c) excl C0 underspec / V2a / 100.0% | T7 unit-claim FAIL | 49.5% | 52.3% |
| (c) excl C0 underspec / V2a / 100.0% | T7 unit-evid FAIL | 21.5% | 22.7% |
| (c) excl C0 underspec / V3 / 100.0% | T7 unit-claim FAIL | 51.1% | 50.6% |
| (c) excl C0 underspec / V3 / 100.0% | T7 unit-evid FAIL | 41.3% | 39.1% |
| (c) excl C0 underspec / V4 / 98.6% | T7 unit-claim FAIL | 97.9% | 97.8% |
| (c) excl C0 underspec / V4 / 98.6% | T7 unit-evid FAIL | 81.9% | 84.3% |
| (c) excl C0 underspec / V5 / 96.6% | T7 unit-claim FAIL | 97.9% | 97.8% |
| (c) excl C0 underspec / V5 / 96.6% | T7 unit-evid FAIL | 66.7% | 65.9% |
| Shifts > 3 pp vs (a) / v2b_bespoke / t7_unit_evid_fail | (row) | — | present |
| Shifts > 3 pp vs (a) / v6_ragas_gpt4o_mini / t7_unit_evid_fail | (a) | 74.07% | 73.79% |
| Shifts > 3 pp vs (a) / v6_ragas_gpt4o_mini / t7_unit_evid_fail | subset | 70.65% | 70.11% |
| Shifts > 3 pp vs (a) / v6_ragas_gpt4o_mini / t7_unit_evid_fail | Δ pp | -3.42 | -3.67 |
| Shifts > 3 pp vs (a) / v6_ragas_llama31_8b / t7_unit_evid_fail | (row) | — | present |

## `results/tables/m1_strong_final_amend5.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| Bind? (criterion uses AFTER values only) / AlignScore-base / False, True → **False** | (row) | present | — |
| Bind? (criterion uses AFTER values only) / AlignScore-base / True, True → **True** | (row) | — | present |
| Bind? (criterion uses AFTER values only) / AlignScore-large / True, True → **True** | EVID (up, down → side) | False, True → **False** | True, True → **True** |
| Bind? (criterion uses AFTER values only) / AlignScore-large / True, True → **True** | Overall | **False** | **True** |
| Bind? (criterion uses AFTER values only) / Bespoke-MiniCheck-7B / True, True → **True** | EVID (up, down → side) | False, True → **False** | True, True → **True** |
| Bind? (criterion uses AFTER values only) / Bespoke-MiniCheck-7B / True, True → **True** | Overall | **False** | **True** |
| Bind? (criterion uses AFTER values only) / Granite Guardian 2B / True, True → **True** | (row) | — | present |
| Bind? (criterion uses AFTER values only) / MiniCheck-Flan-T5-Large / False, True → **False** | (row) | present | — |
| Bind? (criterion uses AFTER values only) / MiniCheck-Flan-T5-Large / True, True → **True** | (row) | — | present |
| Bind? (criterion uses AFTER values only) / SummaC-ZS / False, True → **False** | (row) | present | — |
| Bind? (criterion uses AFTER values only) / SummaC-ZS / True, True → **True** | (row) | — | present |
| US_down (unit-down) vs NS_div10 / Granite Guardian 2B / CLAIM | (row) | — | present |
| US_down (unit-down) vs NS_div10 / Granite Guardian 2B / EVID | (row) | — | present |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | NS_div10 FAIL | 98.9% [96.6,100.0] (86/87) | 98.8% [96.5,100.0] (85/86) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | US_down after | 98.6% [95.7,100.0] (69/70) | 98.6% [95.7,100.0] (68/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | US_down before | 88.6% [81.4,95.7] (62/70) | 88.4% [79.7,95.7] (61/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | n | 70 / 70 / 0 | 69 / 69 / 0 |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | NS_div10 FAIL | 94.3% [88.5,98.9] (82/87) | 94.2% [88.4,98.8] (81/86) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | US_down after | 97.1% [92.9,100.0] (68/70) | 97.1% [92.8,100.0] (67/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | US_down before | 80.0% [71.4,88.6] (56/70) | 79.7% [69.6,88.4] (55/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | n | 70 / 70 / 0 | 69 / 69 / 0 |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | Bind up | False | True |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | US_up after | 74.7% [65.7,82.8] (74/99) | 88.9% [82.8,94.9] (88/99) |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | b/c | 62/0 | 76/0 |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | p≈ | 9.41e-15 | 7.76e-18 |
| US_up (×1000) vs NS_x10 / AlignScore-base / EVID | US_up after | 53.5% [43.4,62.7] (53/99) | 63.6% [54.5,72.8] (63/99) |
| US_up (×1000) vs NS_x10 / AlignScore-base / EVID | b/c | 39/2 | 49/2 |
| US_up (×1000) vs NS_x10 / AlignScore-base / EVID | p≈ | 1.88e-08 | 1.18e-10 |
| US_up (×1000) vs NS_x10 / AlignScore-large / CLAIM | US_up after | 87.1% [80.2,93.1] (88/101) | 97.0% [93.1,100.0] (98/101) |
| US_up (×1000) vs NS_x10 / AlignScore-large / CLAIM | b/c | 34/0 | 44/0 |
| US_up (×1000) vs NS_x10 / AlignScore-large / CLAIM | p≈ | 1.52e-08 | 9.02e-11 |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | Bind up | False | True |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | US_up after | 69.3% [60.4,78.2] (70/101) | 81.2% [73.3,88.1] (82/101) |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | b/c | 30/1 | 42/1 |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | p≈ | 4.93e-07 | 1.06e-09 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / CLAIM | US_up after | 95.3% [90.7,99.1] (102/107) | 100.0% [100.0,100.0] (107/107) |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / CLAIM | b/c | 30/0 | 35/0 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / CLAIM | p≈ | 1.19e-07 | 9.08e-09 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | Bind up | False | True |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | US_up after | 67.3% [57.9,75.7] (72/107) | 77.6% [69.2,84.1] (83/107) |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | b/c | 33/0 | 44/0 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | p≈ | 2.54e-08 | 9.02e-11 |
| US_up (×1000) vs NS_x10 / Granite Guardian 2B / CLAIM | (row) | — | present |
| US_up (×1000) vs NS_x10 / Granite Guardian 2B / EVID | (row) | — | present |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / CLAIM | US_up after | 97.2% [93.4,100.0] (103/106) | 99.1% [97.2,100.0] (105/106) |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / CLAIM | b/c | 7/2 | 7/0 |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / CLAIM | p≈ | 0.182 | 0.0233 |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / EVID | US_up after | 86.8% [80.2,92.5] (92/106) | 87.7% [81.1,93.4] (93/106) |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / EVID | b/c | 38/3 | 39/3 |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / EVID | p≈ | 1.1e-07 | 6.64e-08 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | NS_x10 FAIL | 96.8% [92.5,100.0] (90/93) | 96.7% [92.4,100.0] (89/92) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | US_up after | 92.7% [87.5,96.9] (89/96) | 93.7% [88.4,97.9] (89/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | US_up before | 86.5% [80.2,92.7] (83/96) | 86.3% [80.0,92.6] (82/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | b/c | 9/3 | 11/4 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | n | 96 / 96 / 0 | 95 / 95 / 0 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | p≈ | 0.149 | 0.121 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | NS_x10 FAIL | 93.5% [88.2,97.8] (87/93) | 93.5% [88.0,97.8] (86/92) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | US_up after | 60.4% [51.0,69.8] (58/96) | 58.9% [48.4,68.4] (56/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | US_up before | 71.9% [63.5,80.2] (69/96) | 72.6% [63.2,81.1] (69/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | b/c | 8/19 | 9/22 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | n | 96 / 96 / 0 | 95 / 95 / 0 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | p≈ | 0.0543 | 0.0311 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | Bind up | False | True |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | US_up after | 82.5% [74.8,89.3] (85/103) | 96.1% [92.2,99.0] (99/103) |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | b/c | 31/0 | 45/0 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | p≈ | 7.12e-08 | 5.41e-11 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / EVID | US_up after | 45.6% [36.9,55.3] (47/103) | 55.3% [46.6,65.0] (57/103) |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / EVID | b/c | 33/8 | 43/8 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / EVID | p≈ | 0.000178 | 1.93e-06 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | Bind up | False | True |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | US_up after | 69.4% [58.8,78.8] (59/85) | 87.1% [80.0,94.1] (74/85) |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | b/c | 36/0 | 51/0 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | p≈ | 5.43e-09 | 2.53e-12 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | Bind up | False | True |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | US_up after | 63.5% [52.9,73.0] (54/85) | 81.2% [71.8,89.4] (69/85) |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | b/c | 35/1 | 50/1 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | p≈ | 3.8e-08 | 1.8e-11 |

## `results/tables/polarity_all_verifiers.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| POLARITY — human flip_ok Y (all verifiers) / v1_medscore / 0 | E2 PASS | 21 | 8 |
| POLARITY — human flip_ok Y (all verifiers) / v1_medscore / 0 | n | 25 | 11 |
| POLARITY — human flip_ok Y (all verifiers) / v4_ragas_nli / 0 | (row) | present | — |
| POLARITY — human flip_ok Y (all verifiers) / v4_ragas_nli / 1 | (row) | — | present |

## `results/tables/t14_t3_filter_view.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-base / small fine-tuned checkers | T13 pair(1) | — | 0.909 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-base / small fine-tuned checkers | drop INV | — | 0.773 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-base / small fine-tuned checkers | keep ×1000 | 0.795 | 0.822 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-base / small fine-tuned checkers | n INV | 0 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-base / small fine-tuned checkers | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-large / small fine-tuned checkers | T13 pair(1) | 0.764 | 0.773 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-large / small fine-tuned checkers | drop INV | 0.764 | 0.818 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-large / small fine-tuned checkers | keep ×1000 | 0.446 | 0.449 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-large / small fine-tuned checkers | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / AlignScore-large / small fine-tuned checkers | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Bespoke-MiniCheck-7B / 7B fine-tuned checker | T13 pair(1) | 0.200 | 0.227 |
| T14 / T3 filter view (#3 — existing scores only) / Bespoke-MiniCheck-7B / 7B fine-tuned checker | drop INV | 0.200 | 0.182 |
| T14 / T3 filter view (#3 — existing scores only) / Bespoke-MiniCheck-7B / 7B fine-tuned checker | keep ×1000 | 0.321 | 0.327 |
| T14 / T3 filter view (#3 — existing scores only) / Bespoke-MiniCheck-7B / 7B fine-tuned checker | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / Bespoke-MiniCheck-7B / 7B fine-tuned checker | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Haiku 4.5 (RAGAS) / LLM judges | T13 pair(1) | 0.045 | 0.000 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Haiku 4.5 (RAGAS) / LLM judges | drop INV | 0.055 | 0.000 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Haiku 4.5 (RAGAS) / LLM judges | keep ×1000 | 0.018 | 0.019 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Haiku 4.5 (RAGAS) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Haiku 4.5 (RAGAS) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Sonnet 4.6 (RAGAS NLI) / LLM judges | T13 pair(1) | 0.036 | 0.000 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Sonnet 4.6 (RAGAS NLI) / LLM judges | drop INV | 0.036 | 0.000 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Sonnet 4.6 (RAGAS NLI) / LLM judges | keep ×1000 | 0.018 | 0.019 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Sonnet 4.6 (RAGAS NLI) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / Claude Sonnet 4.6 (RAGAS NLI) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o (MedScore) / LLM judges | T13 pair(1) | 0.036 | 0.000 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o (MedScore) / LLM judges | drop INV | 0.036 | 0.000 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o (MedScore) / LLM judges | keep ×1000 | 0.018 | 0.019 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o (MedScore) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o (MedScore) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (MedScore) / LLM judges | T13 pair(1) | 0.336 | 0.318 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (MedScore) / LLM judges | drop INV | 0.509 | 0.500 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (MedScore) / LLM judges | keep ×1000 | 0.107 | 0.112 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (MedScore) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (MedScore) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (RAGAS) / LLM judges | T13 pair(1) | 0.173 | 0.114 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (RAGAS) / LLM judges | drop INV | 0.236 | 0.136 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (RAGAS) / LLM judges | keep ×1000 | 0.071 | 0.075 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (RAGAS) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / GPT-4o-mini (RAGAS) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Granite Guardian / small fine-tuned checkers | (row) | present | — |
| T14 / T3 filter view (#3 — existing scores only) / Granite Guardian 2B / small fine-tuned checkers | (row) | — | present |
| T14 / T3 filter view (#3 — existing scores only) / HHEM / small fine-tuned checkers | T13 pair(1) | — | 1.000 |
| T14 / T3 filter view (#3 — existing scores only) / HHEM / small fine-tuned checkers | drop INV | — | 0.864 |
| T14 / T3 filter view (#3 — existing scores only) / HHEM / small fine-tuned checkers | keep ×1000 | 0.964 | 0.963 |
| T14 / T3 filter view (#3 — existing scores only) / HHEM / small fine-tuned checkers | n INV | 0 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / HHEM / small fine-tuned checkers | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.1-8B (RAGAS) / LLM judges | T13 pair(1) | 0.509 | 0.500 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.1-8B (RAGAS) / LLM judges | drop INV | 0.764 | 0.727 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.1-8B (RAGAS) / LLM judges | keep ×1000 | 0.152 | 0.159 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.1-8B (RAGAS) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.1-8B (RAGAS) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.3-70B (RAGAS NLI) / LLM judges | T13 pair(1) | 0.132 | 0.262 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.3-70B (RAGAS NLI) / LLM judges | drop INV | 0.226 | 0.273 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.3-70B (RAGAS NLI) / LLM judges | keep ×1000 | 0.027 | 0.075 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.3-70B (RAGAS NLI) / LLM judges | n INV | 53 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / Llama-3.3-70B (RAGAS NLI) / LLM judges | n ×1000 | 112 | 106 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-DeBERTa / small fine-tuned checkers | T13 pair(1) | — | 0.909 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-DeBERTa / small fine-tuned checkers | drop INV | — | 0.955 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-DeBERTa / small fine-tuned checkers | keep ×1000 | 0.125 | 0.121 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-DeBERTa / small fine-tuned checkers | n INV | 0 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-DeBERTa / small fine-tuned checkers | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-Flan-T5-Large / small fine-tuned checkers | T13 pair(1) | 0.800 | 0.955 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-Flan-T5-Large / small fine-tuned checkers | drop INV | 0.909 | 0.955 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-Flan-T5-Large / small fine-tuned checkers | keep ×1000 | 0.482 | 0.458 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-Flan-T5-Large / small fine-tuned checkers | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-Flan-T5-Large / small fine-tuned checkers | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-RoBERTa / small fine-tuned checkers | T13 pair(1) | — | 1.000 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-RoBERTa / small fine-tuned checkers | drop INV | — | 1.000 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-RoBERTa / small fine-tuned checkers | n INV | 0 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / MiniCheck-RoBERTa / small fine-tuned checkers | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Mistral-Small-24B (MedScore) / LLM judges | drop INV | 0.345 | 0.364 |
| T14 / T3 filter view (#3 — existing scores only) / Mistral-Small-24B (MedScore) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / Mistral-Small-24B (MedScore) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / Mistral-Small-3.2-24B (RAGAS) / LLM judges | drop INV | 0.036 | 0.000 |
| T14 / T3 filter view (#3 — existing scores only) / Mistral-Small-3.2-24B (RAGAS) / LLM judges | keep ×1000 | 0.080 | 0.084 |
| T14 / T3 filter view (#3 — existing scores only) / Mistral-Small-3.2-24B (RAGAS) / LLM judges | n INV | 55 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / Mistral-Small-3.2-24B (RAGAS) / LLM judges | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-Conv / small fine-tuned checkers | T13 pair(1) | — | 0.955 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-Conv / small fine-tuned checkers | drop INV | — | 1.000 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-Conv / small fine-tuned checkers | keep ×1000 | 0.330 | 0.336 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-Conv / small fine-tuned checkers | n INV | 0 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-Conv / small fine-tuned checkers | n ×1000 | 112 | 107 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-ZS / small fine-tuned checkers | T13 pair(1) | — | 1.000 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-ZS / small fine-tuned checkers | drop INV | — | 0.955 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-ZS / small fine-tuned checkers | keep ×1000 | 0.607 | 0.589 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-ZS / small fine-tuned checkers | n INV | 0 | 22 |
| T14 / T3 filter view (#3 — existing scores only) / SummaC-ZS / small fine-tuned checkers | n ×1000 | 112 | 107 |

## `notes/m1_strong_final_amend5_report.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| Bind? (criterion uses AFTER values only) / AlignScore-base / False, True → **False** | (row) | present | — |
| Bind? (criterion uses AFTER values only) / AlignScore-base / True, True → **True** | (row) | — | present |
| Bind? (criterion uses AFTER values only) / AlignScore-large / True, True → **True** | EVID (up, down → side) | False, True → **False** | True, True → **True** |
| Bind? (criterion uses AFTER values only) / AlignScore-large / True, True → **True** | Overall | **False** | **True** |
| Bind? (criterion uses AFTER values only) / Bespoke-MiniCheck-7B / True, True → **True** | EVID (up, down → side) | False, True → **False** | True, True → **True** |
| Bind? (criterion uses AFTER values only) / Bespoke-MiniCheck-7B / True, True → **True** | Overall | **False** | **True** |
| Bind? (criterion uses AFTER values only) / Granite Guardian 2B / True, True → **True** | (row) | — | present |
| Bind? (criterion uses AFTER values only) / MiniCheck-Flan-T5-Large / False, True → **False** | (row) | present | — |
| Bind? (criterion uses AFTER values only) / MiniCheck-Flan-T5-Large / True, True → **True** | (row) | — | present |
| Bind? (criterion uses AFTER values only) / SummaC-ZS / False, True → **False** | (row) | present | — |
| Bind? (criterion uses AFTER values only) / SummaC-ZS / True, True → **True** | (row) | — | present |
| US_down (unit-down) vs NS_div10 / Granite Guardian 2B / CLAIM | (row) | — | present |
| US_down (unit-down) vs NS_div10 / Granite Guardian 2B / EVID | (row) | — | present |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | NS_div10 FAIL | 98.9% [96.6,100.0] (86/87) | 98.8% [96.5,100.0] (85/86) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | US_down after | 98.6% [95.7,100.0] (69/70) | 98.6% [95.7,100.0] (68/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | US_down before | 88.6% [81.4,95.7] (62/70) | 88.4% [79.7,95.7] (61/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / CLAIM | n | 70 / 70 / 0 | 69 / 69 / 0 |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | NS_div10 FAIL | 94.3% [88.5,98.9] (82/87) | 94.2% [88.4,98.8] (81/86) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | US_down after | 97.1% [92.9,100.0] (68/70) | 97.1% [92.8,100.0] (67/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | US_down before | 80.0% [71.4,88.6] (56/70) | 79.7% [69.6,88.4] (55/69) |
| US_down (unit-down) vs NS_div10 / MiniCheck-DeBERTa / EVID | n | 70 / 70 / 0 | 69 / 69 / 0 |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | Bind up | False | True |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | US_up after | 74.7% [65.7,82.8] (74/99) | 88.9% [82.8,94.9] (88/99) |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | b/c | 62/0 | 76/0 |
| US_up (×1000) vs NS_x10 / AlignScore-base / CLAIM | p≈ | 9.41e-15 | 7.76e-18 |
| US_up (×1000) vs NS_x10 / AlignScore-base / EVID | US_up after | 53.5% [43.4,62.7] (53/99) | 63.6% [54.5,72.8] (63/99) |
| US_up (×1000) vs NS_x10 / AlignScore-base / EVID | b/c | 39/2 | 49/2 |
| US_up (×1000) vs NS_x10 / AlignScore-base / EVID | p≈ | 1.88e-08 | 1.18e-10 |
| US_up (×1000) vs NS_x10 / AlignScore-large / CLAIM | US_up after | 87.1% [80.2,93.1] (88/101) | 97.0% [93.1,100.0] (98/101) |
| US_up (×1000) vs NS_x10 / AlignScore-large / CLAIM | b/c | 34/0 | 44/0 |
| US_up (×1000) vs NS_x10 / AlignScore-large / CLAIM | p≈ | 1.52e-08 | 9.02e-11 |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | Bind up | False | True |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | US_up after | 69.3% [60.4,78.2] (70/101) | 81.2% [73.3,88.1] (82/101) |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | b/c | 30/1 | 42/1 |
| US_up (×1000) vs NS_x10 / AlignScore-large / EVID | p≈ | 4.93e-07 | 1.06e-09 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / CLAIM | US_up after | 95.3% [90.7,99.1] (102/107) | 100.0% [100.0,100.0] (107/107) |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / CLAIM | b/c | 30/0 | 35/0 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / CLAIM | p≈ | 1.19e-07 | 9.08e-09 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | Bind up | False | True |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | US_up after | 67.3% [57.9,75.7] (72/107) | 77.6% [69.2,84.1] (83/107) |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | b/c | 33/0 | 44/0 |
| US_up (×1000) vs NS_x10 / Bespoke-MiniCheck-7B / EVID | p≈ | 2.54e-08 | 9.02e-11 |
| US_up (×1000) vs NS_x10 / Granite Guardian 2B / CLAIM | (row) | — | present |
| US_up (×1000) vs NS_x10 / Granite Guardian 2B / EVID | (row) | — | present |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / CLAIM | US_up after | 97.2% [93.4,100.0] (103/106) | 99.1% [97.2,100.0] (105/106) |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / CLAIM | b/c | 7/2 | 7/0 |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / CLAIM | p≈ | 0.182 | 0.0233 |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / EVID | US_up after | 86.8% [80.2,92.5] (92/106) | 87.7% [81.1,93.4] (93/106) |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / EVID | b/c | 38/3 | 39/3 |
| US_up (×1000) vs NS_x10 / Llama-3.3-70B (RAGAS NLI) / EVID | p≈ | 1.1e-07 | 6.64e-08 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | NS_x10 FAIL | 96.8% [92.5,100.0] (90/93) | 96.7% [92.4,100.0] (89/92) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | US_up after | 92.7% [87.5,96.9] (89/96) | 93.7% [88.4,97.9] (89/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | US_up before | 86.5% [80.2,92.7] (83/96) | 86.3% [80.0,92.6] (82/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | b/c | 9/3 | 11/4 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | n | 96 / 96 / 0 | 95 / 95 / 0 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / CLAIM | p≈ | 0.149 | 0.121 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | NS_x10 FAIL | 93.5% [88.2,97.8] (87/93) | 93.5% [88.0,97.8] (86/92) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | US_up after | 60.4% [51.0,69.8] (58/96) | 58.9% [48.4,68.4] (56/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | US_up before | 71.9% [63.5,80.2] (69/96) | 72.6% [63.2,81.1] (69/95) |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | b/c | 8/19 | 9/22 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | n | 96 / 96 / 0 | 95 / 95 / 0 |
| US_up (×1000) vs NS_x10 / MiniCheck-DeBERTa / EVID | p≈ | 0.0543 | 0.0311 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | Bind up | False | True |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | US_up after | 82.5% [74.8,89.3] (85/103) | 96.1% [92.2,99.0] (99/103) |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | b/c | 31/0 | 45/0 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / CLAIM | p≈ | 7.12e-08 | 5.41e-11 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / EVID | US_up after | 45.6% [36.9,55.3] (47/103) | 55.3% [46.6,65.0] (57/103) |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / EVID | b/c | 33/8 | 43/8 |
| US_up (×1000) vs NS_x10 / MiniCheck-Flan-T5-Large / EVID | p≈ | 0.000178 | 1.93e-06 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | Bind up | False | True |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | US_up after | 69.4% [58.8,78.8] (59/85) | 87.1% [80.0,94.1] (74/85) |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | b/c | 36/0 | 51/0 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / CLAIM | p≈ | 5.43e-09 | 2.53e-12 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | Bind up | False | True |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | US_up after | 63.5% [52.9,73.0] (54/85) | 81.2% [71.8,89.4] (69/85) |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | b/c | 35/1 | 50/1 |
| US_up (×1000) vs NS_x10 / SummaC-ZS / EVID | p≈ | 3.8e-08 | 1.8e-11 |

## `notes/t7_e1_unit_report.md`

| Row | Column | Old | New |
| --- | --- | --- | --- |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_alignscore_base / 21 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_alignscore_base / 22 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_granite_guardian / 22 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_granite_guardian / 23 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_hhem / 21 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_hhem / 22 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_minicheck_deberta / 19 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_minicheck_deberta / 20 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_minicheck_roberta / 20 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_minicheck_roberta / 21 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_summac_conv / 14 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_summac_conv / 15 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_summac_zs / 18 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / t6a_summac_zs / 19 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v1_medscore / 108 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v1_medscore / 112 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v1b_medscore / 108 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v1b_medscore / 112 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v1c_medscore / 107 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v1c_medscore / 111 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v2a_minicheck / 104 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v2a_minicheck / 108 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v2b_bespoke / 108 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v2b_bespoke / 112 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v3_alignscore / 102 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v3_alignscore / 106 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v4_ragas_nli / 107 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v4_ragas_nli / 108 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v5_ragas_nli / 108 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v5_ragas_nli / 112 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_gpt4o_mini / 104 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_gpt4o_mini / 108 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_haiku45 / 105 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_haiku45 / 109 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_llama31_8b / 104 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_llama31_8b / 108 | (row) | present | — |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_mistral_small32 / 108 | (row) | — | present |
| Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate) / v6_ragas_mistral_small32 / 112 | (row) | present | — |
| LLM judges (|C0 PASS) / v1_medscore / 108 | (row) | — | present |
| LLM judges (|C0 PASS) / v1_medscore / 112 | (row) | present | — |
| LLM judges (|C0 PASS) / v1b_medscore / 108 | (row) | — | present |
| LLM judges (|C0 PASS) / v1b_medscore / 112 | (row) | present | — |
| LLM judges (|C0 PASS) / v4_ragas_nli / 107 | (row) | — | present |
| LLM judges (|C0 PASS) / v4_ragas_nli / 108 | (row) | present | — |
| LLM judges (|C0 PASS) / v5_ragas_nli / 108 | (row) | — | present |
| LLM judges (|C0 PASS) / v5_ragas_nli / 112 | (row) | present | — |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_alignscore_base / 0.230 | n | 0/66 | 0/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_granite_guardian / 0.343 | n | 0/66 | 0/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_hhem / 0.057 | n | 0/66 | 0/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_minicheck_deberta / 0.804 | n | 0/66 | 0/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_minicheck_roberta / 0.348 | n | 0/66 | 0/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_summac_conv / 0.691 | n | 0/66 | 0/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / t6a_summac_zs / 0.370 | n | 0/66 | 0/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1_medscore / 0.804 | E1-claim x2/x10 FAIL rate | 0.991 | 0.995 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1_medscore / 0.804 | INV-unit PASS rate | 0.667 | 0.677 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1_medscore / 0.804 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1b_medscore / 0.570 | E1-claim x2/x10 FAIL rate | 0.963 | 0.966 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1b_medscore / 0.570 | INV-unit PASS rate | 0.970 | 0.968 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1b_medscore / 0.570 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1c_medscore / 0.670 | INV-unit PASS rate | 0.470 | 0.452 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v1c_medscore / 0.670 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v2a_minicheck / 0.365 | E1-claim x2/x10 FAIL rate | 0.953 | 0.957 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v2a_minicheck / 0.365 | INV-unit PASS rate | 0.091 | 0.081 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v2a_minicheck / 0.365 | n | 55/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v2b_bespoke / 0.535 | E1-claim x2/x10 FAIL rate | 0.958 | 0.971 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v2b_bespoke / 0.535 | INV-unit PASS rate | 0.788 | 0.774 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v2b_bespoke / 0.535 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v3_alignscore / 0.504 | INV-unit PASS rate | 0.236 | 0.226 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v3_alignscore / 0.504 | n | 55/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v4_ragas_nli / 0.730 | E1-claim x2/x10 FAIL rate | 0.953 | 0.971 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v4_ragas_nli / 0.730 | INV-unit PASS rate | 0.742 | 0.758 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v4_ragas_nli / 0.730 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v5_ragas_nli / 0.835 | INV-unit PASS rate | 0.970 | 0.968 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v5_ragas_nli / 0.835 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_gpt4o_mini / 0.839 | E1-claim x2/x10 FAIL rate | 0.991 | 0.995 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_gpt4o_mini / 0.839 | INV-unit PASS rate | 0.712 | 0.710 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_gpt4o_mini / 0.839 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_haiku45 / 0.935 | E1-claim x2/x10 FAIL rate | 0.991 | 0.995 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_haiku45 / 0.935 | INV-unit PASS rate | 0.955 | 0.952 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_haiku45 / 0.935 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_llama31_8b / 0.674 | E1-claim x2/x10 FAIL rate | 0.986 | 0.995 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_llama31_8b / 0.674 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_mistral_small32 / 0.700 | E1-claim x2/x10 FAIL rate | 0.991 | 0.995 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_mistral_small32 / 0.700 | INV-unit PASS rate | 0.970 | 0.968 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_mistral_small32 / 0.700 | n | 66/66 | 62/62 |
| T7 E1-unit vs E1-claim vs INV-unit (per verifier) / v6_ragas_nli / — | n | 0/66 | 0/62 |

