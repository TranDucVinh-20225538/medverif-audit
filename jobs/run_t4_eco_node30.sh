#!/usr/bin/env bash
# node30: V2a + V3 + T6-A (7 checkers) on eco_instances → results/raw/t4_eco/
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_ROOT="${ROOT}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
export NLTK_DATA="${NLTK_DATA:-${ROOT}/.cache/nltk}"
LOG="${ROOT}/jobs/logs/t4_eco_node30_$(date +%Y%m%dT%H%M).log"
mkdir -p "${ROOT}/jobs/logs"
exec >>"${LOG}" 2>&1
echo "t4 eco node30 start $(date -Is) ROOT=${ROOT}"
python3 scripts/t4_eco_score_node30.py
echo "t4 eco node30 done $(date -Is)"
