#!/usr/bin/env bash
# Shared Hugging Face cache for medverif (login-node OR jobs; avoids broken /hub paths).
medverif_hf_env() {
  local root="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
  export HF_HOME="${HF_HOME:-${root}/.cache/huggingface}"
  export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
  export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-${HF_HOME}/datasets}"
  export HF_HUB_DISABLE_TELEMETRY=1
  export TOKENIZERS_PARALLELISM=false
  if [[ -z "${HF_TOKEN:-}" && -r "${HOME}/.cache/huggingface/token" ]]; then
    export HF_TOKEN="$(cat "${HOME}/.cache/huggingface/token")"
  fi
}

# Enable HF offline mode only when weight shards for model_id are present in hub cache.
medverif_hf_offline_if_cached() {
  local model_id="${1:?model_id}"
  medverif_hf_env
  local hub="${HUGGINGFACE_HUB_CACHE}"
  local dir="${hub}/models--${model_id//\//--}"
  local n=0
  if [[ -d "${dir}/snapshots" ]]; then
    n="$(find "${dir}/snapshots" -name '*.safetensors' 2>/dev/null | wc -l | tr -d ' ')"
  fi
  local min_shards=2
  if [[ "${model_id}" == *8B* ]] || [[ "${model_id}" == *8b* ]]; then
    min_shards=4
  fi
  if [[ "${n}" -ge "${min_shards}" ]]; then
    export HF_HUB_OFFLINE=1
    export TRANSFORMERS_OFFLINE=1
    echo "hf_offline=1 cached_shards=${n} min=${min_shards} model=${model_id}"
  else
    unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
    echo "hf_offline=0 cached_shards=${n} model=${model_id} (online fetch allowed)"
  fi
}
