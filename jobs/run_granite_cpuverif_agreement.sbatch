#!/bin/bash
#SBATCH --job-name=granite_agree
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/granite_agree_%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/granite_agree_%j.err

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
echo "granite cpuverif agreement start $(date -Is) job=${SLURM_JOB_ID}"
python3 -u scripts/granite_cpuverif_agreement.py
echo "granite agreement done $(date -Is)"
