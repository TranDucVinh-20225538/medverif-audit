#!/bin/bash
#SBATCH --job-name=t15_gpu_cal
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --exclude=node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t15_gpu_cal-%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t15_gpu_cal-%j.err

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_T15_BATCH=64
export MEDVERIF_T15_BF16=1
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
python3 -u scripts/t15_aggrefact_gpu_eval.py --leg base --calibrate-only
