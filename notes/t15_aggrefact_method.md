# T15 AggreFact eval method (2026-09-30)

## Production path (MiniCheck library, GPU)

- **Do not** use raw `transformers` loading for AggreFact base or T15 ft — that path disagreed (~69.5%) with the CPU **MiniCheck library** checker and is not the paper’s MiniCheck-RoBERTa-L eval.
- **Base:** `MiniCheck(model_name='roberta-large')` → `lytang/MiniCheck-RoBERTa-Large`, chunk_size 400, EOS-join `[doc, claim]`, label index 1 = supported, threshold 0.5 (`minicheck@b58b9fa`, same commit as cpuverif).
- **Fine-tuned:** same library `Inferencer` path; weights loaded from `notes/t15_config.json` `best_checkpoint_dir` (patch replaces hub weights only).
- **GPU jobs:** `jobs/run_t15_aggrefact_gpu_cal.sbatch` (200-row cal vs CPU library scores), `run_t15_aggrefact_gpu_leg.sbatch` (`LEG=base|ft`). Script: `scripts/t15_aggrefact_gpu_eval.py`.
- **Card packs** (`main_dose`, T14, T18, `main_ext`): base via `t6a_minicheck_roberta`; ft via `t15_minicheck_roberta` (library wrapper in `src/verifiers/minicheck_roberta_lib.py`).

## Calibration gate

- Compare **200** test rows: GPU library base vs reference `results/raw/t15/_archive_cpu_minicheck_partial_20260930/base_aggrefact_test.jsonl` (`t6a_minicheck_roberta`).
- Require **≥97%** verdict agreement; report subset BAcc vs published reference (`notes/t15_aggrefact_gpu_calibration.json`, `PUBLISHED_AGGREFACT_BACC` in code).

## Training vs inference format

- T15 training (`scripts/t15_train.py`): `eos.join([evidence, claim])`, labels `SUPPORTED→1`, max_length 512, threshold 0.5 — matches MiniCheck `batch_tokenize` for RoBERTa (doc=evidence, claim=claim). **No retrain flag.**

## Fallback (GPU unavailable >2h)

- `scripts/t15_aggrefact_subsample_eval.py` — stratified **n=3000**, seed 42, bootstrap CI (`t15_aggrefact_subsample_report.py`).

## Archived

- Legacy CPU partials: `results/raw/t15/_archive_cpu_minicheck_partial_20260930/`
- HF GPU overwrite of `base_aggrefact_test.jsonl` (61537/61538): restore from archive before full GPU library rescoring if needed.
