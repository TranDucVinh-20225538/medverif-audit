# T14 — pass rates conditional on C0 PASS

Among **main DOSE** bases where the verifier **PASS**es **C0**, report **P(PASS)** on each T14 claim-side family (expected PASS). **QI** column: same conditioning for **INV-unit natural** (conversion) — higher is better.

- T14 pack sizes: unit_spell **112**, spacing **112**, symbol **9**.
- Appendix: Not scored in main pack; n=3 bases would qualify (comma/plain ≥1000).

| model | family | C0 pass rate | n C0 | QI (INV nat | C0) | unit spell | spacing | symbol |
|---|---|---:|---:|---:|---:|---:|---:|
| AlignScore-base | small fine-tuned checkers | 0.927 (n=110) | 102 | 0.227 (n=22) | 0.990 (n=101) | 1.000 (n=101) | 1.000 (n=7) |
| Granite Guardian 2B | small fine-tuned checkers | 0.982 (n=110) | 108 | 0.190 (n=21) | 1.000 (n=107) | 1.000 (n=107) | 0.889 (n=9) |
| HHEM | small fine-tuned checkers | 0.973 (n=110) | 107 | 0.143 (n=21) | — (n=0) | — (n=0) | — (n=0) |
| MiniCheck-DeBERTa | small fine-tuned checkers | 0.900 (n=110) | 99 | 0.050 (n=20) | 0.969 (n=98) | 1.000 (n=98) | 0.857 (n=7) |
| MiniCheck-RoBERTa | small fine-tuned checkers | 0.900 (n=110) | 99 | 0.000 (n=20) | 0.990 (n=98) | 1.000 (n=98) | 0.875 (n=8) |
| SummaC-Conv | small fine-tuned checkers | 0.745 (n=110) | 82 | 0.000 (n=17) | — (n=0) | — (n=0) | — (n=0) |
| SummaC-ZS | small fine-tuned checkers | 0.800 (n=110) | 88 | 0.059 (n=17) | 1.000 (n=87) | 1.000 (n=87) | 1.000 (n=7) |
| MiniCheck-Flan-T5-Large | small fine-tuned checkers | 0.964 (n=110) | 106 | 0.045 (n=22) | 1.000 (n=105) | 1.000 (n=105) | 0.875 (n=8) |
| AlignScore-large | small fine-tuned checkers | 0.945 (n=110) | 104 | 0.190 (n=21) | 1.000 (n=103) | 1.000 (n=103) | 0.714 (n=7) |
| Bespoke-MiniCheck-7B | 7B fine-tuned checker | 1.000 (n=110) | 110 | 0.818 (n=22) | — (n=0) | — (n=0) | — (n=0) |
| Mistral-Small-24B (MedScore) | LLM judges | 1.000 (n=110) | 110 | 0.636 (n=22) | 1.000 (n=109) | 1.000 (n=109) | 1.000 (n=9) |
| GPT-4o (MedScore) | LLM judges | 1.000 (n=110) | 110 | 1.000 (n=22) | 0.990 (n=101) | 1.000 (n=102) | 1.000 (n=9) |
| GPT-4o-mini (MedScore) | LLM judges | 0.991 (n=110) | 109 | 0.500 (n=22) | — (n=0) | — (n=0) | — (n=0) |
| Llama-3.3-70B (RAGAS NLI) | LLM judges | 1.000 (n=109) | 109 | 0.727 (n=22) | 1.000 (n=109) | 1.000 (n=109) | 1.000 (n=9) |
| Claude Sonnet 4.6 (RAGAS NLI) | LLM judges | 1.000 (n=110) | 110 | 1.000 (n=22) | 1.000 (n=61) | 1.000 (n=61) | 1.000 (n=6) |
| GPT-4o-mini (RAGAS) | LLM judges | 0.964 (n=110) | 106 | 0.864 (n=22) | — (n=0) | — (n=0) | — (n=0) |
| Claude Haiku 4.5 (RAGAS) | LLM judges | 0.973 (n=110) | 107 | 1.000 (n=21) | — (n=0) | — (n=0) | — (n=0) |
| Llama-3.1-8B (RAGAS) | LLM judges | 0.972 (n=109) | 106 | 0.273 (n=22) | — (n=0) | — (n=0) | — (n=0) |
| Mistral-Small-3.2-24B (RAGAS) | LLM judges | 1.000 (n=110) | 110 | 1.000 (n=22) | — (n=0) | — (n=0) | — (n=0) |
