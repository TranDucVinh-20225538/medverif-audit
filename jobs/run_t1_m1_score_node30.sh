#!/usr/bin/env bash
# T1-M1 V2a/V3 on node30 only → results/raw_m1/ (not for HPC cluster login nodes).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh 2>/dev/null || true
conda activate vllm 2>/dev/null || true
export CUDA_VISIBLE_DEVICES=""
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_M1="${MEDVERIF_M1:-1}"
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

LOG="${ROOT}/jobs/logs/t1_m1_node30_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t1 m1 node30 V2/V3 start $(date -Is)"
python3 scripts/build_m1_pending_node30.py
python3 scripts/t1_score_pending_m1.py
echo "t1 m1 node30 V2/V3 done $(date -Is)"
