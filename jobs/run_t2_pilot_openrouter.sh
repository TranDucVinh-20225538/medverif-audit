#!/usr/bin/env bash
# T2 pilot: v1b + v5 on 100 stratified DOSE instances. Full T2 waits for notes/t2_full_approved.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t2_pilot

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

LOG="${ROOT}/jobs/logs/t2_pilot_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t2 pilot start $(date -Is)"

python3 scripts/openrouter_budget.py || { echo "BUDGET STOP at start"; exit 2; }

python3 scripts/t2_build_instances.py --mode pilot
python3 scripts/t2_build_instances.py --mode full

PILOT="${ROOT}/data/t2/instances_pilot_100.jsonl"
RAW="${ROOT}/results/raw/t2_pilot"
mkdir -p "${RAW}"

for v in v1b_medscore v5_ragas_nli; do
  echo "scoring ${v} ..."
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${PILOT}" --out "${RAW}/${v}.jsonl"
done

python3 scripts/aggregate_api_cost.py 2>/dev/null || true
python3 scripts/openrouter_budget.py
python3 scripts/t2_pilot_report.py
echo "t2 pilot done $(date -Is)"
