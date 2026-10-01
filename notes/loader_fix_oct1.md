# Oct 1 fixes after job 62017: AggreFact metric, MiniCheck cpuverif loader order, MedScore fallback copy

Full number diff (HEAD d509343 → this commit): `results/diagnostics/loader_fix_oct1/pn_diff_head_to_final.txt`.
Stage snapshots: `pn_head.json` → `pn_loader.json` (fixes 1+2) → `pn_final.json` (fix 3).

## 1. AggreFact metric (P0)

`bal_acc()` in `scripts/t15_aggrefact_report.py` returned plain accuracy (the same bug was in
`t15_aggrefact_subsample_report.py` and `t15_aggrefact_gpu_eval.py`; neither feeds a paper number). All three now compute
BAcc = (TPR + TNR) / 2; the paper metric is the unweighted mean over the 11 LLM-AggreFact datasets
(`t15_card_report.aggrefact_bacc`).

| leg | LLM-AggreFact BAcc (macro) | micro BAcc | accuracy (old "balanced acc") |
|---|---:|---:|---:|
| base | 0.7351 | 0.7632 | 0.7263 |
| ft | 0.7180 | 0.7292 | 0.7297 |

Per-dataset BAcc: `notes/t15_report.md` (AggreFact section) and the per-dataset rows in `paper_numbers_final.md`.
The T15 main-DOSE card is unchanged.

## 2. MiniCheck before-scores: prefer cpuverif (reference env)

`canonical_scores.reference_env_rows(path)` replaces each row of a MiniCheck score file (RoBERTa, DeBERTa, Flan-T5) from
the main / t7 / t3 / t4_eco / t4c_eco groups with its cpuverif rescore in `results/raw/minicheck_cpuverif`. The overlay is
per source file, so after-M1 packs, which reuse instance ids with different text, are untouched. `raw_m1` is excluded:
its cpuverif group was rebuilt with the current M1 enrichment, so those are not the same texts (T1 is superseded).
The loaders using it are `m1_strong_run`, `t13_best_of_n_report` (main card, T13, T14, T17-NS, Figure 1),
`m1_e1_unit_repair_report`, `t3_family_report` and `t7_e1_unit_report`. `paper_numbers_final` attributes those rows to
env cpuverif.

The only verdict flip across all mapped files is one RoBERTa row in `results/raw/t7` (the 1/230 disagreement already
in the agreement log). DeBERTa was already swapped in place, and the main-group files are score-identical.

| number | before | after |
|---|---|---|
| M1-strong amend5, RoBERTa CLAIM US_up_before | 33.3% (32/96) | 32.3% (31/96) |
| M1-strong amend5, RoBERTa CLAIM b/c, p | 59/1, 1.86e-13 | 60/1, 1.12e-13 (bind True, unchanged) |
| Main card, RoBERTa us_claim_up | 33.3% [25.0, 42.7] | 32.3% [24.0, 41.7] |
| Figure 1, RoBERTa us_claim_up | 33.3% | 32.3% |
| T13, RoBERTa P(wrong≥correct) evid_x1000_vs_c0 | 4.7% [0.9, 9.3] | 5.6% [1.9, 10.3] (continuous score change on the same row) |

## 3. MedScore: the 5 rows without API metadata are also excluded from the fallback copy

Job 62017 removed the 5 rows from `results/raw/v1_medscore.jsonl`, but loaders also read
`results/raw_node30/v1_medscore.jsonl`, which holds the same 5 ids (same verdicts, no API metadata), so the
exclusion had no effect ("medscore_changes 0" in `notes/env_cleanup_oct1.md`). They were moved to
`results/raw_node30/v1_medscore.no_api_meta.quarantined.jsonl` (shrink allowlisted). The `raw_m1` copies of these ids
have full API metadata and score M1-applied texts, so they stay.

Changed MedScore cells: main card c0 n 110→109, qi_all 67.7%→68.9% (n 62→61), ns 95.3%→95.2% (n 211→209),
us_evid_up 59.8%→60.4% (n 107→106); M1-strong UP EVID before 59.8%→60.4%, after 92.5% (99/107 → 98/106), b/c 36/1→35/1;
DOWN EVID before 93.3%→94.6%, after 96.0%→95.9%, b/c 3/1→2/1; NS_x10_evid 93.2%→93.1%; T13 evid_x1000_vs_c0
20.1%→19.8%; T14 n only. No M1 bind changes.

## Status

`paper_numbers_final.md`: 640 numbers. Reference 520, checked 131, node30-only 10 (decision M), n/a (human labels) 5,
**UNCHECKED 0**.
