#!/bin/bash
#SBATCH --job-name=rd2-GEN
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=06:00:00
#SBATCH --array=0-3%1
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/rd2-GEN_%A_%a.out
# (RD2-2) answers from the open generators, one model per task, vLLM 0.8.3, bf16, greedy, seed 42, the RD prompts
# (grounded + closed), 480 questions x 2 = 960 answers per model.  Tasks (rd2_generate.LOCAL_DEFAULT):
#   0 llama31_8b (16 GB)  1 qwen25_14b (30 GB)  2 medgemma_27b (54 GB)  3 baichuan_m2_32b (65.5 GB)
# One A100-80GB each (TP=1).  Default %1 = sequential (shared 4-GPU node); resumable (re-submit the same task).
# If a model does not fit: MEDVERIF_RD2_TP=2 with --gres=gpu:2.  Weights: results/journal3/models.json (offline).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal5/rd2_env.sh"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export MEDVERIF_RD2_GPU_UTIL="${MEDVERIF_RD2_GPU_UTIL:-0.92}" MEDVERIF_RD2_TP="${MEDVERIF_RD2_TP:-1}"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv 2>/dev/null || true
"${PY}" -c "import vllm; print('vllm', vllm.__version__)"
"${PY}" -u scripts/journal5/rd2_generate.py --backend vllm --array-index "${SLURM_ARRAY_TASK_ID}" --passes 3
