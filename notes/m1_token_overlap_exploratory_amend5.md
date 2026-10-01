# EXPLORATORY — numeral-token survival after M1 (not preregistered)

**Exploratory analysis; not part of the preregistered M1-strong criterion.** Rows = exactly the pairs/rows behind `results/tables/m1_strong_final_amend5.md` (C0-PASS bases, parsed scores). After-M1 texts = amendment-5 texts actually scored (base pack overlaid with the spec-M1 rebuilds; API judges use their own pack).

- **Flag (US_up after-M1):** tokenize the after-M1 text with the checker's own tokenizer; flag = yes if a token overlapping the numeral M1 introduced (e.g. `500000`) has surface exactly equal to the original numeral (e.g. `500`). Cell = US_up **after** FAIL rate.
- **Control (NS_x10):** same test on the ×10 numeral (e.g. `5000`) vs the C0 numeral (`500`). Cell = NS_x10 FAIL rate.
- Bootstrap 1000 × base_id, seed 42. `no-op` = US_up pairs where M1 left the text unchanged (no rescaled numeral exists; excluded from the split). `unres.` = other rows where no introduced numeral was found.

| Model | Side | US_up after, flag=yes | US_up after, flag=no | no-op | unres. | NS_x10, flag=yes | NS_x10, flag=no | unres. |
| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: |
| MiniCheck-RoBERTa | CLAIM | 90.3% [80.6, 100.0] (n=31) | 95.4% [89.2, 100.0] (n=65) | 0 | 0 | NA (n=0) | 94.6% [89.1, 98.9] (n=92) | 0 |
| MiniCheck-RoBERTa | EVID | 60.0% [43.3, 76.7] (n=30) | 93.9% [87.9, 98.5] (n=66) | 0 | 0 | NA (n=0) | 92.4% [87.0, 97.8] (n=92) | 0 |
| MiniCheck-DeBERTa | CLAIM | 92.6% [85.2, 98.1] (n=54) | 95.1% [87.8, 100.0] (n=41) | 0 | 0 | NA (n=0) | 96.7% [92.4, 100.0] (n=92) | 0 |
| MiniCheck-DeBERTa | EVID | 35.2% [22.2, 50.0] (n=54) | 90.2% [80.5, 97.6] (n=41) | 0 | 0 | NA (n=0) | 93.5% [88.0, 97.8] (n=92) | 0 |
| MiniCheck-Flan-T5-Large | CLAIM | 100.0% [100.0, 100.0] (n=50) | 92.5% [84.9, 98.1] (n=53) | 0 | 0 | NA (n=0) | 94.9% [89.9, 99.0] (n=99) | 0 |
| MiniCheck-Flan-T5-Large | EVID | 24.0% [12.0, 36.0] (n=50) | 84.9% [73.6, 94.3] (n=53) | 0 | 0 | NA (n=0) | 83.8% [75.8, 90.9] (n=99) | 0 |
| AlignScore-base | CLAIM | 87.1% [74.2, 96.8] (n=31) | 89.7% [82.4, 97.1] (n=68) | 0 | 0 | NA (n=0) | 91.6% [85.3, 96.8] (n=95) | 0 |
| AlignScore-base | EVID | 16.7% [3.3, 30.0] (n=30) | 84.1% [75.4, 91.3] (n=69) | 0 | 0 | NA (n=0) | 90.5% [84.2, 95.8] (n=95) | 0 |
| AlignScore-large | CLAIM | 93.8% [84.4, 100.0] (n=32) | 98.6% [95.7, 100.0] (n=69) | 0 | 0 | NA (n=0) | 96.9% [92.8, 100.0] (n=97) | 0 |
| AlignScore-large | EVID | 71.0% [54.8, 87.1] (n=31) | 85.7% [77.1, 92.9] (n=70) | 0 | 0 | NA (n=0) | 89.7% [83.5, 94.8] (n=97) | 0 |
| SummaC-ZS | CLAIM | 81.6% [68.4, 92.2] (n=38) | 91.5% [83.0, 97.9] (n=47) | 0 | 0 | NA (n=0) | 95.1% [90.2, 98.8] (n=82) | 0 |
| SummaC-ZS | EVID | 65.8% [50.0, 81.6] (n=38) | 93.6% [85.1, 100.0] (n=47) | 0 | 0 | NA (n=0) | 93.9% [89.0, 98.8] (n=82) | 0 |
| Granite Guardian 2B | CLAIM | 100.0% [100.0, 100.0] (n=25) | 97.5% [93.8, 100.0] (n=81) | 0 | 0 | 95.8% [87.5, 100.0] (n=24) | 83.3% [74.4, 91.0] (n=78) | 0 |
| Granite Guardian 2B | EVID | 92.0% [80.0, 100.0] (n=25) | 74.1% [64.2, 82.7] (n=81) | 0 | 0 | 87.5% [75.0, 100.0] (n=24) | 62.8% [51.3, 73.1] (n=78) | 0 |
| Bespoke-MiniCheck-7B | CLAIM | 100.0% [100.0, 100.0] (n=57) | 100.0% [100.0, 100.0] (n=50) | 0 | 0 | NA (n=0) | 97.1% [93.2, 100.0] (n=103) | 0 |
| Bespoke-MiniCheck-7B | EVID | 77.2% [66.7, 87.7] (n=57) | 78.0% [68.0, 88.0] (n=50) | 0 | 0 | NA (n=0) | 89.3% [82.5, 95.1] (n=103) | 0 |
| Mistral-Small-24B (MedScore) | CLAIM | 100.0% [100.0, 100.0] (n=25) | 98.8% [95.1, 100.0] (n=81) | 0 | 0 | 100.0% [100.0, 100.0] (n=24) | 100.0% [100.0, 100.0] (n=78) | 0 |
| Mistral-Small-24B (MedScore) | EVID | 92.0% [80.0, 100.0] (n=25) | 92.6% [86.4, 97.5] (n=81) | 0 | 0 | 91.7% [79.2, 100.0] (n=24) | 93.6% [87.2, 98.7] (n=78) | 0 |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 100.0% [100.0, 100.0] (n=29) | 98.7% [96.1, 100.0] (n=77) | 0 | 0 | 100.0% [100.0, 100.0] (n=32) | 98.6% [95.8, 100.0] (n=71) | 0 |
| Llama-3.3-70B (RAGAS NLI) | EVID | 72.4% [55.2, 89.7] (n=29) | 93.5% [87.0, 98.7] (n=77) | 0 | 0 | 81.2% [65.6, 93.8] (n=32) | 94.4% [88.7, 98.6] (n=71) | 0 |

