#!/bin/bash
#SBATCH --job-name=medverif-v4
#SBATCH --partition=defq
#SBATCH --exclude=node001,node002
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export VLLM_CACHE_ROOT="${ROOT}/.cache/vllm"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/gpu_graceful.sh"
source "${ROOT}/jobs/lib/stage_vllm_cache.sh"
gpu_graceful_init
export MEDVERIF_ROOT="${ROOT}"
stage_hf_snapshot "Qwen/Qwen3-14B" "40c069824f4251a91eefaf281ebe4c544efd3e18"

python src/split_cpu_early.py
mkdir -p results/raw results/raw_threshold

gpu_run python -u src/stage3_v4_run.py
echo "v4 stage3 done $(date -Is)"
