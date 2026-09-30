# Autonomous run log

| Time (+07) | Job | Cause | Fix | Commit |
|------------|-----|-------|-----|--------|
| 01:00 | lane_c | Missing v6 modules | v6 wrappers + resume script | 7d8e919 |
| 01:15 | t19_8b | HF offline + incomplete cache | `medverif_hf_offline_if_cached` | f5e96af |
| 01:15 | t15_eval | AggreFact `doc`→evidence | normalize + dedupe jsonl | f5e96af |
| 01:16 | H7 | Registry assert vs gpt-4o v4 | `MEDVERIF_SKIP_OPENROUTER_REGISTRY_ASSERT` | 6cc584d |
| 30/9 AM | decision_M | SummaC-Conv/HHEM &lt;97% | excluded from new packs; decision-log M | (pending push) |
| 30/9 AM | lane_c_repair | `load_joined_from_records(..., verifier=)` | remove broken call in repair report | (pending push) |
| 30/9 AM | bespoke | missing `v2b_bespoke` | `src/verifiers/v2b_bespoke.py` + vllm sbatch | (pending push) |
| 30/9 AM | OR baseline | new day $10 cap | `lane_or_night_budget.py reset-baseline` | — |
| 30/9 AM | t15 | duplicate AggreFact lines | `jsonl_dedupe_instance.py` + resume eval | — |
| 30/9 AM | T20–T23 | — | gated on 6 prerequisites (`notes/t20_t23_gate.md`) | — |
