# T19 scale sweep (RAGAS-NLI)

Cohort: `data/t19/instances_t19.jsonl` (n=1623 instances; non-dose excluded).

**QI definition (all models):** subset **natural INV-unit**; conditioning **| C0 PASS** (verifier-specific); exclusions **non_dose_targets** on main slice; scores under `results/raw/t19/` (70B: `results/raw/v4_ragas_nli.llama.jsonl` + T14 overlap).

**70B QI line:** 72.7% [54.5,86.4], n_inv=22 — see `notes/reconcile_llama70b_qi.md` (not M1 table 84.9% Qwen; not ~91% NS).

| Params | Model | QI | NS | US | C0 pass | n(inv) | n(E1) | AUROC C0 vs Conv | AUROC Conv vs Unit |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1B | 1B | 94.1% [82.4,100.0] | 5.3% [3.3,7.2] | 94.1% | 87.6% [81.0,93.3] | 17 | 513 | 0.531 | 0.505 |
| 3B | 3B | NA | NA | NA | NA | 0 | 0 | NA | NA |
| 8B | 8B (local) | NA | NA | NA | NA | 0 | 0 | NA | NA |
| 70B | 70B (API) | 72.7% [54.5,86.4] | 94.7% [92.6,96.7] | 72.7% | 100.0% [100.0,100.0] | 22 | 418 | NA | NA |

**8B local vs API (T6-B Llama-3.1-8B) verdict agreement:** 0.0% (n=0).
