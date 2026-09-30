# T15 evaluation — QVC card (base vs fine-tuned MiniCheck-RoBERTa)

Main **DOSE** cohort (`instances_main.jsonl`): non-dose bases excluded, `analysis_keep_row`, bootstrap **1000** × `base_id`, seed **42**. Metrics **| C0 PASS** except C0 row. Same definitions as `scripts/compute_paper_numbers.py`.

| Leg | C0 bases scored | C0 PASS bases | QI all | QI nat | NS (E1-evid FAIL) | US claim↑ (×1000) | US evid↑ (×1000) | US claim↓ (unit-down) | US evid↓ (unit-down) |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| base | 110 | 99 | 5.5% [0.0%, 12.7%] (n=55, q=55) | 0.0% [0.0%, 0.0%] (n=20, q=20) | 94.7% [90.9%, 97.9%] (n=189, q=96) | 32.3% [24.0%, 41.7%] (n=96, q=96) | 20.8% [13.5%, 29.2%] (n=96, q=96) | 7.1% [1.4%, 12.9%] (n=70, q=70) | 5.7% [1.4%, 11.4%] (n=70, q=70) |
| ft | 110 | 102 | 96.5% [91.2%, 100.0%] (n=57, q=57) | 95.2% [85.7%, 100.0%] (n=21, q=21) | 97.9% [95.4%, 100.0%] (n=195, q=99) | 100.0% [100.0%, 100.0%] (n=99, q=99) | 98.0% [94.9%, 100.0%] (n=99, q=99) | 100.0% [100.0%, 100.0%] (n=71, q=71) | 98.6% [95.8%, 100.0%] (n=71, q=71) |

## AggreFact test (paired base vs ft)

- Test split rows in file: **29320** · scored paired: **29320**

- **base** overall balanced acc=0.7263 (n=29320 paired)
  - AggreFact-CNN: 0.7957 (n=558)
  - AggreFact-XSum: 0.7061 (n=558)
  - ClaimVerify: 0.7969 (n=1088)
  - ExpertQA: 0.4525 (n=3702)
  - FactCheck-GPT: 0.8206 (n=1566)
  - Lfqa: 0.8336 (n=1911)
  - RAGTruth: 0.7410 (n=16371)
  - Reveal: 0.8632 (n=1710)
  - TofuEval-MediaS: 0.7521 (n=726)
  - TofuEval-MeetB: 0.7876 (n=772)
  - Wice: 0.7682 (n=358)
- **ft** overall balanced acc=0.7297 (n=29320 paired)
  - AggreFact-CNN: 0.7115 (n=558)
  - AggreFact-XSum: 0.7258 (n=558)
  - ClaimVerify: 0.7849 (n=1088)
  - ExpertQA: 0.5313 (n=3702)
  - FactCheck-GPT: 0.8052 (n=1566)
  - Lfqa: 0.8514 (n=1911)
  - RAGTruth: 0.7422 (n=16371)
  - Reveal: 0.7456 (n=1710)
  - TofuEval-MediaS: 0.7672 (n=726)
  - TofuEval-MeetB: 0.8329 (n=772)
  - Wice: 0.7179 (n=358)

