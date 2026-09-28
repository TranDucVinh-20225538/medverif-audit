#!/usr/bin/env bash
# Full T2: v1b + v5 on instances_full_pending.jsonl (requires notes/t2_full_approved).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
APPROVE="${ROOT}/notes/t2_full_approved"
if [[ ! -f "${APPROVE}" ]]; then
  echo "missing ${APPROVE}" >&2
  exit 2
fi
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t2_full

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_V1B_OPENROUTER_MODEL="${MEDVERIF_V1B_OPENROUTER_MODEL:-openai/gpt-4o}"
export MEDVERIF_V5_OPENROUTER_MODEL="${MEDVERIF_V5_OPENROUTER_MODEL:-anthropic/claude-sonnet-4.6}"
export MEDVERIF_V5_TOKENIZER_MODEL="${MEDVERIF_V5_TOKENIZER_MODEL:-HuggingFaceH4/zephyr-7b-beta}"
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"
export MEDVERIF_V5_PROVIDER="${MEDVERIF_V5_PROVIDER:-Anthropic}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-2}"

LOG="${ROOT}/jobs/logs/t2_full_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t2 full start $(date -Is)"

python3 scripts/openrouter_budget.py || { echo "BUDGET STOP at start"; exit 2; }
python3 scripts/t2_build_instances.py --mode full

FULL="${ROOT}/data/t2/instances_full_pending.jsonl"
RAW="${ROOT}/results/raw/t2_full"
mkdir -p "${RAW}"

for v in v1b_medscore v5_ragas_nli; do
  echo "scoring ${v} ..."
  python3 scripts/openrouter_budget.py || exit 2
  if [[ -f "${ROOT}/notes/pause_t2_openrouter" ]]; then
    echo "paused (notes/pause_t2_openrouter); retry later"
    exit 3
  fi
  python3 src/score_jsonl.py --verifier "${v}" --instances "${FULL}" --out "${RAW}/${v}.jsonl"
done

python3 scripts/aggregate_api_cost.py 2>/dev/null || true
python3 scripts/openrouter_budget.py
python3 scripts/t2_full_report.py
echo "t2 full done $(date -Is)"
