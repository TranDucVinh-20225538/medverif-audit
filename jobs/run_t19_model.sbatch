#!/bin/bash
#SBATCH --job-name=t19-ragas
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --time=08:00:00
#SBATCH --exclude=node004
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t19-%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/gpu_graceful.sh"
source "${ROOT}/jobs/lib/gpu_node_precheck.sh"

: "${MEDVERIF_T19_HF_MODEL:?set MEDVERIF_T19_HF_MODEL}"
: "${MEDVERIF_T19_SLUG:?set MEDVERIF_T19_SLUG}"
: "${MEDVERIF_T19_OUT:?set MEDVERIF_T19_OUT}"

medverif_acquire_lock "t19_${MEDVERIF_T19_SLUG}"

: "${MEDVERIF_REQ_MEM_GB:=48}"
export MEDVERIF_REQ_MEM_GB
medverif_gpu_node_precheck

source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_offline_if_cached "${MEDVERIF_T19_HF_MODEL}"
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0
export MEDVERIF_SCORE_FLUSH_EVERY="${MEDVERIF_SCORE_FLUSH_EVERY:-20}"
export MEDVERIF_SCORE_BATCH="${MEDVERIF_SCORE_BATCH:-4}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/job_elapsed.sh"
medverif_job_elapsed_begin \
  --pack "data/t19/instances_t19.jsonl" \
  --verifier "t19_ragas_local/${MEDVERIF_T19_SLUG}" \
  --machine "hpc"

gpu_graceful_init
INST="${ROOT}/${MEDVERIF_T19_INSTANCES:-data/t19/instances_t19.jsonl}"
OUT="${ROOT}/results/raw/t19/${MEDVERIF_T19_OUT}"
mkdir -p "$(dirname "${OUT}")"

echo "T19 score ${MEDVERIF_T19_SLUG} model=${MEDVERIF_T19_HF_MODEL} $(date -Is)"
gpu_run python3 -u scripts/t19_score_jsonl.py --instances "${INST}" --out "${OUT}"
echo "T19 done ${MEDVERIF_T19_SLUG} $(date -Is)"
medverif_job_elapsed_end --rows "$(wc -l < "${OUT}" 2>/dev/null || echo 0)"
