# T19 scale sweep (RAGAS-NLI)

Cohort: `data/t19/instances_t19.jsonl` (n=1060 instances; non-dose excluded).

| Params | Model | QI | NS | US | C0 pass | n(inv) | n(E1) | AUROC C0 vs Conv | AUROC Conv vs Unit |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1B | 1B | NA | NA | NA | NA | 0 | 0 | NA | NA |
| 3B | 3B | NA | NA | NA | NA | 0 | 0 | NA | NA |
| 8B | 8B (local) | NA | NA | NA | NA | 0 | 0 | NA | NA |
| 70B | 70B (API) | 76.5% [62.7,88.2] | 95.0% [92.8,97.0] | 76.5% | 100.0% [100.0,100.0] | 51 | 400 | NA | NA |

**8B local vs API (T6-B Llama-3.1-8B) verdict agreement:** 0.0% (n=0).
