#!/bin/bash
#SBATCH --job-name=t14_small
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t14_small_%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t14_small_%j.err

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export NLTK_DATA="${ROOT}/.cache/nltk"
export PYTHONPATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts:${ROOT}/.cache/src/AlignScore/src"
export MEDVERIF_LEGACY_GPU=1
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
echo "t14 env agreement start $(date -Is) job=${SLURM_JOB_ID}"
python3 -u scripts/t14_env_agreement.py
echo "t14 small checkers start $(date -Is) job=${SLURM_JOB_ID}"
python3 -u scripts/t14_score_small_checkers.py
echo "t14 small checkers done $(date -Is)"
