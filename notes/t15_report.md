# T15 evaluation — QVC card (base vs fine-tuned MiniCheck-RoBERTa)

Main **DOSE** cohort (`instances_main.jsonl`): non-dose bases excluded, `analysis_keep_row`, bootstrap **1000** × `base_id`, seed **42**. Metrics **| C0 PASS** except C0 row. Same definitions as `scripts/compute_paper_numbers.py`.

env: **cpuverif** (`results/raw/t15_cpuverif`, base and ft scored in separate processes); verdict agreement with the earlier vllm-env files is in `notes/t15_card_cpuverif_agreement.json`.

| Leg | C0 bases scored | C0 PASS bases | QI all | QI nat | NS (E1-evid FAIL) | US claim↑ (×1000) | US evid↑ (×1000) | US claim↓ (unit-down) | US evid↓ (unit-down) |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| base | 110 | 99 | 5.5% [0.0%, 12.7%] (n=55, q=55) | 0.0% [0.0%, 0.0%] (n=20, q=20) | 94.7% [90.9%, 97.9%] (n=189, q=96) | 32.3% [24.0%, 41.7%] (n=96, q=96) | 20.8% [13.5%, 29.2%] (n=96, q=96) | 7.1% [1.4%, 12.9%] (n=70, q=70) | 5.7% [1.4%, 11.4%] (n=70, q=70) |
| ft | 110 | 102 | 96.5% [91.2%, 100.0%] (n=57, q=57) | 95.2% [85.7%, 100.0%] (n=21, q=21) | 97.9% [95.4%, 100.0%] (n=195, q=99) | 100.0% [100.0%, 100.0%] (n=99, q=99) | 98.0% [94.9%, 100.0%] (n=99, q=99) | 100.0% [100.0%, 100.0%] (n=71, q=71) | 98.6% [95.8%, 100.0%] (n=71, q=71) |

## AggreFact test (paired base vs ft)

- env: **cpuverif** (`results/raw/t15_cpuverif`)
- Test split rows in file: **29320** · scored paired: **29320**

Metric: balanced accuracy = (TPR + TNR) / 2 per dataset; **LLM-AggreFact BAcc = unweighted mean over the 11 datasets**. Micro BAcc pools all rows; accuracy shown for reference only.

- **base** LLM-AggreFact BAcc (macro over datasets)=0.7351 · micro BAcc=0.7632 · accuracy=0.7263 (n=29320 paired)
- **ft** LLM-AggreFact BAcc (macro over datasets)=0.7180 · micro BAcc=0.7292 · accuracy=0.7297 (n=29320 paired)

| Dataset | n | base BAcc | ft BAcc | Δ (ft − base) |
| --- | ---: | ---: | ---: | ---: |
| AggreFact-CNN | 558 | 0.6375 | 0.5906 | -0.0469 |
| AggreFact-XSum | 558 | 0.7076 | 0.7256 | +0.0181 |
| ClaimVerify | 1088 | 0.7758 | 0.7177 | -0.0581 |
| ExpertQA | 3702 | 0.5743 | 0.5708 | -0.0035 |
| FactCheck-GPT | 1566 | 0.7328 | 0.7591 | +0.0263 |
| Lfqa | 1911 | 0.8436 | 0.8442 | +0.0006 |
| RAGTruth | 16371 | 0.7719 | 0.7332 | -0.0387 |
| Reveal | 1710 | 0.8881 | 0.8079 | -0.0802 |
| TofuEval-MediaS | 726 | 0.7193 | 0.7072 | -0.0121 |
| TofuEval-MeetB | 772 | 0.7594 | 0.7774 | +0.0180 |
| Wice | 358 | 0.6757 | 0.6641 | -0.0116 |

