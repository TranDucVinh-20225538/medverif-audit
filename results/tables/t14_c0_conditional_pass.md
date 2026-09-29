# T14 — pass rates conditional on C0 PASS

Among **main DOSE** bases where the verifier **PASS**es **C0**, report **P(PASS)** on each T14 claim-side family (expected PASS). **QI** column: same conditioning for **INV-unit natural** (conversion) — higher is better.

- T14 pack sizes: unit_spell **114**, spacing **114**, symbol **9**.
- Appendix: Not scored in main pack; n=3 bases would qualify (comma/plain ≥1000).

| model | family | C0 pass rate | n C0 | QI (INV nat | C0) | unit spell | spacing | symbol |
|---|---|---:|---:|---:|---:|---:|---:|
| AlignScore-base | small fine-tuned checkers | 0.955 (n=22) | 21 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| Granite Guardian | small fine-tuned checkers | 1.000 (n=22) | 22 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| HHEM | small fine-tuned checkers | 0.955 (n=22) | 21 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| MiniCheck-DeBERTa | small fine-tuned checkers | 0.864 (n=22) | 19 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| MiniCheck-RoBERTa | small fine-tuned checkers | 0.909 (n=22) | 20 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| SummaC-Conv | small fine-tuned checkers | 0.636 (n=22) | 14 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| SummaC-ZS | small fine-tuned checkers | 0.818 (n=22) | 18 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| MiniCheck-Flan-T5-Large | small fine-tuned checkers | 0.965 (n=114) | 110 | 0.093 (n=54) | — (n=0) | — (n=0) | — (n=0) |
| AlignScore-large | small fine-tuned checkers | 0.947 (n=114) | 108 | 0.245 (n=53) | — (n=0) | — (n=0) | — (n=0) |
| Bespoke-MiniCheck-7B | 7B fine-tuned checker | 1.000 (n=114) | 114 | 0.800 (n=55) | — (n=0) | — (n=0) | — (n=0) |
| Mistral-Small-24B (MedScore) | LLM judges | 1.000 (n=114) | 114 | 0.655 (n=55) | — (n=0) | — (n=0) | — (n=0) |
| GPT-4o (MedScore) | LLM judges | 1.000 (n=114) | 114 | 0.964 (n=55) | — (n=0) | — (n=0) | — (n=0) |
| GPT-4o-mini (MedScore) | LLM judges | 0.991 (n=114) | 113 | 0.500 (n=54) | — (n=0) | — (n=0) | — (n=0) |
| Llama-3.3-70B (RAGAS NLI) | LLM judges | 1.000 (n=110) | 110 | 0.769 (n=52) | — (n=0) | — (n=0) | — (n=0) |
| Claude Sonnet 4.6 (RAGAS NLI) | LLM judges | 1.000 (n=114) | 114 | 0.964 (n=55) | — (n=0) | — (n=0) | — (n=0) |
| GPT-4o-mini (RAGAS) | LLM judges | 0.965 (n=114) | 110 | 0.774 (n=53) | — (n=0) | — (n=0) | — (n=0) |
| Claude Haiku 4.5 (RAGAS) | LLM judges | 0.974 (n=114) | 111 | 0.963 (n=54) | — (n=0) | — (n=0) | — (n=0) |
| Llama-3.1-8B (RAGAS) | LLM judges | 0.973 (n=113) | 110 | 0.250 (n=52) | — (n=0) | — (n=0) | — (n=0) |
| Mistral-Small-3.2-24B (RAGAS) | LLM judges | 1.000 (n=114) | 114 | 0.964 (n=55) | — (n=0) | — (n=0) | — (n=0) |
