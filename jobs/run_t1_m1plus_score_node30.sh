#!/usr/bin/env bash
# M1+ V2a/V3 on node30 → results/raw_m1plus/
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh 2>/dev/null || true
conda activate vllm 2>/dev/null || true
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES=""
export MEDVERIF_M1=0
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"

LOG="${ROOT}/jobs/logs/t1_m1plus_node30_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "m1plus node30 start $(date -Is)"
python3 scripts/build_m1plus_pending_node30.py
python3 scripts/build_score_pending.py
python3 scripts/t1_score_pending_m1plus.py
python3 scripts/t3_family_report.py
echo "m1plus node30 done $(date -Is)"
