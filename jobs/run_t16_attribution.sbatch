#!/bin/bash
#SBATCH --job-name=t16_attr
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=24:00:00
#SBATCH --exclude=node002,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t16_attribution-%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t16_attribution-%j.err

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t16_attribution

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MEDVERIF_T16_DEVICE=cpu

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

echo "t16 CPU fallback start $(date -Is) — prefer jobs/run_t16_attribution_gpu.sbatch"
python3 -u scripts/t16_attribution.py
echo "t16 attribution done $(date -Is)"
