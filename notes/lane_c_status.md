# Lane C M1 H2 — raw_m1/lane_c reconciliation

Pack instances: `data/lane_c/m1_h2_main.jsonl` (**854** rows).

| Verifier | Lines | Status |
|----------|------:|--------|
| v1_medscore | 854 | complete |
| v1b_medscore | 854 | complete |
| v1c_medscore | 854 | complete |
| v4_ragas_nli | 854 | complete |
| v5_ragas_nli | 854 | complete |
| v6_ragas_gpt4o_mini | 0 | pending (import fixed) |
| v6_ragas_haiku45 | 0 | pending |
| v6_ragas_llama31_8b | 0 | pending |
| v6_ragas_mistral_small32 | 0 | pending |

Resume: `jobs/run_lane_c_m1_h2.sh` skips complete outputs; cap **$3** lane / **$10** night.
