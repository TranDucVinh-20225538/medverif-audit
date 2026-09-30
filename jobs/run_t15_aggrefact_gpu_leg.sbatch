#!/bin/bash
#SBATCH --job-name=t15_gpu
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t15_gpu_%x-%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t15_gpu_%x-%j.err

# Usage: sbatch --export=ALL,LEG=base|ft jobs/run_t15_aggrefact_gpu_leg.sbatch

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LEG="${LEG:?set LEG=base or ft}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src"
export MEDVERIF_T15_BATCH=64
export MEDVERIF_T15_BF16=1
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
export MEDVERIF_ROOT="${ROOT}"
bash "${ROOT}/jobs/lib/install_minicheck_gpu.sh"
export MEDVERIF_MINICHECK_BATCH=32
echo "t15 gpu leg=${LEG} start $(date -Is)"
python3 -u scripts/t15_aggrefact_gpu_eval.py --leg "${LEG}"
echo "t15 gpu leg=${LEG} done $(date -Is)"
