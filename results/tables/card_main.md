# Quantity Validity Card (main DOSE)

Generated: 2026-09-29T10:58:01.389867+00:00

Canonical pipeline: `scripts/compute_paper_numbers.py`. Cluster-bootstrap by `base_id`, seed 42, 1000 resamples.

| Metric | Verifier | Subset | Conditioning | Rate [95% CI] | n | Sources |
| --- | --- | --- | --- | --- | ---: | --- |
| **C0** | Mistral-Small-24B (MedScore) | C0 all | unconditional on C0 | 1.000 [1.000, 1.000] | 114 | `results/raw/v1_medscore.jsonl` |
| **NS** | Mistral-Small-24B (MedScore) | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | 0.954 [0.918, 0.982] | 219 | `results/raw/v1_medscore.jsonl` |
| **QI** | Mistral-Small-24B (MedScore) | INV-claim all magnitudes | | C0 PASS | 0.661 [0.536, 0.786] | 56 | `results/raw/v1_medscore.jsonl` |
| **QI** | Mistral-Small-24B (MedScore) | INV-unit natural | | C0 PASS | 0.661 [0.536, 0.786] | 56 | `results/raw/v1_medscore.jsonl` |
| **US** | Mistral-Small-24B (MedScore) | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw/v1_medscore.jsonl` |
| **C0** | MiniCheck-Flan-T5-Large | C0 all | unconditional on C0 | 0.965 [0.930, 0.991] | 115 | `results/raw/v2a_minicheck.jsonl` |
| **NS** | MiniCheck-Flan-T5-Large | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | 0.892 [0.840, 0.939] | 213 | `results/raw/v2a_minicheck.jsonl` |
| **QI** | MiniCheck-Flan-T5-Large | INV-claim all magnitudes | | C0 PASS | 0.091 [0.018, 0.182] | 55 | `results/raw/v2a_minicheck.jsonl` |
| **QI** | MiniCheck-Flan-T5-Large | INV-unit natural | | C0 PASS | 0.091 [0.018, 0.182] | 55 | `results/raw/v2a_minicheck.jsonl` |
| **US** | MiniCheck-Flan-T5-Large | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw/v2a_minicheck.jsonl` |
| **C0** | AlignScore-large | C0 all | unconditional on C0 | 0.948 [0.896, 0.983] | 115 | `results/raw/v3_alignscore.jsonl` |
| **NS** | AlignScore-large | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | 0.943 [0.901, 0.976] | 209 | `results/raw/v3_alignscore.jsonl` |
| **QI** | AlignScore-large | INV-claim all magnitudes | | C0 PASS | 0.241 [0.130, 0.370] | 54 | `results/raw/v3_alignscore.jsonl` |
| **QI** | AlignScore-large | INV-unit natural | | C0 PASS | 0.241 [0.130, 0.370] | 54 | `results/raw/v3_alignscore.jsonl` |
| **US** | AlignScore-large | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw/v3_alignscore.jsonl` |
| **C0** | Llama-3.3-70B (RAGAS NLI) | C0 all | unconditional on C0 | 1.000 [1.000, 1.000] | 108 | `results/raw/v4_ragas_nli.llama.jsonl` |
| **NS** | Llama-3.3-70B (RAGAS NLI) | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | 0.929 [0.884, 0.965] | 198 | `results/raw/v4_ragas_nli.llama.jsonl` |
| **QI** | Llama-3.3-70B (RAGAS NLI) | INV-claim all magnitudes | | C0 PASS | 0.770 [0.656, 0.869] | 61 | `results/raw/v4_ragas_nli.llama.jsonl` |
| **QI** | Llama-3.3-70B (RAGAS NLI) | INV-unit natural | | C0 PASS | 0.765 [0.627, 0.882] | 51 | `results/raw/v4_ragas_nli.llama.jsonl` |
| **US** | Llama-3.3-70B (RAGAS NLI) | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw/v4_ragas_nli.llama.jsonl` |

