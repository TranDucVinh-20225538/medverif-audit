#!/bin/bash
#SBATCH --job-name=jr3-JG
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --array=0-6%3
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr3-JG_%A_%a.out
# (J3-JG) one small local LLM judge per array task (vLLM bf16, RAGAS-NLI prompt, temperature 0) on the frozen DOSE
# card (958), the journal RAG pack (1622) and the RD answers (1451).  Tasks (j3_models.JUDGES): 0 Qwen2.5-7B,
# 1 Llama-3.1-8B, 2 MedGemma-4B-it, 3 Qwen2.5-0.5B, 4 Qwen2.5-1.5B, 5 Qwen2.5-3B, 6 Qwen2.5-14B, (7 Qwen2.5-32B opt-in).
# Weights were downloaded on the login node (results/journal3/models.json, pinned revision); gated/unavailable models
# mark themselves skipped and exit 0.  Resumable by instance_id.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal3/jr3_env.sh"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv 2>/dev/null || true
"${PY}" -c "import vllm; print('vllm', vllm.__version__)" 2>/dev/null || echo "vllm not importable -> HF transformers fallback"
"${PY}" -u scripts/journal3/j3_judge_score.py --array-index "${SLURM_ARRAY_TASK_ID}"
