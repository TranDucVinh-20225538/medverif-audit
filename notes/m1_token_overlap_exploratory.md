# EXPLORATORY — numeral-token survival after M1 (not preregistered)

**Exploratory analysis; not part of the preregistered M1-strong criterion.** Rows = exactly the pairs/rows behind `results/tables/m1_strong_final.md` (C0-PASS bases, parsed scores).

- **Flag (US_up after-M1):** tokenize the after-M1 text with the checker's own tokenizer; flag = yes if a token overlapping the numeral M1 introduced (e.g. `500000`) has surface exactly equal to the original numeral (e.g. `500`). Cell = US_up **after** FAIL rate.
- **Control (NS_x10):** same test on the ×10 numeral (e.g. `5000`) vs the C0 numeral (`500`). Cell = NS_x10 FAIL rate.
- Bootstrap 1000 × base_id, seed 42. `no-op` = US_up pairs where M1 left the text unchanged (no rescaled numeral exists; excluded from the split). `unres.` = other rows where no introduced numeral was found.

| Model | Side | US_up after, flag=yes | US_up after, flag=no | no-op | unres. | NS_x10, flag=yes | NS_x10, flag=no | unres. |
| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: |
| MiniCheck-RoBERTa | CLAIM | 89.3% [75.0, 100.0] (n=28) | 96.2% [90.4, 100.0] (n=52) | 16 | 0 | NA (n=0) | 94.6% [89.1, 98.9] (n=92) | 0 |
| MiniCheck-RoBERTa | EVID | 55.6% [37.0, 74.1] (n=27) | 90.6% [81.1, 98.1] (n=53) | 16 | 0 | NA (n=0) | 92.4% [87.0, 97.8] (n=92) | 0 |
| MiniCheck-DeBERTa | CLAIM | 91.8% [83.7, 98.0] (n=49) | 93.1% [82.8, 100.0] (n=29) | 18 | 0 | NA (n=0) | 96.8% [92.5, 100.0] (n=93) | 0 |
| MiniCheck-DeBERTa | EVID | 38.8% [26.5, 53.1] (n=49) | 86.2% [72.4, 96.6] (n=29) | 18 | 0 | NA (n=0) | 93.5% [88.2, 97.8] (n=93) | 0 |
| MiniCheck-Flan-T5-Large | CLAIM | 100.0% [100.0, 100.0] (n=42) | 90.5% [81.0, 97.6] (n=42) | 19 | 0 | NA (n=0) | 94.9% [89.9, 99.0] (n=99) | 0 |
| MiniCheck-Flan-T5-Large | EVID | 23.8% [11.9, 38.1] (n=42) | 85.7% [73.8, 95.2] (n=42) | 19 | 0 | NA (n=0) | 83.8% [75.8, 90.9] (n=99) | 0 |
| AlignScore-base | CLAIM | 85.7% [71.4, 96.4] (n=28) | 86.5% [76.9, 94.2] (n=52) | 19 | 0 | NA (n=0) | 91.6% [85.3, 96.8] (n=95) | 0 |
| AlignScore-base | EVID | 18.5% [3.7, 33.3] (n=27) | 81.1% [69.8, 90.6] (n=53) | 19 | 0 | NA (n=0) | 90.5% [84.2, 95.8] (n=95) | 0 |
| AlignScore-large | CLAIM | 93.1% [82.8, 100.0] (n=29) | 98.1% [94.4, 100.0] (n=54) | 18 | 0 | NA (n=0) | 96.9% [92.8, 100.0] (n=97) | 0 |
| AlignScore-large | EVID | 71.4% [53.6, 89.3] (n=28) | 81.8% [70.9, 90.9] (n=55) | 18 | 0 | NA (n=0) | 89.7% [83.5, 94.8] (n=97) | 0 |
| SummaC-ZS | CLAIM | 80.6% [66.7, 91.7] (n=36) | 85.7% [74.3, 97.1] (n=35) | 14 | 0 | NA (n=0) | 95.1% [90.2, 98.8] (n=82) | 0 |
| SummaC-ZS | EVID | 63.9% [47.2, 77.8] (n=36) | 88.6% [77.1, 97.1] (n=35) | 14 | 0 | NA (n=0) | 93.9% [89.0, 98.8] (n=82) | 0 |
| Granite Guardian 2B | CLAIM | 100.0% [100.0, 100.0] (n=15) | 95.8% [90.1, 100.0] (n=71) | 20 | 0 | 95.8% [87.5, 100.0] (n=24) | 83.3% [74.4, 91.0] (n=78) | 0 |
| Granite Guardian 2B | EVID | 100.0% [100.0, 100.0] (n=15) | 69.0% [59.2, 80.3] (n=71) | 20 | 0 | 87.5% [75.0, 100.0] (n=24) | 62.8% [51.3, 73.1] (n=78) | 0 |
| Bespoke-MiniCheck-7B | CLAIM | 100.0% [100.0, 100.0] (n=44) | 100.0% [100.0, 100.0] (n=43) | 20 | 0 | NA (n=0) | 97.1% [93.2, 100.0] (n=103) | 0 |
| Bespoke-MiniCheck-7B | EVID | 77.3% [65.9, 88.6] (n=44) | 72.1% [58.1, 83.8] (n=43) | 20 | 0 | NA (n=0) | 89.3% [82.5, 95.1] (n=103) | 0 |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0% [100.0, 100.0] (n=15) | 98.6% [95.8, 100.0] (n=72) | 20 | 0 | 100.0% [100.0, 100.0] (n=24) | 100.0% [100.0, 100.0] (n=79) | 0 |
| Mistral-Small-24B (MedScore) | EVID | 93.3% [80.0, 100.0] (n=15) | 91.7% [84.7, 97.2] (n=72) | 20 | 0 | 91.7% [79.2, 100.0] (n=24) | 93.7% [87.3, 98.7] (n=79) | 0 |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 100.0% [100.0, 100.0] (n=28) | 98.2% [93.0, 100.0] (n=57) | 19 | 0 | 100.0% [100.0, 100.0] (n=32) | 100.0% [100.0, 100.0] (n=70) | 0 |
| Llama-3.3-70B (RAGAS NLI) | EVID | 71.4% [53.6, 89.3] (n=28) | 91.4% [82.8, 98.3] (n=58) | 20 | 0 | 84.4% [71.9, 96.9] (n=32) | 94.3% [88.6, 98.6] (n=70) | 0 |

