# QC — Gemini 2.5 Flash approved, author rejected

Gemini 2.5 Flash is the validator only for the G-INV paraphrase run (`notes/g_full_run_report.md`); the main pipeline validator is Phi-4 (`qc/qc_stats.md`). Author labels: `qc/inv_manual_review_PI_ok_labels.csv` (PI_ok). An item counts as Gemini-approved only if the reviewed rewrite matches a Gemini-passed attempt in `data/v3/para_attempts_g.jsonl`.

| condition | author rejected / Gemini-approved & labelled | reviewed text ≠ Gemini-passed text | no Gemini pass |
|---|---:|---:|---:|
| INV paraphrase · DOSE · llm | **17/40** | 0 | 0 |
| INV paraphrase · POLARITY · llm | **0/0** | 13 | 0 |
| INV paraphrase · POLARITY · template | **0/0** | 13 | 29 |

Pilot audit (`notes/g_inv_gemini_audit.json`): Gemini approved **2/4** author must-reject pairs.
