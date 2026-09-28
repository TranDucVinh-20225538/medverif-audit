#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock cpu_early

cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
LOG="${ROOT}/jobs/logs/cpu_v2a_v3_$(date +%Y%m%dT%H%M).log"
exec nice -n 19 python3 -u src/cpu_early.py >> "${LOG}" 2>&1
