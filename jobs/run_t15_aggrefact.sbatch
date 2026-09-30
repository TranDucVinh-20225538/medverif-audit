#!/bin/bash
#SBATCH --job-name=t15_aggrefact
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --exclude=node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t15_aggrefact-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t15_aggrefact_eval

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export CUDA_VISIBLE_DEVICES=""

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

echo "t15 aggrefact-only start $(date -Is)"
python3 -u scripts/t15_eval.py --aggrefact-only --aggrefact-leg base
echo "t15 aggrefact-only done $(date -Is)"
