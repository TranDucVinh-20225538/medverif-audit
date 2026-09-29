# QC v3 decision log (PI review)

| ID | Summary |
| --- | --- |
| **G** | INV-paraphrase: LLM rewrite only (no clause rotation). Grammar, no added hedge, second-LLM equivalence. Add POLARITY rephrase INV (`should not be used` ↔ `is contraindicated`). |
| **H** | POLARITY flip only if predicate ends clause or continues with `for/in` + patient/condition NP; exclude adjuncts (`at`, `with`, `as needed`, `when`, `annually`, `regularly`, `in full`, `for` + duration/purpose) and coordinated VPs. Caution: `with (great\|extreme )?caution`. **P0143** invalid (subject not intervention). |
| **I** | Main analysis POLARITY: `domain_kind==treatment` only; `unclear` reported separately. |
| **J** | DOSE span that is a range endpoint (`X to/–/or Y`) → `subset=range`, out of main. |
| **K** | Sensitivity analysis excluding `ocr_noise==True`. |
| **L** | **2026-09-29 — QC v3 GPU paraphrase (Qwen+Phi / `label_v3`, `label_v3b`) ON HOLD.** Do not run while `notes/HOLD_medverif_v3` exists. **Do not rewrite** `data/v3/instances_main*` or any JSONL that existing **`results/raw/**` scores reference. If decision **G** paraphrase is revived: outputs go only under **`data/v3_para/`** (separate pack + new `condition` slug), full rescore as a **new** arm — never replace or merge into the locked main set. T19 unchanged (await HF Llama license). |

Applied in code: `src/qc_v3.py`, `src/apply_qc_v3_decisions.py`, `src/apply_v3.py`, `analysis/analyze.py`.  
**Not applied to main instances while L is active:** `src/generate_v3.py`, `src/label_v3b.py`, `jobs/label_v3.sbatch`, `jobs/label_v3b.sbatch`.
