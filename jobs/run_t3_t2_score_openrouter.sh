#!/usr/bin/env bash
# Score T3 INV families with T2 verifiers when instances exist.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
INST="${ROOT}/data/v3/instances_inv_families.jsonl"
if [[ ! -s "${INST}" ]]; then
  INST="${ROOT}/data/t3/instances_inv_families.jsonl"
fi
if [[ ! -s "${INST}" ]]; then
  echo "T3 INV families not ready (empty ${INST})"
  exit 0
fi
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t3_t2_score

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_V1B_OPENROUTER_MODEL="${MEDVERIF_V1B_OPENROUTER_MODEL:-openai/gpt-4o}"
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"
export MEDVERIF_V5_OPENROUTER_MODEL="${MEDVERIF_V5_OPENROUTER_MODEL:-anthropic/claude-sonnet-4.6}"
export MEDVERIF_V5_TOKENIZER_MODEL="${MEDVERIF_V5_TOKENIZER_MODEL:-HuggingFaceH4/zephyr-7b-beta}"
export MEDVERIF_V5_PROVIDER="${MEDVERIF_V5_PROVIDER:-Anthropic}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-2}"

RAW="${ROOT}/results/raw/t3_t2"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t3_t2_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t3 t2 score start $(date -Is) n=$(wc -l < "${INST}")"

for v in v1b_medscore v5_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done
echo "t3 t2 score done $(date -Is)"
