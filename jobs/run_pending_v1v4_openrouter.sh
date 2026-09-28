#!/usr/bin/env bash
# Score new cpu_main rows (POL INV rephrase) via OpenRouter; appends to existing raw JSONL.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock pending_v1v4

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"

PENDING="${ROOT}/data/v3/instances_score_pending_cpu_early.jsonl"
python3 "${ROOT}/scripts/build_score_pending.py"
LOG="${ROOT}/jobs/logs/pending_v1v4_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "pending v1v4 start $(date -Is) n=$(wc -l <"${PENDING}")"

python3 src/score_jsonl.py --verifier v1_medscore \
  --instances "${PENDING}" \
  --out results/raw/v1_medscore.jsonl

export MEDVERIF_V4_OPENROUTER_MODEL="${MEDVERIF_V4_OPENROUTER_MODEL:-meta-llama/llama-3.3-70b-instruct}"
export MEDVERIF_V4_PROVIDER="${MEDVERIF_V4_PROVIDER:-DeepInfra}"
python3 src/score_jsonl.py --verifier v4_ragas_nli \
  --instances "${PENDING}" \
  --out results/raw/v4_ragas_nli.jsonl

python3 scripts/aggregate_api_cost.py
echo "pending v1v4 done $(date -Is)"
