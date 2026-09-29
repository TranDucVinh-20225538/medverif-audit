# main_ext funnel

- Textbook candidates → stage1: **1200**
- Stage1 unique bases (Qwen claim + Phi-4 YES + perturb + Phi-4 INV): **1100**
  - Claim/rule drops: span_not_unique_in_claim=10, span_missing_in_claim=1
  - Phi-4 claim validation drops: **98**
  - Perturb rule drops: **16**
  - Phi-4 INV drops: **0**
- Post-perturb **author_whitelist INV** bases: **122** (11.1% of stage1 bases)
- **bases_kept** in `data/main_ext/bases_main_ext.jsonl`: **60**
- Disjointness (stage1 bases vs main+T15): **pass**

Full counts: `notes/main_ext_funnel.json`
