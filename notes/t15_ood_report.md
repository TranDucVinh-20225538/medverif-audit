# T15 OOD — base vs fine-tuned MiniCheck-RoBERTa

Perturbation cells are FAIL rates among units whose C0 is PASS. Bootstrap 1000 × cluster (T24b: question_id; T18: base_id), seed 42. n = instances, q = clusters.

- **T24b**: `data/t24/instances_t24b.jsonl`, excluded questions T24_037, T24_066 (as in `t24b_report.py`).
- **T18 (Wikipedia, non-medical)**: `data/t18/instances_t18_t15ood.jsonl` — reviewed C0 from `data/t18/instances_t18.jsonl`; value ×10 = `E1-claim x10` rows from build `7d8e919` reused only where C0 claim+evidence are identical (the reviewed pack has ×2/÷2 only); unit up/down = reviewed `E1-unit` unit_swap split by `unit_pair` direction.

| Pack | Leg | C0 PASS | Value×10 FAIL|C0 | Unit-up FAIL|C0 | Unit-down FAIL|C0 |
| --- | --- | --- | --- | --- | --- |
| T24b real answers | base | 84.9% [73.6, 94.3] (n=53, q=53) | 100.0% [100.0, 100.0] (n=45, q=45) | 59.0% [43.6, 74.4] (n=39, q=39) | 11.8% [2.9, 23.5] (n=34, q=34) |
| T24b real answers | ft | 88.7% [79.2, 96.2] (n=53, q=53) | 97.9% [93.6, 100.0] (n=47, q=47) | 100.0% [100.0, 100.0] (n=41, q=41) | 100.0% [100.0, 100.0] (n=37, q=37) |
| T18 Wikipedia | base | 100.0% [100.0, 100.0] (n=37, q=37) | 100.0% [100.0, 100.0] (n=32, q=32) | 100.0% [100.0, 100.0] (n=15, q=15) | 100.0% [100.0, 100.0] (n=22, q=22) |
| T18 Wikipedia | ft | 100.0% [100.0, 100.0] (n=37, q=37) | 100.0% [100.0, 100.0] (n=32, q=32) | 100.0% [100.0, 100.0] (n=15, q=15) | 100.0% [100.0, 100.0] (n=22, q=22) |