Tokenizers: MiniCheck-RoBERTa = `lytang/MiniCheck-RoBERTa-Large`; MiniCheck-DeBERTa = `lytang/MiniCheck-DeBERTa-v3-Large`; MiniCheck-Flan-T5-Large = `lytang/MiniCheck-Flan-T5-Large`; AlignScore-base = `roberta-base`; AlignScore-large = `roberta-large`; SummaC-ZS = `tals/albert-xlarge-vitaminc-mnli`; Granite Guardian 2B = `ibm-granite/granite-guardian-3.0-2b`; Bespoke-MiniCheck-7B = `bespokelabs/Bespoke-MiniCheck-7B`; Mistral-Small-24B (MedScore) = `mistralai/Mistral-Small-24B-Instruct-2501`; Llama-3.3-70B (RAGAS NLI) = `meta-llama/Llama-3.1-8B-Instruct`.
- Llama-3.3-70B (RAGAS NLI): proxy: Llama-3.1-8B-Instruct tokenizer (same Llama-3 vocabulary as 3.3-70B)

## Caveat found here — M1 no-op rows inside the US_up after pairs (sensitivity, not a revision)

Checker-side M1 (`src/quantity_norm.py` DOSE_RE) has no `g/kg` or `L`, so **40/214** US_up ×1000 rows (mg/kg→g/kg, mL→L) are unchanged by M1; the gate still passes them because M1-lib and M1 agree (both unchanged). In `m1_strong_final` these count as after-M1 pairs although the checker saw the before input. US_down after (150/150 changed) and NS (no M1) are unaffected. The accepted table is **not** changed.

