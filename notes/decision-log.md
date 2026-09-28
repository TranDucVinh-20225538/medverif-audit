# QC v3 decision log (PI review)

| ID | Summary |
| --- | --- |
| **G** | INV-paraphrase: LLM rewrite only (no clause rotation). Grammar, no added hedge, second-LLM equivalence. Add POLARITY rephrase INV (`should not be used` ↔ `is contraindicated`). |
| **H** | POLARITY flip only if predicate ends clause or continues with `for/in` + patient/condition NP; exclude adjuncts (`at`, `with`, `as needed`, `when`, `annually`, `regularly`, `in full`, `for` + duration/purpose) and coordinated VPs. Caution: `with (great\|extreme )?caution`. **P0143** invalid (subject not intervention). |
| **I** | Main analysis POLARITY: `domain_kind==treatment` only; `unclear` reported separately. |
| **J** | DOSE span that is a range endpoint (`X to/–/or Y`) → `subset=range`, out of main. |
| **K** | Sensitivity analysis excluding `ocr_noise==True`. |

Applied in code: `src/qc_v3.py`, `src/apply_qc_v3_decisions.py`, `src/apply_v3.py`, `analysis/analyze.py`.
