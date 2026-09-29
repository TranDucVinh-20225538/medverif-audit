#!/bin/bash
#SBATCH --job-name=t19-ragas
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --time=08:00:00
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t19-%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/gpu_graceful.sh"

: "${MEDVERIF_T19_HF_MODEL:?set MEDVERIF_T19_HF_MODEL}"
: "${MEDVERIF_T19_SLUG:?set MEDVERIF_T19_SLUG}"
: "${MEDVERIF_T19_OUT:?set MEDVERIF_T19_OUT}"

medverif_acquire_lock "t19_${MEDVERIF_T19_SLUG}"

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm

gpu_graceful_init
INST="${ROOT}/data/t19/instances_t19.jsonl"
OUT="${ROOT}/results/raw/t19/${MEDVERIF_T19_OUT}"
mkdir -p "$(dirname "${OUT}")"

echo "T19 score ${MEDVERIF_T19_SLUG} model=${MEDVERIF_T19_HF_MODEL} $(date -Is)"
gpu_run python3 -u scripts/t19_score_jsonl.py --instances "${INST}" --out "${OUT}"
echo "T19 done ${MEDVERIF_T19_SLUG} $(date -Is)"
