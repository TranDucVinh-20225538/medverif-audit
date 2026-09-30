# T19 scale sweep (RAGAS-NLI)

Cohort: `data/t19/instances_t19.jsonl` (n=1703 instances). Cluster-bootstrap by `base_id`, seed 42, 1000 resamples (matches `compute_paper_numbers.py`).

**Shared conditioning:** `n_c0_pass_bases` = bases with C0 PASS on main_dose (per model). QI/NS/US use that base set; row `bases=` is clustered units contributing to each metric.

| Model | C0 | QI all | QI nat | NS claim | NS evid | NS ÷2 (T17) | NS ÷10 (T17) | US claim ×1k | US evid ×1k | US unit÷ (T17) | Rephrase (POL) | T14_repr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1B (local) | 87.6% [81.0, 93.3] (n=105, bases=105) | 87.8% [77.6, 95.9] (n=49, bases=49) | 94.1% [82.4, 100.0] (n=17, bases=17) | 5.3% [1.8, 9.9] (n=169, bases=89) | 8.1% [3.5, 13.7] (n=173, bases=90) | 7.7% [3.6, 12.4] (n=169, bases=90) | 6.2% [2.2, 11.4] (n=176, bases=91) | 3.5% [0.0, 7.1] (n=85, bases=85) | 1.2% [0.0, 4.7] (n=86, bases=86) | 7.2% [3.1, 12.1] (n=125, bases=64) | NA | 90.1% [85.0, 94.4] (n=212, bases=105) |
| 3B (local) | 87.5% [79.6, 95.3] (n=64, bases=64) | 13.0% [0.0, 26.1] (n=23, bases=23) | 22.2% [0.0, 44.4] (n=9, bases=9) | 91.4% [84.4, 96.9] (n=93, bases=52) | 77.4% [67.1, 86.5] (n=93, bases=51) | 89.9% [82.8, 96.0] (n=99, bases=50) | 87.2% [79.6, 93.9] (n=94, bases=52) | 100.0% [100.0, 100.0] (n=48, bases=48) | 67.3% [55.1, 79.6] (n=49, bases=49) | 80.3% [68.6, 90.3] (n=71, bases=39) | NA | 91.4% [85.0, 96.6] (n=151, bases=86) |
| 8B (local) | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| 8B (API) | 97.2% [93.6, 100.0] (n=109, bases=109) | 27.6% [17.2, 39.7] (n=58, bases=58) | 27.3% [9.1, 45.5] (n=22, bases=22) | 99.5% [98.5, 100.0] (n=203, bases=103) | 95.6% [92.6, 98.0] (n=203, bases=103) | 97.6% [95.2, 99.5] (n=210, bases=105) | 97.1% [94.3, 99.5] (n=210, bases=105) | 83.5% [76.7, 89.3] (n=103, bases=103) | 47.6% [38.8, 56.3] (n=103, bases=103) | 73.3% [65.1, 80.8] (n=146, bases=73) | 100.0% [100.0, 100.0] (n=34, bases=34) | NA |
| 70B (API Llama-3.3) | 100.0% [100.0, 100.0] (n=109, bases=109) | 75.8% [64.5, 85.5] (n=62, bases=62) | 72.7% [54.5, 86.4] (n=22, bases=22) | 97.1% [94.7, 99.0] (n=209, bases=106) | 92.3% [88.0, 96.2] (n=209, bases=106) | 92.6% [88.0, 96.3] (n=216, bases=108) | 95.3% [91.6, 98.1] (n=214, bases=108) | NA | NA | 75.7% [69.1, 82.2] (n=152, bases=76) | 100.0% [100.0, 100.0] (n=34, bases=34) | 100.0% [100.0, 100.0] (n=227, bases=109) |

Per model: `n_c0_pass_bases`, `n_pol_c0_pass_bases`, QI base counts in `notes/t19_scale_sweep.json`.

**T14_repr by family** (when n>0):
- **1B (local)** T14_repr by family: spacing: 86.1% [79.2, 93.1] (n=101, bases=101); symbol_micro: 100.0% [100.0, 100.0] (n=9, bases=9); unit_spell: 93.1% [88.2, 98.0] (n=102, bases=102)
- **3B (local)** T14_repr by family: spacing: 92.6% [86.4, 97.5] (n=81, bases=81); symbol_micro: 75.0% [50.0, 100.0] (n=8, bases=8); unit_spell: 91.9% [83.9, 98.4] (n=62, bases=62)
- **70B (API Llama-3.3)** T14_repr by family: spacing: 100.0% [100.0, 100.0] (n=109, bases=109); symbol_micro: 100.0% [100.0, 100.0] (n=9, bases=9); unit_spell: 100.0% [100.0, 100.0] (n=109, bases=109)

_E2: no E2 rows in T19 cohort._
