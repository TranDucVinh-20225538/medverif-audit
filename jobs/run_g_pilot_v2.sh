#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock g_pilot_openrouter

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_G_PILOT_VERSION=v2
export MEDVERIF_PARA_GEN_PROVIDER="${MEDVERIF_PARA_GEN_PROVIDER:-DeepInfra}"
export MEDVERIF_PARA_VAL_PROVIDER="${MEDVERIF_PARA_VAL_PROVIDER:-DeepInfra}"

LOG="${ROOT}/jobs/logs/g_pilot_v2_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "g pilot v2 start $(date -Is)"
python3 src/inv_paraphrase_openrouter.py
echo "g pilot v2 done $(date -Is)"
