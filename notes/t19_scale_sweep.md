# T19 scale sweep (RAGAS-NLI)

Cohort: `data/t19/instances_t19.jsonl` (n=1623 instances). Cluster-bootstrap by `base_id`, seed 42, 1000 resamples (matches `compute_paper_numbers.py`).

**Shared conditioning:** `n_c0_pass_bases` = bases with C0 PASS on main_dose (per model). QI/NS/US use that base set; row `bases=` is clustered units contributing to each metric.

| Model | C0 | QI all | QI nat | NS claim | NS evid | NS ÷2 (T17) | NS ÷10 (T17) | US claim ×1k | US evid ×1k | US unit÷ (T17) | Rephrase |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1B (local) | 87.6% [81.0, 93.3] (n=105, bases=105) | 87.8% [77.6, 95.9] (n=49, bases=49) | 94.1% [82.4, 100.0] (n=17, bases=17) | 5.3% [1.8, 9.9] (n=169, bases=89) | 8.1% [3.5, 13.7] (n=173, bases=90) | 7.7% [3.6, 12.4] (n=169, bases=90) | 6.2% [2.2, 11.4] (n=176, bases=91) | 3.5% [0.0, 7.1] (n=85, bases=85) | 1.2% [0.0, 4.7] (n=86, bases=86) | 7.2% [3.1, 12.1] (n=125, bases=64) | 90.1% [85.0, 94.4] (n=212, bases=105) |
| 3B (local) | 83.3% [50.0, 100.0] (n=6, bases=6) | NA | NA | 90.0% [70.0, 100.0] (n=10, bases=5) | 87.5% [66.7, 100.0] (n=8, bases=5) | NA | NA | NA | NA | NA | NA |
| 8B (local) | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 8B (API) | 97.2% [93.6, 100.0] (n=109, bases=109) | 27.6% [17.2, 39.7] (n=58, bases=58) | 27.3% [9.1, 45.5] (n=22, bases=22) | 99.5% [98.5, 100.0] (n=203, bases=103) | 95.6% [92.6, 98.0] (n=203, bases=103) | NA | NA | 83.5% [76.7, 89.3] (n=103, bases=103) | 47.6% [38.8, 56.3] (n=103, bases=103) | NA | NA |
| 70B (API Llama-3.3) | 100.0% [100.0, 100.0] (n=109, bases=109) | 75.8% [64.5, 85.5] (n=62, bases=62) | 72.7% [54.5, 86.4] (n=22, bases=22) | 97.1% [94.7, 99.0] (n=209, bases=106) | 92.3% [88.0, 96.2] (n=209, bases=106) | NA | NA | NA | NA | NA | 100.0% [100.0, 100.0] (n=227, bases=109) |

Per model: `n_c0_pass_bases`, `n_bases_qi_all`, `n_bases_qi_nat` in `notes/t19_scale_sweep.json`.

_E2: no E2 rows in T19 cohort._
