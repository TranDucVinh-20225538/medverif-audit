# T19 local Llama — HF gated models

Job **61439** hung ~40m with **0 GPU memory** and **0 score rows**: vLLM blocked on **missing local weights** (no `models--meta-llama--Llama-3.2-*` in `HF_HOME/hub`; compute nodes have no reliable Hub egress).

Prefetch on login node (`scripts/t19_prefetch_models.sh`) failed with:

`GatedRepoError: meta-llama/Llama-3.2-1B-Instruct` — account must accept the Meta Llama license on Hugging Face.

**Before resubmitting T19 Slurm jobs:**

1. Open each model page on HF and accept the license (same account as `huggingface-cli whoami`).
2. On a **login node**: `bash scripts/t19_prefetch_models.sh` (needs network).
3. Confirm safetensors exist under `.cache/huggingface/hub/models--meta-llama--Llama-3.2-1B-Instruct/`.
4. Submit with offline flags already set in `jobs/run_t19_model.sbatch` (`HF_HUB_OFFLINE=1`).

**Mitigations already in repo:** progress JSON lines every 20 rows, `flush` on each append, cancel + dependency chain via `jobs/run_t19_submit_chain.sh`.
