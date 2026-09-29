#!/usr/bin/env bash
# Resumable V1 full run (main + threshold) via OpenRouter.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock v1_openrouter_full

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_V1_PROVIDER=DeepInfra
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-4}"
export MEDVERIF_API_LEDGER=1
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
LOG="${ROOT}/jobs/logs/v1_openrouter_full_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "v1 full start $(date -Is)"
python3 src/score_jsonl.py --verifier v1_medscore \
  --instances data/v3/instances_cpu_main.jsonl \
  --out results/raw/v1_medscore.jsonl
python3 src/score_jsonl.py --verifier v1_medscore \
  --instances data/v3/instances_cpu_threshold.jsonl \
  --out results/raw_threshold/v1_medscore.jsonl
python3 scripts/aggregate_api_cost.py
echo "v1 full done $(date -Is); starting agreement 50x2"
python3 scripts/v1_agreement_50x2.py
python3 scripts/aggregate_api_cost.py
echo "all done $(date -Is)"
