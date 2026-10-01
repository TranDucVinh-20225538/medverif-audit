# Journal chain status

API spend (sum of api_cost_usd under results/journal): **$0.4360** of $5.00 cap

Slurm jobs: `{"FINAL": "62064", "B4g": "62060", "B4": "62059", "B3": "62058", "B2": "62057", "B1": "62056", "A": "62055", "C1": "62061", "C2": "62062", "C3": "62063", "submitted": "2026-10-01T13:13:01+07:00"}`

| stage | status | info |
|---|---|---|
| A_threshold | done | `{"finished": "2026-10-01T13:15:37+0700", "slurm_job": "62055", "out_md": "/data2/hpcshared/medverif-audit/notes/threshold_robustness.md"}` |
| B1_questions | done | `{"finished": "2026-10-01T13:18:36+0700", "slurm_job": "62056", "valid_questions": 200, "candidates": 280, "chunks": 125847, "dose_sentences": 1541, "drop_t15_train_or_t24": 563, "drop_main_or_pack_sentence_hash": 17, "drop_main_or_pack_source_passage_id": 1, "eligible_after_filters": 960, "books": 1` |
| B2_retrieve | done | `{"finished": "2026-10-01T13:29:18+0700", "slurm_job": "62057", "n": 200, "gold_recall": {"bm25@3": 0.765, "dense@3": 0.58, "hybrid@3": 0.75}, "dense_model": "ncbi/MedCPT-Article-Encoder", "corpus_chunks": 125847}` |
| B3a_generate | done | `{"finished": "2026-10-01T13:33:36+0700", "slurm_job": "62058", "answers": 400, "expected": 400}` |
| B3b_instances | done | `{"finished": "2026-10-01T13:33:36+0700", "slurm_job": "62058", "answers": 400, "instances": 1622, "status_counts": {"unmatched": 9, "matched": 340, "skip_RAG-conv": 191, "RAG-value-x2": 340, "RAG-value-x10": 340, "RAG-unit-up": 252, "RAG-unit-down": 201, "RAG-conv": 149, "no_dose_in_answer": 51, "sk` |
| B4_judges | done | `{"finished": "2026-10-01T15:08:16+0700", "slurm_job": "62058", "judges": ["v4_ragas_nli", "v1_medscore"]}` |
| B4_small | done | `{"finished": "2026-10-01T18:27:38+0700", "slurm_job": "62059", "checkers": ["t6a_minicheck_roberta", "t6a_minicheck_deberta", "t6a_alignscore_base", "v2a_minicheck", "v3_alignscore"]}` |
| B4_bespoke | done | `{"finished": "2026-10-01T15:45:41+0700", "slurm_job": "62060"}` |
| C1_ft_data | done | `{"finished": "2026-10-01T13:13:55+0700", "slurm_job": "62061", "n_dose_train": 10508, "n_anli_in_t15_train": 10515, "n_dev": 2343, "dev_label_counts": {"SUPPORTED": 649, "UNSUPPORTED": 1694}}` |
| C2_train_alignscore_large_r0.5 | done | `{"finished": "2026-10-01T13:25:07+0700", "slurm_job": "62065", "best_dev_loss": 0.044286242573324475}` |
| C2_train_alignscore_large_r1 | done | `{"finished": "2026-10-01T13:43:58+0700", "slurm_job": "62066", "best_dev_loss": 0.03853050463268874}` |
| C2_train_alignscore_large_r2 | done | `{"finished": "2026-10-01T14:06:08+0700", "slurm_job": "62067", "best_dev_loss": 0.04726870277279617}` |
| C2_train_minicheck_ft5_r0.5 | done | `{"finished": "2026-10-01T14:41:15+0700", "slurm_job": "62068", "best_dev_loss": 0.08451601841037924}` |
| C2_train_minicheck_ft5_r1 | done | `{"finished": "2026-10-01T14:53:09+0700", "slurm_job": "62069", "best_dev_loss": 0.07489844805883372}` |
| C2_train_minicheck_ft5_r2 | done | `{"finished": "2026-10-01T15:53:22+0700", "slurm_job": "62062", "best_dev_loss": 0.07157821745209864}` |
| C3_eval_alignscore_large_base | done | `{"finished": "2026-10-01T16:00:34+0700", "slurm_job": "62092", "weights": "/data2/hpcshared/medverif-audit/.cache/huggingface/hub/models--yzha--AlignScore/snapshots/8509e78d25bb914939fc585c626500c9b2944249/AlignScore-large.ckpt", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggre` |
| C3_eval_alignscore_large_r0.5 | done | `{"finished": "2026-10-01T16:00:30+0700", "slurm_job": "62093", "weights": "/data2/hpcshared/medverif-audit/.cache/checkpoints/jr_alignscore_large_r0.5/best.ckpt", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggrefact": 3000}}` |
| C3_eval_alignscore_large_r1 | done | `{"finished": "2026-10-01T16:07:29+0700", "slurm_job": "62095", "weights": "/data2/hpcshared/medverif-audit/.cache/checkpoints/jr_alignscore_large_r1/best.ckpt", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggrefact": 3000}}` |
| C3_eval_alignscore_large_r2 | done | `{"finished": "2026-10-01T16:07:32+0700", "slurm_job": "62096", "weights": "/data2/hpcshared/medverif-audit/.cache/checkpoints/jr_alignscore_large_r2/best.ckpt", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggrefact": 3000}}` |
| C3_eval_minicheck_ft5_base | done | `{"finished": "2026-10-01T16:15:40+0700", "slurm_job": "62097", "weights": "lytang/MiniCheck-Flan-T5-Large (library default)", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggrefact": 3000}}` |
| C3_eval_minicheck_ft5_r0.5 | done | `{"finished": "2026-10-01T16:15:45+0700", "slurm_job": "62098", "weights": "/data2/hpcshared/medverif-audit/.cache/checkpoints/jr_minicheck_ft5_r0.5/best", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggrefact": 3000}}` |
| C3_eval_minicheck_ft5_r1 | done | `{"finished": "2026-10-01T16:23:51+0700", "slurm_job": "62099", "weights": "/data2/hpcshared/medverif-audit/.cache/checkpoints/jr_minicheck_ft5_r1/best", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggrefact": 3000}}` |
| C3_eval_minicheck_ft5_r2 | done | `{"finished": "2026-10-01T16:23:56+0700", "slurm_job": "62063", "weights": "/data2/hpcshared/medverif-audit/.cache/checkpoints/jr_minicheck_ft5_r2/best", "rows": {"main_dose": 996, "t7": 214, "t24b": 202, "rag": 1622, "aggrefact": 3000}}` |

Reports: `notes/threshold_robustness.md`, `notes/journal_rag_expansion.md`, `notes/journal_second_finetune.md`; human check: `qc/jr_rag_human_check.csv`.
