# Ops status (2026-09-29 ~00:35 UTC+7)

## T2 full (approved)

- `notes/t2_full_approved` present.
- tmux **`t2_full`**: V1b `openai/gpt-4o` → `results/raw/t2_full/v1b_medscore.jsonl`, then V5 `anthropic/claude-sonnet-4.6`.
- Scope **533** instances (~**$6.4** projected from pilot).
- **`t3_watch`**: scores T3 INV families when `data/t3/instances_inv_families.jsonl` is non-empty (currently **0**).

## V1 / V4 main (OpenRouter)

- **V1** `results/raw/v1_medscore.jsonl`: check `wc -l` vs ~1085 valid main target.
- **V4** `results/raw/v4_ragas_nli.jsonl`: in progress (`v4_full` tmux).
- Credit: see `notes/openrouter_credit.json` (`scripts/openrouter_budget.py`).

## T6-B zoo (pilot)

- Models pinned in `notes/t6_models.json` (no Gemini/Qwen).
- Pilot **20** × **5** judges → tmux **`t6b_pilot`**, cap **$10**, inflight **1**.
- Report: `notes/t6b_pilot_report.md` when pilot finishes.

## T6-D / node30

- Scope: **`data/v3/instances_t6_scope.jsonl`** (533 rows, `content_sha1` on claim+evidence).
- Manifest: `data/v3/manifest_t6_scope.json`.
- Analysis: `scripts/t6d_analysis.py` → `results/tables/t6d_cost_validity.md`, `results/figures/t6d/`.

## T1 (M1)

- tmux **`t1_m1_or`** (HPC): M1 V1/V4 → `results/raw_m1/`; **node30**: `run_t1_m1_score_node30.sh` for V2/V3 M1.
- Table: `results/tables/cost_vs_validity.md`.
