# Audit snapshot

Built: 2026-09-29T13:09:26.085351+00:00

Recompute paper numbers:

```bash
python scripts/compute_paper_numbers.py
```

## Instance packs

- `data/v3/instances_main.jsonl` — columns: instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …
- `data/v3/instances_cpu_early.jsonl` — columns: instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …
- `data/v3/instances_inv_families.jsonl` — columns: instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …
- `data/v3/t17_downdose.jsonl` — columns: instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …
- `data/t7/instances_e1_unit.jsonl` — columns: instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …
- `data/t14/instances_t14.jsonl` — columns: instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …
- `data/t3/instances_inv_families.jsonl` — columns: instance_id, base_id, type, condition, magnitude, claim, evidence, valid, invalid_reason, subset, …

## QC / exclusions

- `qc/e1_pol_review.csv`
- `qc/inv_manual_review.csv`
- `qc/unit_naturalness.csv`
- `qc/dose3_labels.csv`
- `qc/t7_PI_ok_labels.csv`
- `qc/t14_PI_ok_labels.csv`
- `notes/allow_data_shrink.json`
- `notes/openrouter_verifiers.json`
- `src/non_dose_targets.py`
- `scripts/compute_paper_numbers.py`

## Score files included (HPC / master `results/raw/`)

- `results/raw/v2a_minicheck.jsonl`
- `results/raw/v3_alignscore.jsonl`
- `results/raw/v1_medscore.jsonl`
- `results/raw/v4_ragas_nli.llama.jsonl`
- `results/raw/e2_main/t6_alignscore_base.jsonl`
- `results/raw/e2_main/t6_bespoke_minicheck.jsonl`
- `results/raw/e2_main/t6_granite_guardian.jsonl`
- `results/raw/e2_main/t6_hhem.jsonl`
- `results/raw/e2_main/t6_minicheck_deberta.jsonl`
- `results/raw/e2_main/t6_minicheck_roberta.jsonl`
- `results/raw/e2_main/t6_summac_conv.jsonl`
- `results/raw/e2_main/t6_summac_zs.jsonl`
- `results/raw/e2_main/v2a_minicheck.jsonl`
- `results/raw/e2_main/v3_alignscore.jsonl`
- `results/raw/t7/t6_alignscore_base.jsonl`
- `results/raw/t7/t6_bespoke_minicheck.jsonl`
- `results/raw/t7/t6_granite_guardian.jsonl`
- `results/raw/t7/t6_hhem.jsonl`
- `results/raw/t7/t6_minicheck_deberta.jsonl`
- `results/raw/t7/t6_minicheck_roberta.jsonl`
- `results/raw/t7/t6_summac_conv.jsonl`
- `results/raw/t7/t6_summac_zs.jsonl`
- `results/raw/t7/v1_medscore.jsonl`
- `results/raw/t7/v1b_medscore.jsonl`
- `results/raw/t7/v1c_medscore.jsonl`
- `results/raw/t7/v2a_minicheck.jsonl`
- `results/raw/t7/v3_alignscore.jsonl`
- `results/raw/t7/v4_ragas_nli.legacy.jsonl`
- `results/raw/t7/v4_ragas_nli.llama.jsonl`
- `results/raw/t7/v5_ragas_nli.jsonl`
- `results/raw/t7/v6_ragas_gpt4o_mini.jsonl`
- `results/raw/t7/v6_ragas_haiku45.jsonl`
- `results/raw/t7/v6_ragas_llama31_8b.jsonl`
- `results/raw/t7/v6_ragas_mistral_small32.jsonl`
- `results/raw/t14/v1_medscore.jsonl`
- `results/raw/t14/v1b_medscore.jsonl`
- `results/raw/t14/v5_ragas_nli.jsonl`
- `results/raw/t17/v1_medscore.jsonl`
- `results/raw/t17/v1b_medscore.jsonl`
- `results/raw/t17/v5_ragas_nli.jsonl`
- `results/raw/t3/t6_alignscore_base.jsonl`
- `results/raw/t3/t6_granite_guardian.jsonl`
- `results/raw/t3/t6_hhem.jsonl`
- `results/raw/t3/t6_minicheck_deberta.jsonl`
- `results/raw/t3/t6_minicheck_roberta.jsonl`
- `results/raw/t3/t6_summac_conv.jsonl`
- `results/raw/t3/t6_summac_zs.jsonl`
- `results/raw/t3/v1_medscore.jsonl`
- `results/raw/t3/v2a_minicheck.jsonl`
- `results/raw/t3/v3_alignscore.jsonl`
- `results/raw/t3_t2/v1b_medscore.jsonl`
- `results/raw/t3_t2/v5_ragas_nli.jsonl`
- `results/raw/t3_t6b/v1c_medscore.jsonl`
- `results/raw/t3_t6b/v6_ragas_gpt4o_mini.jsonl`
- `results/raw/t3_t6b/v6_ragas_haiku45.jsonl`
- `results/raw/t3_t6b/v6_ragas_llama31_8b.jsonl`
- `results/raw/t3_t6b/v6_ragas_mistral_small32.jsonl`
- `results/raw_m1/v1_medscore.jsonl`
- `results/raw_m1/v4_ragas_nli.llama.jsonl`
- `results/raw_m1/v2a_minicheck.jsonl`
- `results/raw_m1/v3_alignscore.jsonl`

## Node30 CPU scores (`env=node30`)

