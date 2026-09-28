#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock g_full_openrouter

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_G_PILOT_VERSION=v2
export MEDVERIF_PARA_GEN_PROVIDER="${MEDVERIF_PARA_GEN_PROVIDER:-DeepInfra}"
export MEDVERIF_PARA_VAL_PROVIDER="${MEDVERIF_PARA_VAL_PROVIDER:-}"
export MEDVERIF_PARA_VAL_MODEL="${MEDVERIF_PARA_VAL_MODEL:-google/gemini-2.5-flash}"
export MEDVERIF_G_RESUME=1
export MEDVERIF_G_SKIP_SANITY=1
export MEDVERIF_PARA_GEN_ALLOW_FALLBACKS=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-7}"
export MEDVERIF_G_WORKERS="${MEDVERIF_G_WORKERS:-1}"

LOG="${ROOT}/jobs/logs/g_full_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "g full start $(date -Is) resume=${MEDVERIF_G_RESUME}"
python3 src/inv_paraphrase_full_openrouter.py
echo "g full done $(date -Is)"
bash "${ROOT}/scripts/g_inv_post_finish.sh"
