# T14 — pass rates conditional on C0 PASS

Among **main DOSE** bases where the verifier **PASS**es **C0**, report **P(PASS)** on each T14 claim-side family (expected PASS). **QI** column: same conditioning for **INV-unit natural** (conversion) — higher is better.

- T14 pack sizes: unit_spell **112**, spacing **112**, symbol **9**.
- Appendix: Not scored in main pack; n=3 bases would qualify (comma/plain ≥1000).

| model | family | C0 pass rate | n C0 | QI (INV nat | C0) | unit spell | spacing | symbol |
|---|---|---:|---:|---:|---:|---:|---:|
| AlignScore-base | small fine-tuned checkers | 0.957 (n=23) | 22 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| Granite Guardian | small fine-tuned checkers | 1.000 (n=23) | 23 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| HHEM | small fine-tuned checkers | 0.957 (n=23) | 22 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| MiniCheck-DeBERTa | small fine-tuned checkers | 0.870 (n=23) | 20 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| MiniCheck-RoBERTa | small fine-tuned checkers | 0.913 (n=23) | 21 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| SummaC-Conv | small fine-tuned checkers | 0.652 (n=23) | 15 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| SummaC-ZS | small fine-tuned checkers | 0.826 (n=23) | 19 | — (n=0) | — (n=0) | — (n=0) | — (n=0) |
| MiniCheck-Flan-T5-Large | small fine-tuned checkers | 0.965 (n=115) | 111 | 0.091 (n=55) | — (n=0) | — (n=0) | — (n=0) |
| AlignScore-large | small fine-tuned checkers | 0.948 (n=115) | 109 | 0.241 (n=54) | — (n=0) | — (n=0) | — (n=0) |
| Bespoke-MiniCheck-7B | 7B fine-tuned checker | 1.000 (n=115) | 115 | 0.804 (n=56) | — (n=0) | — (n=0) | — (n=0) |
| Mistral-Small-24B (MedScore) | LLM judges | 1.000 (n=115) | 115 | 0.661 (n=56) | 1.000 (n=112) | 1.000 (n=112) | 1.000 (n=9) |
| GPT-4o (MedScore) | LLM judges | 1.000 (n=115) | 115 | 0.964 (n=56) | 0.990 (n=103) | 1.000 (n=104) | 1.000 (n=9) |
| GPT-4o-mini (MedScore) | LLM judges | 0.991 (n=115) | 114 | 0.509 (n=55) | — (n=0) | — (n=0) | — (n=0) |
| Llama-3.3-70B (RAGAS NLI) | LLM judges | 1.000 (n=111) | 111 | 0.774 (n=53) | 1.000 (n=108) | 1.000 (n=108) | 1.000 (n=9) |
| Claude Sonnet 4.6 (RAGAS NLI) | LLM judges | 1.000 (n=115) | 115 | 0.964 (n=56) | 1.000 (n=61) | 1.000 (n=61) | 1.000 (n=6) |
| GPT-4o-mini (RAGAS) | LLM judges | 0.965 (n=115) | 111 | 0.778 (n=54) | — (n=0) | — (n=0) | — (n=0) |
| Claude Haiku 4.5 (RAGAS) | LLM judges | 0.974 (n=115) | 112 | 0.964 (n=55) | — (n=0) | — (n=0) | — (n=0) |
| Llama-3.1-8B (RAGAS) | LLM judges | 0.965 (n=114) | 110 | 0.269 (n=52) | — (n=0) | — (n=0) | — (n=0) |
| Mistral-Small-3.2-24B (RAGAS) | LLM judges | 1.000 (n=115) | 115 | 0.964 (n=56) | — (n=0) | — (n=0) | — (n=0) |
