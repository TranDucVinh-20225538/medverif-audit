#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock v4_openrouter_probe

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_V4_OPENROUTER_MODEL="${MEDVERIF_V4_OPENROUTER_MODEL:-qwen/qwen3-14b}"

LOG="${ROOT}/jobs/logs/v4_probe_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "v4 probe start $(date -Is)"
python3 scripts/v4_openrouter_probe.py
echo "v4 probe done $(date -Is)"
