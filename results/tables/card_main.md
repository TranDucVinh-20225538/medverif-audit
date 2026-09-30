# Quantity Validity Card (main DOSE)

Generated: 2026-09-29T13:09:06.456794+00:00

Canonical pipeline: `scripts/compute_paper_numbers.py`. Cluster-bootstrap by `base_id`, seed 42, 1000 resamples.

| Metric | Verifier | Subset | Conditioning | Rate [95% CI] | n | Sources |
| --- | --- | --- | --- | --- | ---: | --- |
| **C0** | AlignScore-base | C0 all | unconditional on C0 | 0.930 [0.887, 0.974] | 115 | `results/raw_node30/t6_alignscore_base.jsonl` |
| **NS** | AlignScore-base | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_alignscore_base.jsonl` |
| **QI** | AlignScore-base | INV-claim all magnitudes | | C0 PASS | 0.194 [0.113, 0.290] | 62 | `results/raw_node30/t6_alignscore_base.jsonl` |
| **QI** | AlignScore-base | INV-unit natural | | C0 PASS | 0.200 [0.091, 0.309] | 55 | `results/raw_node30/t6_alignscore_base.jsonl` |
| **US** | AlignScore-base | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_alignscore_base.jsonl` |
| **C0** | Granite Guardian | C0 all | unconditional on C0 | 0.991 [0.974, 1.000] | 115 | `results/raw_node30/t6_granite_guardian.jsonl` |
| **NS** | Granite Guardian | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_granite_guardian.jsonl` |
| **QI** | Granite Guardian | INV-claim all magnitudes | | C0 PASS | 0.179 [0.090, 0.269] | 67 | `results/raw_node30/t6_granite_guardian.jsonl` |
| **QI** | Granite Guardian | INV-unit natural | | C0 PASS | 0.214 [0.107, 0.321] | 56 | `results/raw_node30/t6_granite_guardian.jsonl` |
| **US** | Granite Guardian | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_granite_guardian.jsonl` |
| **C0** | HHEM | C0 all | unconditional on C0 | 0.974 [0.939, 1.000] | 115 | `results/raw_node30/t6_hhem.jsonl` |
| **NS** | HHEM | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_hhem.jsonl` |
| **QI** | HHEM | INV-claim all magnitudes | | C0 PASS | 0.078 [0.016, 0.156] | 64 | `results/raw_node30/t6_hhem.jsonl` |
| **QI** | HHEM | INV-unit natural | | C0 PASS | 0.094 [0.019, 0.189] | 53 | `results/raw_node30/t6_hhem.jsonl` |
| **US** | HHEM | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_hhem.jsonl` |
| **C0** | MiniCheck-DeBERTa | C0 all | unconditional on C0 | 0.887 [0.826, 0.939] | 115 | `results/raw_node30/t6_minicheck_deberta.jsonl` |
| **NS** | MiniCheck-DeBERTa | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_minicheck_deberta.jsonl` |
| **QI** | MiniCheck-DeBERTa | INV-claim all magnitudes | | C0 PASS | 0.034 [0.000, 0.085] | 59 | `results/raw_node30/t6_minicheck_deberta.jsonl` |
| **QI** | MiniCheck-DeBERTa | INV-unit natural | | C0 PASS | 0.039 [0.000, 0.098] | 51 | `results/raw_node30/t6_minicheck_deberta.jsonl` |
| **US** | MiniCheck-DeBERTa | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_minicheck_deberta.jsonl` |
| **C0** | MiniCheck-RoBERTa | C0 all | unconditional on C0 | 0.904 [0.843, 0.957] | 115 | `results/raw_node30/t6_minicheck_roberta.jsonl` |
| **NS** | MiniCheck-RoBERTa | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_minicheck_roberta.jsonl` |
| **QI** | MiniCheck-RoBERTa | INV-claim all magnitudes | | C0 PASS | 0.067 [0.017, 0.133] | 60 | `results/raw_node30/t6_minicheck_roberta.jsonl` |
| **QI** | MiniCheck-RoBERTa | INV-unit natural | | C0 PASS | 0.077 [0.019, 0.154] | 52 | `results/raw_node30/t6_minicheck_roberta.jsonl` |
| **US** | MiniCheck-RoBERTa | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_minicheck_roberta.jsonl` |
| **C0** | SummaC-Conv | C0 all | unconditional on C0 | 0.748 [0.670, 0.826] | 115 | `results/raw_node30/t6_summac_conv.jsonl` |
| **NS** | SummaC-Conv | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_summac_conv.jsonl` |
| **QI** | SummaC-Conv | INV-claim all magnitudes | | C0 PASS | 0.020 [0.000, 0.059] | 51 | `results/raw_node30/t6_summac_conv.jsonl` |
| **QI** | SummaC-Conv | INV-unit natural | | C0 PASS | 0.022 [0.000, 0.065] | 46 | `results/raw_node30/t6_summac_conv.jsonl` |
| **US** | SummaC-Conv | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_summac_conv.jsonl` |
| **C0** | SummaC-ZS | C0 all | unconditional on C0 | 0.800 [0.730, 0.878] | 115 | `results/raw_node30/t6_summac_zs.jsonl` |
| **NS** | SummaC-ZS | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_summac_zs.jsonl` |
| **QI** | SummaC-ZS | INV-claim all magnitudes | | C0 PASS | 0.145 [0.073, 0.236] | 55 | `results/raw_node30/t6_summac_zs.jsonl` |
| **QI** | SummaC-ZS | INV-unit natural | | C0 PASS | 0.146 [0.042, 0.251] | 48 | `results/raw_node30/t6_summac_zs.jsonl` |
| **US** | SummaC-ZS | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw_node30/t6_summac_zs.jsonl` |
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
| **C0** | Bespoke-MiniCheck-7B | C0 all | unconditional on C0 | 1.000 [1.000, 1.000] | 115 | `results/raw/t6_bespoke_minicheck.jsonl` |
| **NS** | Bespoke-MiniCheck-7B | E1-evid (value perturb evidence) | | C0 PASS; rate = FAIL | NA | 0 | `results/raw/t6_bespoke_minicheck.jsonl` |
| **QI** | Bespoke-MiniCheck-7B | INV-claim all magnitudes | | C0 PASS | 0.791 [0.687, 0.881] | 67 | `results/raw/t6_bespoke_minicheck.jsonl` |
| **QI** | Bespoke-MiniCheck-7B | INV-unit natural | | C0 PASS | 0.804 [0.696, 0.911] | 56 | `results/raw/t6_bespoke_minicheck.jsonl` |
| **US** | Bespoke-MiniCheck-7B | E1-unit claim/evid | | C0 PASS; rate = FAIL | NA | 0 | `results/raw/t6_bespoke_minicheck.jsonl` |
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

