# T3 encoder families (PI_ok=Y, valid)

- Label ids (freq/route): **36**; instances in pack: **35**
- Scores resolved per verifier from pack-specific paths (see JSON `score_paths`).

| Verifier | Family | PASS | n |
|---|---|---:|---:|
| v2a_minicheck | inv_frequency | 9 | 14 |
| v2a_minicheck | inv_route | 20 | 20 |
| v3_alignscore | inv_frequency | 10 | 14 |
| v3_alignscore | inv_route | 19 | 21 |
| v1b_medscore | inv_frequency | 14 | 14 |
| v1b_medscore | inv_route | 21 | 21 |
| v5_ragas_nli | inv_frequency | 14 | 14 |
| v5_ragas_nli | inv_route | 21 | 21 |
| v1_medscore | inv_frequency | 14 | 14 |
| v1_medscore | inv_route | 21 | 21 |
| v4_ragas_nli | inv_frequency | 13 | 14 |
| v4_ragas_nli | inv_route | 21 | 21 |
| v1c_medscore | inv_frequency | 14 | 14 |
| v1c_medscore | inv_route | 21 | 21 |
| v6_ragas_gpt4o_mini | inv_frequency | 10 | 14 |
| v6_ragas_gpt4o_mini | inv_route | 21 | 21 |
| v6_ragas_haiku45 | inv_frequency | 13 | 14 |
| v6_ragas_haiku45 | inv_route | 20 | 20 |
| v6_ragas_llama31_8b | inv_frequency | 10 | 13 |
| v6_ragas_llama31_8b | inv_route | 20 | 21 |
| v6_ragas_mistral_small32 | inv_frequency | 14 | 14 |
| v6_ragas_mistral_small32 | inv_route | 21 | 21 |
| v6_ragas_nli | inv_frequency | 0 | 0 |
| v6_ragas_nli | inv_route | 0 | 0 |
| v2b_bespoke | inv_frequency | 0 | 0 |
| v2b_bespoke | inv_route | 0 | 0 |
| t6a_minicheck_roberta | inv_frequency | 4 | 14 |
| t6a_minicheck_roberta | inv_route | 13 | 19 |
| t6a_minicheck_deberta | inv_frequency | 2 | 14 |
| t6a_minicheck_deberta | inv_route | 10 | 18 |
| t6a_alignscore_base | inv_frequency | 6 | 14 |
| t6a_alignscore_base | inv_route | 18 | 20 |
| t6a_summac_zs | inv_frequency | 8 | 12 |
| t6a_summac_zs | inv_route | 15 | 16 |
| t6a_summac_conv | inv_frequency | 3 | 10 |
| t6a_summac_conv | inv_route | 8 | 13 |
| t6a_hhem | inv_frequency | 9 | 14 |
| t6a_hhem | inv_route | 15 | 20 |
| t6a_granite_guardian | inv_frequency | 13 | 14 |
| t6a_granite_guardian | inv_route | 21 | 21 |

## Score path hints

- **t6a_alignscore_base**: `results/raw/t3/t6_alignscore_base.jsonl, results/raw/e2_main/t6_alignscore_base.jsonl, results/raw/t7/t6_alignscore_base.jsonl`
- **t6a_granite_guardian**: `results/raw/t3/t6_granite_guardian.jsonl, results/raw/e2_main/t6_granite_guardian.jsonl, results/raw/t7/t6_granite_guardian.jsonl`
- **t6a_hhem**: `results/raw/t3/t6_hhem.jsonl, results/raw/e2_main/t6_hhem.jsonl, results/raw/t7/t6_hhem.jsonl`
- **t6a_minicheck_deberta**: `results/raw/t3/t6_minicheck_deberta.jsonl, results/raw/e2_main/t6_minicheck_deberta.jsonl, results/raw/t7/t6_minicheck_deberta.jsonl`
- **t6a_minicheck_roberta**: `results/raw/t3/t6_minicheck_roberta.jsonl, results/raw/e2_main/t6_minicheck_roberta.jsonl, results/raw/t7/t6_minicheck_roberta.jsonl`
- **t6a_summac_conv**: `results/raw/t3/t6_summac_conv.jsonl, results/raw/e2_main/t6_summac_conv.jsonl, results/raw/t7/t6_summac_conv.jsonl`
- **t6a_summac_zs**: `results/raw/t3/t6_summac_zs.jsonl, results/raw/e2_main/t6_summac_zs.jsonl, results/raw/t7/t6_summac_zs.jsonl`
- **v1_medscore**: `results/raw/t3/v1_medscore.jsonl, results/raw/v1_medscore.jsonl`
- **v1b_medscore**: `results/raw/t3_t2/v1b_medscore.jsonl`
- **v1c_medscore**: `results/raw/t3_t6b/v1c_medscore.jsonl, results/raw/t6b/full/v1c_medscore.jsonl, results/raw/e2_main/v1c_medscore.jsonl, results/raw/t4_eco/v1c_medscore.jsonl`
- **v2a_minicheck**: `results/raw/t3/v2a_minicheck.jsonl, results/raw/v2a_minicheck.jsonl`
- **v2b_bespoke**: `results/raw/t6_bespoke_minicheck.jsonl`
- **v3_alignscore**: `results/raw/t3/v3_alignscore.jsonl, results/raw/v3_alignscore.jsonl`
- **v4_ragas_nli**: `results/raw/t3/v4_ragas_nli.jsonl, results/raw/e2_main/v4_ragas_nli.llama.jsonl, results/raw/t4_eco/v4_ragas_nli.llama.jsonl, results/raw/t4c_eco/v4_ragas_nli.llama.jsonl, results/raw/v4_ragas_nli.llama.jsonl`
- **v5_ragas_nli**: `results/raw/t3_t2/v5_ragas_nli.jsonl`
- **v6_ragas_gpt4o_mini**: `results/raw/t3_t6b/v6_ragas_gpt4o_mini.jsonl, results/raw/t6b/full/v6_ragas_gpt4o_mini.jsonl, results/raw/e2_main/v6_ragas_gpt4o_mini.jsonl`
- **v6_ragas_haiku45**: `results/raw/t3_t6b/v6_ragas_haiku45.jsonl, results/raw/t6b/full/v6_ragas_haiku45.jsonl, results/raw/e2_main/v6_ragas_haiku45.jsonl`
- **v6_ragas_llama31_8b**: `results/raw/t3_t6b/v6_ragas_llama31_8b.jsonl, results/raw/t6b/full/v6_ragas_llama31_8b.jsonl, results/raw/e2_main/v6_ragas_llama31_8b.jsonl`
- **v6_ragas_mistral_small32**: `results/raw/t3_t6b/v6_ragas_mistral_small32.jsonl, results/raw/t6b/full/v6_ragas_mistral_small32.jsonl, results/raw/e2_main/v6_ragas_mistral_small32.jsonl`
- **v6_ragas_nli**: `results/raw/t4_eco/v6_ragas_nli.jsonl, results/raw/t4c_eco/v6_ragas_nli.jsonl`
