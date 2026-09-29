# main_ext cohort (scoring scope)

- **Stage1 expansion bases** (Qwen/Phi pipeline artifact, not the main_ext pack): **1100**
- **main_ext bases** (`data/main_ext/bases_main_ext.jsonl`): **60**
- **Bases with a valid author_whitelist INV-unit row** (main_ext scoring cohort): **60**
- **INV-unit instance rows** in review CSV: **60**

Only rows in `data/main_ext/instances_main_ext.jsonl` (subset=`main_ext`) are scored as main_ext.
Stage1 `validator_raw.jsonl` / 892-base counts are expand funnel diagnostics only.

Review file: `qc/main_ext_review.csv`

