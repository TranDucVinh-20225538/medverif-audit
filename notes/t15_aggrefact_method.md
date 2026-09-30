# T15 AggreFact eval method (2026-09-30)

## CPU path (stopped)

- `t15_eval.py` base leg used **MiniCheck lib** `roberta-large` (`t6a_minicheck_roberta`) — ~13–20 rows/min on CPU.
- **Not** identical to `notes/t15_config.json` `base_checkpoint` (`lytang/MiniCheck-RoBERTa-Large`).

## GPU calibration (200 rows)

- **61537:** HF `lytang/MiniCheck-RoBERTa-Large`, bf16, batch 64 vs legacy CPU base scores → **69.5%** verdict agreement (expected — different base weights).
- See `notes/t15_aggrefact_gpu_calibration.json`.

## Production path (current)

- **GPU** `scripts/t15_aggrefact_gpu_eval.py` — transformers `AutoModelForSequenceClassification`, evidence+EOS+claim, threshold 0.5, batch 64, bf16.
- **Base:** `lytang/MiniCheck-RoBERTa-Large`
- **Ft:** `notes/t15_config.json` `best_checkpoint_dir`
- Verifiers: `t15_aggrefact_base_gpu`, `t15_aggrefact_ft_gpu`
- CPU partials archived under `results/raw/t15/_archive_cpu_minicheck_partial_*`

## Fallback (if GPU queue blocked >2h)

- `scripts/t15_aggrefact_subsample_eval.py` — stratified **n=3000**, seed 42, bootstrap CI in `notes/t15_report.md` (labeled subsample).
