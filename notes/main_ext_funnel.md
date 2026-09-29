# main_ext funnel

- Textbook candidates → stage1: **200**
- Stage1 unique bases (Qwen claim + Phi-4 YES + perturb + Phi-4 INV): **208**
  - Claim/rule drops: span_not_unique_in_claim=2
  - Phi-4 claim validation drops: **12**
  - Perturb rule drops: **3**
  - Phi-4 INV drops: **0**
- Post-perturb **author_whitelist INV** bases: **16** (7.7% of stage1 bases)
- **bases_kept** in `data/main_ext/bases_main_ext.jsonl`: **16**
- Disjointness (stage1 bases vs main+T15): **pass**

Full counts: `notes/main_ext_funnel.json`
