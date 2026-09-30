#!/bin/bash
#SBATCH --job-name=t24b
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t24b_%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t24b_%j.err

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export NLTK_DATA="${ROOT}/.cache/nltk"
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
export MEDVERIF_T24B_OR_CAP_USD=1
export MEDVERIF_USE_OPENROUTER=1
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
python3 -u scripts/t24b_build_instances.py
python3 -u scripts/t24b_score_checkers.py
python3 -u scripts/t24b_report.py
echo "t24b done $(date -Is)"
