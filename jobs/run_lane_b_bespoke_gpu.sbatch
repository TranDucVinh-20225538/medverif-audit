#!/bin/bash
#SBATCH --job-name=lane_b_bespoke
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=04:00:00
#SBATCH --exclude=node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/lane_b_bespoke-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/gpu_graceful.sh"
medverif_acquire_lock lane_b_bespoke_gpu
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=1
export HF_HOME="${ROOT}/.cache/huggingface"
gpu_graceful_init
bash jobs/run_lane_b_bespoke_gpu.sh
