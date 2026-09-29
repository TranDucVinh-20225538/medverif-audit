#!/usr/bin/env bash
# Tokenizers for OpenRouter scoring (T17/T14); weights stay on OR.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
# shellcheck source=/dev/null
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-0}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm

huggingface-cli whoami >/dev/null

# V1 / V1b chat template
huggingface-cli download mistralai/Mistral-Small-24B-Instruct-2501 \
  --revision 9527884be6e5616bdd54de542f9ae13384489724 \
  tokenizer.json tokenizer_config.json special_tokens_map.json tokenizer.model 2>/dev/null || \
huggingface-cli download mistralai/Mistral-Small-24B-Instruct-2501 \
  --revision 9527884be6e5616bdd54de542f9ae13384489724

# V5 RAGAS-NLI template
huggingface-cli download HuggingFaceH4/zephyr-7b-beta \
  tokenizer.json tokenizer_config.json special_tokens_map.json 2>/dev/null || \
huggingface-cli download HuggingFaceH4/zephyr-7b-beta

echo "tokenizer prefetch ok $(date -Is)"
