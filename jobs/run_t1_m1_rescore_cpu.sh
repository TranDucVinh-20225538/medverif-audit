#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t1_m1_cpu

cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export CUDA_VISIBLE_DEVICES=""
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_M1=1
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export OMP_NUM_THREADS=4

LOG="${ROOT}/jobs/logs/t1_m1_cpu_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
python3 scripts/build_m1_pending_node30.py
python3 scripts/t1_score_pending_m1.py
python3 scripts/t1_cost_validity_report.py
echo "t1 m1 cpu done $(date -Is)"
