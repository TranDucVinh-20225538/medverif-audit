# Expand C0 regen (OpenRouter, 2026-09-29)

- **Generator:** `qwen/qwen-2.5-72b-instruct` (DeepInfra)  
- **Validator:** `microsoft/phi-4`  
- **Budget cap:** $2.00 — **spent $0.0023** (`data/expand/c0_regen/api_spend.jsonl`)

| Metric | Count |
| --- | ---: |
| Regenerated (1 attempt each) | 17 |
| Fixed (validator YES + audit clean) | 8 |
| Dropped (9 bases removed from `bases_main`) | 9 |

**Dropped base_ids:** D0010, D0018, D0019, D0025, D0083, D0141, D0213, D0219, D0292  

**Fixed base_ids:** D0023, D0029, D0097, D0192, D0204, D0237, D0308, D0375  

After rebuild: **351** main bases (DOSE **213**, POL **138**); valid main instances **2532**.

Spot-check: `qc/expand_dose_sample.csv` — **54** DOSE bases, seed **20260930**, columns `claim_c0`, `evidence_c0`, `e1_magnitude`, `e1_claim` (alternating ×2 / ×10).
