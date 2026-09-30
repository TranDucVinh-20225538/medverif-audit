# T24b — real-RAG dose prevalence & perturbation (P1)

Author labels: `qc/t24_labels.csv` (**FINAL**). **55** unique Y questions (56 Y minus **T24_003**; duplicate rows excluded). **8** unique N → appendix only (span-matcher errors). **0/56** Y answers re-express a unit → **prevalence**, not in-the-wild conversion.

Edit spot-check: `qc/t24b_labels.csv` — **18/20** edits valid; unit-up/down sample **14/14**.
Excluded from all cells (threshold doses, not point doses): **T24_037, T24_066**.

- Instances built: **202**
- Build manifest: `notes/t24b_build_manifest.json` · skips: **18**
- Edit log: `/data2/hpcshared/medverif-audit/notes/t24b_edit_log.jsonl`

Conditional cells: perturbation metrics among questions where **C0 PASS**. Bootstrap: **1000** resamples cluster by `question_id`, seed **42**.

| Checker | C0 PASS | Unit-up FAIL|C0 | Unit-down FAIL|C0 | Value×10 FAIL|C0 |
| --- | --- | --- | --- | --- |
| MiniCheck-RoBERTa | 84.9% [73.6%, 94.3%] (n=53, q=53) | 59.0% [43.6%, 74.4%] (n=39, q=39) | 11.8% [2.9%, 23.5%] (n=34, q=34) | 100.0% [100.0%, 100.0%] (n=45, q=45) |
| MiniCheck-DeBERTa | 90.6% [81.1%, 98.1%] (n=53, q=53) | 83.3% [71.4%, 92.9%] (n=42, q=42) | 88.9% [77.8%, 97.2%] (n=36, q=36) | 87.5% [77.1%, 95.8%] (n=48, q=48) |
| AlignScore-base | 88.7% [79.2%, 96.2%] (n=53, q=53) | 35.7% [21.4%, 50.0%] (n=42, q=42) | 10.8% [2.7%, 21.6%] (n=37, q=37) | 93.6% [87.2%, 100.0%] (n=47, q=47) |
| MiniCheck-Flan-T5-Large | 92.5% [84.9%, 98.1%] (n=53, q=53) | 55.8% [41.9%, 69.8%] (n=43, q=43) | 10.5% [2.6%, 21.1%] (n=38, q=38) | 93.9% [87.7%, 100.0%] (n=49, q=49) |
| AlignScore-large | 94.3% [86.8%, 100.0%] (n=53, q=53) | 70.5% [56.8%, 84.1%] (n=44, q=44) | 17.9% [7.7%, 30.8%] (n=39, q=39) | 98.0% [94.0%, 100.0%] (n=50, q=50) |
| Bespoke-MiniCheck-7B | 98.1% [94.3%, 100.0%] (n=53, q=53) | 73.9% [60.9%, 87.0%] (n=46, q=46) | 82.5% [70.0%, 92.5%] (n=40, q=40) | 100.0% [100.0%, 100.0%] (n=52, q=52) |
| Llama-3.3-70B (RAGAS NLI) | 100.0% [100.0%, 100.0%] (n=53, q=53) | 100.0% [100.0%, 100.0%] (n=47, q=47) | 100.0% [100.0%, 100.0%] (n=41, q=41) | 98.1% [92.5%, 100.0%] (n=53, q=53) |
| Mistral-Small-24B (MedScore) | 100.0% [100.0%, 100.0%] (n=53, q=53) | 97.9% [93.6%, 100.0%] (n=47, q=47) | 100.0% [100.0%, 100.0%] (n=41, q=41) | 100.0% [100.0%, 100.0%] (n=53, q=53) |
