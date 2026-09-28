# Expansion status (expanded set)

Updated: 2026-09-29 02:38 +07

## StatPearls
- Pipeline stage: **chunked**
- Tar: `/data2/hpcshared/medverif-audit/.cache/statpearls/statpearls_NBK430685.tar.gz`
- Chunks: `/data2/hpcshared/medverif-audit/.cache/statpearls/chunk`

## Candidate counts (unused sentences vs v2)
- Pool DOSE: **6309**
- Pool POLARITY: **2580**
- Selected (cap 400/type): **800**
- Used v2 sentence keys excluded: 246

## Natural INV-unit (all DOSE main, rule-based)
- Valid unit INV instances: **68**
- Bases with unit INV: **68**

## Review packs
- `qc/expand_pol_flips.csv`
- `qc/expand_dose_sample.csv` (25% DOSE bases, seed 2026)
- `qc/expand_unit_natural.csv`

## Scoring
- Pending: `data/expand/instances_score_pending.jsonl` (after Stage-1 bases built)
- Budget guard: expansion API spend stop at **$30** (`notes/expand_budget.json`)
