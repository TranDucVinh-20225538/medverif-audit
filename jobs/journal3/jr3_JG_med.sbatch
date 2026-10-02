#!/bin/bash
#SBATCH --job-name=jr3-JGmed
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=10:00:00
#SBATCH --array=8-9
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr3-JGmed_%A_%a.out
# (J3-JG, journal 4) medical open LLM judges through the chain-3 judge path (same prompt / parser / vLLM settings as
# jr3_JG.sbatch): 8 MedGemma-27B-text-it (~54 GB bf16), 9 Baichuan-M2-32B (Qwen2 arch, ~65.5 GB bf16), on the DOSE card (958)
# and the RD answers (1451).  One A100-80GB each (TP=1); 0.95 GPU memory leaves ~7-20 GB for the KV cache at max_model_len 8192.
# Set MEDVERIF_J3_TP=2 with --gres=gpu:2 if a model does not fit.  Weights: results/journal3/models.json (login-node download).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal3/jr3_env.sh"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export MEDVERIF_J3_PACKS="${MEDVERIF_J3_PACKS:-card,rd}" MEDVERIF_J3_GPU_UTIL="${MEDVERIF_J3_GPU_UTIL:-0.95}" MEDVERIF_J3_TP="${MEDVERIF_J3_TP:-1}"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv 2>/dev/null || true
"${PY}" -c "import vllm; print('vllm', vllm.__version__)" 2>/dev/null || echo "vllm not importable -> HF transformers fallback"
"${PY}" -u scripts/journal3/j3_judge_score.py --array-index "${SLURM_ARRAY_TASK_ID}" --backend vllm