Under `results/raw_node30/` — sourced from `node30-results` at `c48093bdc73a6b11161a26a2b11124a0e2ba5612` (MiniCheck, AlignScore, SummaC, HHEM, Granite, Bespoke, V2/V3, T9 NeMo). Not merged into `results/raw/` on master.

- `results/raw_node30/e2_main/t6_alignscore_base.jsonl`
- `results/raw_node30/e2_main/t6_bespoke_minicheck.jsonl`
- `results/raw_node30/e2_main/t6_granite_guardian.jsonl`
- `results/raw_node30/e2_main/t6_hhem.jsonl`
- `results/raw_node30/e2_main/t6_minicheck_deberta.jsonl`
- `results/raw_node30/e2_main/t6_minicheck_roberta.jsonl`
- `results/raw_node30/e2_main/t6_summac_conv.jsonl`
- `results/raw_node30/e2_main/t6_summac_zs.jsonl`
- `results/raw_node30/e2_main/v2a_minicheck.jsonl`
- `results/raw_node30/e2_main/v3_alignscore.jsonl`
- `results/raw_node30/t3/t6_alignscore_base.jsonl`
- `results/raw_node30/t3/t6_bespoke_minicheck.jsonl`
- `results/raw_node30/t3/t6_granite_guardian.jsonl`
- `results/raw_node30/t3/t6_hhem.jsonl`
- `results/raw_node30/t3/t6_minicheck_deberta.jsonl`
- `results/raw_node30/t3/t6_minicheck_roberta.jsonl`
- `results/raw_node30/t3/t6_summac_conv.jsonl`
- `results/raw_node30/t3/t6_summac_zs.jsonl`
- `results/raw_node30/t3/v2a_minicheck.jsonl`
- `results/raw_node30/t3/v3_alignscore.jsonl`
- `results/raw_node30/t4_eco/t6_alignscore_base.jsonl`
- `results/raw_node30/t4_eco/t6_granite_guardian.jsonl`
- `results/raw_node30/t4_eco/t6_hhem.jsonl`
- `results/raw_node30/t4_eco/t6_minicheck_deberta.jsonl`
- `results/raw_node30/t4_eco/t6_minicheck_roberta.jsonl`
- `results/raw_node30/t4_eco/t6_summac_conv.jsonl`
- `results/raw_node30/t4_eco/t6_summac_zs.jsonl`
- `results/raw_node30/t4_eco/v2a_minicheck.jsonl`
- `results/raw_node30/t4_eco/v3_alignscore.jsonl`
- `results/raw_node30/t4c_eco/t6_alignscore_base.jsonl`
- `results/raw_node30/t4c_eco/t6_bespoke_minicheck.jsonl`
- `results/raw_node30/t4c_eco/t6_granite_guardian.jsonl`
- `results/raw_node30/t4c_eco/t6_hhem.jsonl`
- `results/raw_node30/t4c_eco/t6_minicheck_deberta.jsonl`
- `results/raw_node30/t4c_eco/t6_minicheck_roberta.jsonl`
- `results/raw_node30/t4c_eco/t6_summac_conv.jsonl`
- `results/raw_node30/t4c_eco/t6_summac_zs.jsonl`
- `results/raw_node30/t4c_eco/v2a_minicheck.jsonl`
- `results/raw_node30/t4c_eco/v3_alignscore.jsonl`
- `results/raw_node30/t6_alignscore_base.jsonl`
- `results/raw_node30/t6_bespoke_minicheck.jsonl`
- `results/raw_node30/t6_granite_guardian.jsonl`
- `results/raw_node30/t6_hhem.jsonl`
- `results/raw_node30/t6_minicheck_deberta.jsonl`
- `results/raw_node30/t6_minicheck_roberta.jsonl`
- `results/raw_node30/t6_summac_conv.jsonl`
- `results/raw_node30/t6_summac_zs.jsonl`
- `results/raw_node30/t7/t6_alignscore_base.jsonl`
- `results/raw_node30/t7/t6_bespoke_minicheck.jsonl`
- `results/raw_node30/t7/t6_granite_guardian.jsonl`
- `results/raw_node30/t7/t6_hhem.jsonl`
- `results/raw_node30/t7/t6_minicheck_deberta.jsonl`
- `results/raw_node30/t7/t6_minicheck_roberta.jsonl`
- `results/raw_node30/t7/t6_summac_conv.jsonl`
- `results/raw_node30/t7/t6_summac_zs.jsonl`
- `results/raw_node30/t7/v2a_minicheck.jsonl`
- `results/raw_node30/t7/v3_alignscore.jsonl`
- `results/raw_node30/t9/alignscore_rail.jsonl`
- `results/raw_node30/t9/alignscore_rail.legacy_536.jsonl`
- `results/raw_node30/t9/alignscore_rail_large.jsonl`
- `results/raw_node30/v1_medscore.jsonl`
- `results/raw_node30/v2a_minicheck.jsonl`
- `results/raw_node30/v3_alignscore.jsonl`
- `results/raw_node30/v4_ragas_nli.jsonl`

## Manifest

- `release/score_manifest.tsv` — one row per score file: verifier, pack, row count, source branch/commit.
- `release/canonical_sources.tsv` — authoritative (verifier, pack) → score_path for `compute_paper_numbers.py`.

## Excluded by policy

- `results/raw/**/v4_ragas_nli.jsonl` (non-Llama / Qwen local on HPC tree only)
- `**/_quarantine/**`, secrets, `.env`

