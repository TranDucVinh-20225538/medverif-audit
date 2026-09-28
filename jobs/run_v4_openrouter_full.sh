#!/usr/bin/env bash
# V4 RAGAS-NLI full run via OpenRouter (Llama 3.3 70B default after Qwen3 probe fail).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock v4_openrouter_full

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"

export MEDVERIF_V4_OPENROUTER_MODEL="${MEDVERIF_V4_OPENROUTER_MODEL:-meta-llama/llama-3.3-70b-instruct}"
export MEDVERIF_V4_PROVIDER="${MEDVERIF_V4_PROVIDER:-DeepInfra}"
export MEDVERIF_V4_PROMPT_SUFFIX="${MEDVERIF_V4_PROMPT_SUFFIX:-}"

LOG="${ROOT}/jobs/logs/v4_openrouter_full_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "v4 full start $(date -Is) model=${MEDVERIF_V4_OPENROUTER_MODEL} provider=${MEDVERIF_V4_PROVIDER}"

python3 src/score_jsonl.py --verifier v4_ragas_nli \
  --instances data/v3/instances_cpu_main.jsonl \
  --out results/raw/v4_ragas_nli.jsonl
python3 src/score_jsonl.py --verifier v4_ragas_nli \
  --instances data/v3/instances_cpu_threshold.jsonl \
  --out results/raw_threshold/v4_ragas_nli.jsonl
python3 scripts/aggregate_api_cost.py
echo "v4 full done $(date -Is)"
