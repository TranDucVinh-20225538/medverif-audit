#!/usr/bin/env bash
# Score only instance_ids missing from results/raw/v4_ragas_nli.jsonl (main set).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
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

LOG="${ROOT}/jobs/logs/v4_resume_missing_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "v4 resume missing start $(date -Is)"
python3 src/score_jsonl.py --verifier v4_ragas_nli \
  --instances data/v3/instances_cpu_main.jsonl \
  --out results/raw/v4_ragas_nli.jsonl
python3 scripts/aggregate_api_cost.py
echo "v4 resume missing done $(date -Is)"
