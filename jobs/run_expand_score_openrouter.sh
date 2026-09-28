#!/usr/bin/env bash
# HPC OpenRouter: V1 + V4 on expand pending (append to results/raw/).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock expand_or_score

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-2}"

python3 scripts/build_score_pending.py
PENDING="${ROOT}/data/expand/instances_score_pending.jsonl"
if [[ ! -s "${PENDING}" ]]; then
  echo "expand score pending empty"
  exit 0
fi

LOG="${ROOT}/jobs/logs/expand_or_score_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "expand OR score start $(date -Is) n=$(wc -l <"${PENDING}")"

python3 scripts/openrouter_budget.py || exit 2

python3 src/score_jsonl.py --verifier v1_medscore \
  --instances "${PENDING}" \
  --out results/raw/v1_medscore.jsonl

export MEDVERIF_V4_OPENROUTER_MODEL="${MEDVERIF_V4_OPENROUTER_MODEL:-meta-llama/llama-3.3-70b-instruct}"
export MEDVERIF_V4_PROVIDER="${MEDVERIF_V4_PROVIDER:-DeepInfra}"
python3 src/score_jsonl.py --verifier v4_ragas_nli \
  --instances "${PENDING}" \
  --out results/raw/v4_ragas_nli.jsonl

python3 scripts/aggregate_api_cost.py 2>/dev/null || true
python3 scripts/build_score_pending.py
echo "expand OR score done $(date -Is)"
