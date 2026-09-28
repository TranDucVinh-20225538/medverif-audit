#!/usr/bin/env bash
# Expand scoring: V1b + V5 on T2 full-scope pending only (after V1/V4 on expand pending).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock expand_t2_v1b_v5

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-1.5}"
export MEDVERIF_V1B_OPENROUTER_MODEL="${MEDVERIF_V1B_OPENROUTER_MODEL:-openai/gpt-4o}"
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"
export MEDVERIF_V5_OPENROUTER_MODEL="${MEDVERIF_V5_OPENROUTER_MODEL:-anthropic/claude-sonnet-4.6}"
export MEDVERIF_V5_TOKENIZER_MODEL="${MEDVERIF_V5_TOKENIZER_MODEL:-HuggingFaceH4/zephyr-7b-beta}"
export MEDVERIF_V5_PROVIDER="${MEDVERIF_V5_PROVIDER:-Anthropic}"

INST="${ROOT}/data/t2/instances_full_pending.jsonl"
if [[ ! -s "${INST}" ]]; then
  python3 scripts/t2_build_instances.py --mode full || true
fi
RAW="${ROOT}/results/raw/t2_full"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/expand_v1b_v5_t2_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "expand v1b/v5 t2 start $(date -Is) n=$(wc -l <"${INST}")"

for v in v1b_medscore v5_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done
python3 scripts/aggregate_api_cost.py 2>/dev/null || true
echo "expand v1b/v5 t2 done $(date -Is)"