Tokenizers: MiniCheck-RoBERTa = `lytang/MiniCheck-RoBERTa-Large`; MiniCheck-DeBERTa = `lytang/MiniCheck-DeBERTa-v3-Large`; MiniCheck-Flan-T5-Large = `lytang/MiniCheck-Flan-T5-Large`; AlignScore-base = `roberta-base`; AlignScore-large = `roberta-large`; SummaC-ZS = `tals/albert-xlarge-vitaminc-mnli`; Granite Guardian 2B = `ibm-granite/granite-guardian-3.0-2b`; Bespoke-MiniCheck-7B = `bespokelabs/Bespoke-MiniCheck-7B`; Mistral-Small-24B (MedScore) = `mistralai/Mistral-Small-24B-Instruct-2501`; Llama-3.3-70B (RAGAS NLI) = `meta-llama/Llama-3.1-8B-Instruct`.
- Llama-3.3-70B (RAGAS NLI): proxy: Llama-3.1-8B-Instruct tokenizer (same Llama-3 vocabulary as 3.3-70B)

## M1 no-op rows after amendment 5

Local pack: **0/214** US_up ×1000 rows unchanged by M1; API pack: **0** rows (pre-amendment-5: 40/214 local). Sensitivity split below for reference.

| Model | Side | US_up after (as reported) | US_up after, M1-changed rows only | US_up after, no-op rows only | NS_x10 |
| --- | --- | --- | --- | --- | --- |
| MiniCheck-RoBERTa | CLAIM | 93.8% [88.5, 97.9] (n=96) | 93.8% [88.5, 97.9] (n=96) | NA (n=0) | 94.6% [89.1, 98.9] (n=92) |
| MiniCheck-RoBERTa | EVID | 83.3% [75.0, 89.6] (n=96) | 83.3% [75.0, 89.6] (n=96) | NA (n=0) | 92.4% [87.0, 97.8] (n=92) |
| MiniCheck-DeBERTa | CLAIM | 93.7% [88.4, 97.9] (n=95) | 93.7% [88.4, 97.9] (n=95) | NA (n=0) | 96.7% [92.4, 100.0] (n=92) |
| MiniCheck-DeBERTa | EVID | 58.9% [48.4, 68.4] (n=95) | 58.9% [48.4, 68.4] (n=95) | NA (n=0) | 93.5% [88.0, 97.8] (n=92) |
| MiniCheck-Flan-T5-Large | CLAIM | 96.1% [92.2, 99.0] (n=103) | 96.1% [92.2, 99.0] (n=103) | NA (n=0) | 94.9% [89.9, 99.0] (n=99) |
| MiniCheck-Flan-T5-Large | EVID | 55.3% [46.6, 65.0] (n=103) | 55.3% [46.6, 65.0] (n=103) | NA (n=0) | 83.8% [75.8, 90.9] (n=99) |
| AlignScore-base | CLAIM | 88.9% [82.8, 94.9] (n=99) | 88.9% [82.8, 94.9] (n=99) | NA (n=0) | 91.6% [85.3, 96.8] (n=95) |
| AlignScore-base | EVID | 63.6% [54.5, 72.8] (n=99) | 63.6% [54.5, 72.8] (n=99) | NA (n=0) | 90.5% [84.2, 95.8] (n=95) |
| AlignScore-large | CLAIM | 97.0% [93.1, 100.0] (n=101) | 97.0% [93.1, 100.0] (n=101) | NA (n=0) | 96.9% [92.8, 100.0] (n=97) |
| AlignScore-large | EVID | 81.2% [73.3, 88.1] (n=101) | 81.2% [73.3, 88.1] (n=101) | NA (n=0) | 89.7% [83.5, 94.8] (n=97) |
| SummaC-ZS | CLAIM | 87.1% [80.0, 94.1] (n=85) | 87.1% [80.0, 94.1] (n=85) | NA (n=0) | 95.1% [90.2, 98.8] (n=82) |
| SummaC-ZS | EVID | 81.2% [71.8, 89.4] (n=85) | 81.2% [71.8, 89.4] (n=85) | NA (n=0) | 93.9% [89.0, 98.8] (n=82) |
| Granite Guardian 2B | CLAIM | 98.1% [95.3, 100.0] (n=106) | 98.1% [95.3, 100.0] (n=106) | NA (n=0) | 86.3% [79.4, 93.1] (n=102) |
| Granite Guardian 2B | EVID | 78.3% [70.8, 85.8] (n=106) | 78.3% [70.8, 85.8] (n=106) | NA (n=0) | 68.6% [59.8, 77.5] (n=102) |
| Bespoke-MiniCheck-7B | CLAIM | 100.0% [100.0, 100.0] (n=107) | 100.0% [100.0, 100.0] (n=107) | NA (n=0) | 97.1% [93.2, 100.0] (n=103) |
| Bespoke-MiniCheck-7B | EVID | 77.6% [69.2, 84.1] (n=107) | 77.6% [69.2, 84.1] (n=107) | NA (n=0) | 89.3% [82.5, 95.1] (n=103) |
| Mistral-Small-24B (MedScore) | CLAIM | 99.1% [97.2, 100.0] (n=106) | 99.1% [97.2, 100.0] (n=106) | NA (n=0) | 100.0% [100.0, 100.0] (n=102) |
| Mistral-Small-24B (MedScore) | EVID | 92.5% [86.8, 97.2] (n=106) | 92.5% [86.8, 97.2] (n=106) | NA (n=0) | 93.1% [88.2, 97.1] (n=102) |
| Llama-3.3-70B (RAGAS NLI) | CLAIM | 99.1% [97.2, 100.0] (n=106) | 99.1% [97.2, 100.0] (n=106) | NA (n=0) | 99.0% [97.1, 100.0] (n=103) |
| Llama-3.3-70B (RAGAS NLI) | EVID | 87.7% [81.1, 93.4] (n=106) | 87.7% [81.1, 93.4] (n=106) | NA (n=0) | 90.3% [83.5, 96.1] (n=103) |
