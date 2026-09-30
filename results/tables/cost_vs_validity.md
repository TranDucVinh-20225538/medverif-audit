# Cost vs validity (T1)

Instances: `data/v3/instances_cpu_early.jsonl` (n=1306).

**Metrics (DOSE, conditional on C0 PASS):** invariance = INV-claim PASS rate; sensitivity = E1-evid FAIL rate (higher = better). PARSE_FAIL excluded.

| Verifier | Verifier type | $/1k claims | Paper BAcc (AggreFact) | Source | Inv (raw) | Sens (raw) | Inv (M1 infer)* | Sens (M1 infer)* | Inv (M1+M2†) | Sens (M1+M2†) |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V1 (Mistral OR) | LLM-based checker | $0.03 | 0.72 | https://arxiv.org/abs/2609.30467 | 0.671 | 0.954 | 0.942 | 0.952 | 0.630 | 1.000 |
| V4 (Llama OR) | LLM judge | $0.00 | 0.75 | https://arxiv.org/abs/2309.15217 | 0.818 | 1.000 | 0.933 | 1.000 | 0.625 | 1.000 |
| V2a (MiniCheck, node30) | encoder-NLI checker | $0.00 | 0.78 | https://arxiv.org/abs/2404.04881 | 0.121 | 0.880 | 0.833 | 0.859 | 0.098 | 1.000 |
| V3 (AlignScore, node30) | encoder-NLI checker | $0.00 | 0.81 | https://arxiv.org/abs/2305.16739 | 0.292 | 0.911 | 0.915 | 0.876 | 0.240 | 1.000 |

\* **M1 infer:** scores from `results/raw_m1/` with `MEDVERIF_M1=1` at inference (job `t1_m1_rescore`). Em dash until re-score completes.

† **M1+M2 hybrid:** post-hoc M2 quantity veto on M1-normalized claim/evidence (no extra LLM calls).

Paper BAcc notes:
- **v1_medscore:** MedScore open Mistral-24B on AggreFact-style eval (arXiv:2609.30467 Table 2, BAcc column; verify against published table)
- **v4_ragas_nli:** RAGAS faithfulness NLI-style judge BAcc on AggreFact subset (Es et al., 2023; RAGAS paper Table — verify exact row)
- **v2a_minicheck:** MiniCheck-Flan-T5-Large reported BAcc on LLM-AggreFact (Tang et al., 2024 Table 1)
- **v3_alignscore:** AlignScore-large BAcc on AggreFact (Zha et al., ACL 2023; evaluate.py balanced accuracy @ 0.5)
