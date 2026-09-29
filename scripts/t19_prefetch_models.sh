#!/usr/bin/env bash
# Download T19 Llama weights on a login node (internet required). Compute jobs use HF_HUB_OFFLINE=1.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-0}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm

models=(
  meta-llama/Llama-3.2-1B-Instruct
  meta-llama/Llama-3.2-3B-Instruct
  meta-llama/Llama-3.1-8B-Instruct
)

if ! huggingface-cli whoami >/dev/null 2>&1; then
  echo "ERROR: huggingface-cli not logged in (HF_TOKEN or hf auth login)" >&2
  exit 1
fi

for m in "${models[@]}"; do
  echo "prefetch ${m} $(date -Is)"
  if ! huggingface-cli download "${m}" --resume-download; then
    echo "ERROR: download failed for ${m} — accept the model license on huggingface.co" >&2
    exit 1
  fi
  n=$(find "${HUGGINGFACE_HUB_CACHE}/models--$(echo "${m}" | tr '/' '--')" -name '*.safetensors' 2>/dev/null | wc -l)
  echo "prefetch ${m}: safetensors=${n}"
  need=1
  if [[ "${m}" == *"3B"* ]] || [[ "${m}" == *"8B"* ]]; then
    need=2
  fi
  if [[ "${n}" -lt "${need}" ]]; then
    echo "ERROR: need ${need} safetensors shards for ${m}, got ${n}" >&2
    exit 1
  fi
done
echo "prefetch done $(date -Is)"
