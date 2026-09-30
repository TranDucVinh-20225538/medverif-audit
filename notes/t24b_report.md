# T24b — real-RAG dose prevalence & perturbation (P1)

Author labels: `qc/t24_labels.csv` (**FINAL**). **55** unique Y questions (56 Y minus **T24_003**; duplicate rows excluded). **8** unique N → appendix only (span-matcher errors). **0/56** Y answers re-express a unit → **prevalence**, not in-the-wild conversion.

- Instances built: **202**
- Build manifest: `notes/t24b_build_manifest.json` · skips: **18**
- Edit log: `/data2/hpcshared/medverif-audit/notes/t24b_edit_log.jsonl`

Conditional cells: perturbation metrics among questions where **C0 PASS**. Bootstrap: **1000** resamples cluster by `question_id`, seed **42**.

| Checker | C0 PASS | Unit-up FAIL|C0 | Unit-down FAIL|C0 | Value×10 FAIL|C0 |
| --- | --- | --- | --- | --- |
| MiniCheck-RoBERTa | 85.5% [74.5%, 94.5%] (n=55, q=55) | 58.5% [43.9%, 73.2%] (n=41, q=41) | 11.1% [2.7%, 22.2%] (n=36, q=36) | 100.0% [100.0%, 100.0%] (n=47, q=47) |
| MiniCheck-DeBERTa | 89.1% [80.0%, 96.4%] (n=55, q=55) | 83.7% [72.1%, 93.0%] (n=43, q=43) | 89.2% [78.4%, 97.3%] (n=37, q=37) | 87.8% [77.6%, 95.9%] (n=49, q=49) |
| AlignScore-base | 89.1% [80.0%, 96.4%] (n=55, q=55) | 34.1% [20.5%, 50.0%] (n=44, q=44) | 10.3% [2.6%, 20.5%] (n=39, q=39) | 93.9% [85.7%, 100.0%] (n=49, q=49) |
| MiniCheck-Flan-T5-Large | 92.7% [85.5%, 98.2%] (n=55, q=55) | 55.6% [42.2%, 68.9%] (n=45, q=45) | 10.0% [2.5%, 20.0%] (n=40, q=40) | 94.1% [86.3%, 100.0%] (n=51, q=51) |
| AlignScore-large | 94.5% [87.3%, 100.0%] (n=55, q=55) | 69.6% [56.5%, 82.6%] (n=46, q=46) | 17.1% [7.3%, 29.3%] (n=41, q=41) | 98.1% [94.2%, 100.0%] (n=52, q=52) |
| Bespoke-MiniCheck-7B | 96.4% [90.9%, 100.0%] (n=55, q=55) | 74.5% [61.7%, 87.2%] (n=47, q=47) | 80.5% [65.9%, 92.7%] (n=41, q=41) | 100.0% [100.0%, 100.0%] (n=53, q=53) |
| Llama-3.3-70B (RAGAS NLI) | 100.0% [100.0%, 100.0%] (n=55, q=55) | 100.0% [100.0%, 100.0%] (n=49, q=49) | 100.0% [100.0%, 100.0%] (n=43, q=43) | 98.2% [94.5%, 100.0%] (n=55, q=55) |
| Mistral-Small-24B (MedScore) | 100.0% [100.0%, 100.0%] (n=55, q=55) | 98.0% [93.9%, 100.0%] (n=49, q=49) | 100.0% [100.0%, 100.0%] (n=43, q=43) | 100.0% [100.0%, 100.0%] (n=55, q=55) |