| Model | Side | US_up after (as reported) | US_up after, M1-changed rows only | US_up after, no-op rows only | NS_x10 |
| --- | --- | --- | --- | --- | --- |
| MiniCheck-RoBERTa | CLAIM | 80.2% [71.9, 87.5] (n=96) | 93.8% [87.5, 98.8] (n=80) | 12.5% [0.0, 31.2] (n=16) | 94.6% [89.1, 98.9] (n=92) |
| MiniCheck-RoBERTa | EVID | 68.8% [59.4, 77.1] (n=96) | 78.8% [70.0, 87.5] (n=80) | 18.8% [0.0, 37.5] (n=16) | 92.4% [87.0, 97.8] (n=92) |
| MiniCheck-DeBERTa | CLAIM | 89.6% [83.3, 94.8] (n=96) | 92.3% [85.9, 97.4] (n=78) | 77.8% [61.1, 94.4] (n=18) | 96.8% [92.5, 100.0] (n=93) |
| MiniCheck-DeBERTa | EVID | 58.3% [47.9, 67.7] (n=96) | 56.4% [44.9, 66.7] (n=78) | 66.7% [44.4, 88.9] (n=18) | 93.5% [88.2, 97.8] (n=93) |
| MiniCheck-Flan-T5-Large | CLAIM | 82.5% [74.8, 89.3] (n=103) | 95.2% [90.5, 98.8] (n=84) | 26.3% [10.5, 47.4] (n=19) | 94.9% [89.9, 99.0] (n=99) |
| MiniCheck-Flan-T5-Large | EVID | 45.6% [36.9, 55.3] (n=103) | 54.8% [44.0, 65.5] (n=84) | 5.3% [0.0, 15.8] (n=19) | 83.8% [75.8, 90.9] (n=99) |
| AlignScore-base | CLAIM | 74.7% [65.7, 82.8] (n=99) | 86.2% [77.5, 93.8] (n=80) | 26.3% [5.3, 47.4] (n=19) | 91.6% [85.3, 96.8] (n=95) |
| AlignScore-base | EVID | 53.5% [43.4, 62.7] (n=99) | 60.0% [50.0, 71.2] (n=80) | 26.3% [10.5, 47.4] (n=19) | 90.5% [84.2, 95.8] (n=95) |
| AlignScore-large | CLAIM | 87.1% [80.2, 93.1] (n=101) | 96.4% [92.8, 100.0] (n=83) | 44.4% [22.2, 66.7] (n=18) | 96.9% [92.8, 100.0] (n=97) |
| AlignScore-large | EVID | 69.3% [60.4, 78.2] (n=101) | 78.3% [69.9, 86.7] (n=83) | 27.8% [5.6, 50.0] (n=18) | 89.7% [83.5, 94.8] (n=97) |
| SummaC-ZS | CLAIM | 69.4% [58.8, 78.8] (n=85) | 83.1% [74.6, 91.5] (n=71) | 0.0% [0.0, 0.0] (n=14) | 95.1% [90.2, 98.8] (n=82) |
| SummaC-ZS | EVID | 63.5% [52.9, 73.0] (n=85) | 76.1% [66.2, 85.9] (n=71) | 0.0% [0.0, 0.0] (n=14) | 93.9% [89.0, 98.8] (n=82) |
| Granite Guardian 2B | CLAIM | 90.6% [84.9, 96.2] (n=106) | 96.5% [93.0, 100.0] (n=86) | 65.0% [40.0, 85.0] (n=20) | 86.3% [79.4, 93.1] (n=102) |
| Granite Guardian 2B | EVID | 67.0% [57.5, 76.4] (n=106) | 74.4% [65.1, 83.7] (n=86) | 35.0% [15.0, 55.0] (n=20) | 68.6% [59.8, 77.5] (n=102) |
| Bespoke-MiniCheck-7B | CLAIM | 95.3% [90.7, 99.1] (n=107) | 100.0% [100.0, 100.0] (n=87) | 75.0% [55.0, 95.0] (n=20) | 97.1% [93.2, 100.0] (n=103) |
| Bespoke-MiniCheck-7B | EVID | 67.3% [57.9, 75.7] (n=107) | 74.7% [65.5, 82.8] (n=87) | 35.0% [15.0, 55.0] (n=20) | 89.3% [82.5, 95.1] (n=103) |
| Mistral-Small-24B (MedScore) | CLAIM | 99.1% [97.2, 100.0] (n=107) | 98.9% [96.6, 100.0] (n=87) | 100.0% [100.0, 100.0] (n=20) | 100.0% [100.0, 100.0] (n=103) |
| Mistral-Small-24B (MedScore) | EVID | 88.8% [82.2, 94.4] (n=107) | 92.0% [86.2, 96.6] (n=87) | 75.0% [55.0, 90.0] (n=20) | 93.2% [88.3, 98.1] (n=103) |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 97.1% [93.3, 100.0] (n=104) | 98.8% [96.5, 100.0] (n=85) | 89.5% [73.7, 100.0] (n=19) | 100.0% [100.0, 100.0] (n=102) |
| Llama-3.3-70B (RAGAS NLI) | EVID | 84.9% [77.4, 91.5] (n=106) | 84.9% [76.7, 91.9] (n=86) | 85.0% [70.0, 100.0] (n=20) | 91.2% [85.3, 96.1] (n=102) |
